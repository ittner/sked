# -*- coding: utf-8 -*-

# Sked - a wikish scheduler with Python and PyGTK
# (c) 2006-10 Alexandre Erwin Ittner <alexandre@ittner.com.br>
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston,
# MA 02111-1307, USA.
#

"""
Methods for locking file *paths* (not files, which are handled by the native
lock system from Berkeley DB). Some procedures defined here are a bit tricky.
"""

import os
try:    # For Posix file locking
    import fcntl
except:
    fcntl = None


class BaseLockSystem(object):
    """ Base class for the file locking systems. """

    @property
    def lock_path(self):
        return self._lock_path

    def lock_file_exists(self):
        """ When used with 'PosixLockSystem', this method says that is a
        good idea to run a database verification (see bellow). When used
        with 'DumbLockSystem' we have no other information except the return
        of this method, so, it is an order to stop.
        """
        return os.path.exists(self._lock_path)

    def _set_paths(self, path):
        self._lock_path = path + ".lock"
        self._lock_fd = None

    def get_lock(self):
        """ Get the lock and returns True (or do not get and return False).
        Must be implemented by derived classes.
        """
        raise NotImplementedError()

    def release_lock(self):
        """ Release the lock. Must be implemented by derived classes. """
        raise NotImplementedError()


class DumbLockSystem(BaseLockSystem):
    """ A very primitive and buggy, but portable, locking system. """

    def __init__(self, path):
        self._set_paths(path)

    def get_lock(self):
        try:
            if self.lock_file_exists() or self._lock_fd != None:
                return False
            self._lock_fd = open(self._lock_path, "a")
        except IOError: return False
        return True

    def release_lock(self):
        if self._lock_fd:
            self._lock_fd.close()
            self._lock_fd = None
        try:
            os.remove(self._lock_path)
        except: pass


class PosixLockSystem(BaseLockSystem):
    """ A better lock system for Linux and other Unices.
    The idea: create a file which name is based in the path we want to lock
    and get a posixly correct file lock for it. The nice thing is that the
    posix lock is lost when the file is closed (even if crash-closed) but
    the file remains. Consequences: 
      - If there is a file and we can not get a lock for it, Sked stills
        running. Stop now.
      - If there is a file and we got a lock for it, Sked was not closed
        properly and it is a good idea to run db.verify before start working.
        If everything is ok, we can proceed without bothering the user with
        stray lockfile messages.
    Problems: It does not play well with 'DumbLockSystem' and it is a very 
    bad idea to run it over any network share, except NFS (which locks well).
    """

    def __init__(self, path):
        self._set_paths(path)

    def get_lock(self):
        try:
            self._lock_fd = os.open(self._lock_path,
                os.O_CREAT | os.O_WRONLY, 0644)
            fcntl.lockf(self._lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except: return False
        return True

    def release_lock(self):
        try:
            os.close(self._lock_fd)
        except: pass
        try:
            os.remove(self._lock_path)
        except: pass
        self._lock_fd = None


def any_lock_system(path):
    """ Return a instance of the best locking system available. """
    if fcntl != None and os.name == "posix":
        return PosixLockSystem(path)
    else:
        return DumbLockSystem(path)
