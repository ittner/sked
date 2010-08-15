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
Databases used by Sked.
"""


from bsddb import db
import os
import zlib
import cPickle as pickle
import hashlib

import utils


class AccessDeniedError(Exception):
    pass

class CorruptedDatabaseError(Exception):
    pass

class NotReadyError(Exception):
    pass


def _hash_sha256_str(*args):
    md = hashlib.sha256()
    for s in args:
        md.update(s)
    return md.hexdigest()

def _normalize_pwd(pwd):
    return pwd.encode("utf-8")

def make_key(pwd):
    """
    Oracle Berkeley DB uses a very simple string-to-key function: the first
    128 bits of the SHA1 hash of the concatenation of the password, a hard
    coded magic number, and the password again. This happens in version 5.0
    and should not change in a near future. It is possible to improve the
    security by using a proper S2K algorithm before passing the password to
    the database.

    To use a secure, salted, S2K algorithm like PBKDF2, we need to store the
    salt somewhere outside the database, adding a undesired complexity layer
    to the application. So we resort to a less secure, non-salted, algorithm.
    It is better than nothing...

    Our algorithm hashes the concatenation of the ASCII representation of an
    integer 'i' (without leading zeros) and the password (encoded in UTF-8),
    repeating the process 4242 times, with 'i' ranging from 0 to 4241 (closed
    interval).We use the SHA-256 hash function to get a 256 bits long key
    encoded as a lowercase hex string with any leading zeros. This new
    password is also a valid ASCII string, so it may be passed to the standard
    DB4 utilities, if needed for some maintenance work (an utility to get the
    password is provided in the file printkey.py).
    """

    npwd = _normalize_pwd(pwd)
    md = hashlib.sha256()
    for i in range(0, 4242):
        md.update(str(i))
        md.update(npwd)
    return md.hexdigest().lower().encode("utf-8")


class EncryptedDatabase(object):
    """Implements a Sked secure database over a Berkeley DB4.x encrypted 
    database. Key MUST be a valid Unicode string, data may be any python
    object.
    """

    def __init__(self, path):
        self._db = None
        self._path = os.path.realpath(path)
        ddir = os.path.split(self._path)[0]
        if not os.path.exists(ddir):
            os.makedirs(ddir, 0700)
        self.lock_path = self._path + ".lock"
        self._ready = False
        self._lock_fd = None

    @property
    def path(self):
        """Returns the database path."""
        return self._path

    def is_new(self):
        return not os.path.exists(self._path)
        
    def is_ready(self):
        return self._ready

    def try_open(self, pwd):
        try:
            self._db = db.DB()
            enckey = make_key(pwd)
            self._db.set_encrypt(enckey, db.DB_ENCRYPT_AES)
            self._db.open(self._path, None, db.DB_HASH, db.DB_DIRTY_READ)
            self._set_pwd_hash(pwd)
            self._ready = True
            return True
        except:
            pass
        return False
    
    def create(self, pwd):
        self._db = db.DB()
        enckey = make_key(pwd)
        self._db.set_encrypt(enckey, db.DB_ENCRYPT_AES)
        self._db.open(self._path, None, db.DB_HASH, db.DB_CREATE)
        self._set_pwd_hash(pwd)
        self._ready = True

    def change_pwd(self, newpwd):
        # Creates a new database and re-encrypts everything
        i = 0
        newpath = self._path  + ".tmp"  # FIXME: Bad, very bad race condition
        while os.path.exists(newpath):
            newpath = self._path  + ".tmp" + str(i)
            i = i + 1

        newdb = EncryptedDatabase(newpath)
        newdb.create(newpwd)
        
        cursor = self._db.cursor()
        rec = cursor.first()
        while rec:
            newdb._db.put(rec[0], rec[1])
            rec = cursor.next()
        
        newdb.close()
        self._db.close()

        # DB4 provides its own rename. Why?  May it save us from the lack 
        # of atomicity on Windows' os.rename()?
        utils.rename_file(newpath, self._path)
        return self.try_open(newpwd)


    def close(self):
        self._db.close()
        self._db = None
        self.release_lock()
        self._ready = False

    def get_lock(self):
        """Try to get exclusive access to the database."""
        # A very primitive (and buggy) locking system. We can't use the DB4
        # native locking bacause we need it before create the database.
        try:
            if os.path.exists(self.lock_path) or self._lock_fd != None:
                return False
            self._lock_fd = open(self.lock_path, "a")
            return True
        except IOError, ex:
            return False

    def release_lock(self):
        """Releases exclusive access to database."""
        if self._lock_fd:
            self._lock_fd.close()
            self._lock_fd = None
        try:
            os.remove(self.lock_path)
        except:
            pass

    def check_password(self, pwd):
        return self._pwd_hash == self._make_pwd_hash(pwd)
        
    def has_key(self, key):
        if not self._ready:
            raise NotReadyError
        return self._db.has_key(key) == 1
    
    def set_key(self, key, value, sync = True):
        if not self._ready:
            raise NotReadyError
        self._db.put(key, zlib.compress(pickle.dumps(value, 2)))
        if sync:
            self._db.sync()

    def get_key(self, key, default = None):
        if not self._ready:
            raise NotReadyError
        try:
            val = self._db.get(key)
            if val != None:
                return pickle.loads(zlib.decompress(val))
        except db.DBNotFoundError:
            pass
        return default

    def del_key(self, key):
        if self._db.has_key(key) == 1:
            self._db.delete(key)

    def pairs(self):
        if not self._ready:
            raise NotReadyError
        cursor = self._db.cursor()
        rec = cursor.first()
        while rec:
            data = pickle.loads(zlib.decompress(rec[1]))
            yield rec[0], data
            rec = cursor.next()

    def keys(self):
        if not self._ready:
            raise NotReadyError
        cursor = self._db.cursor()
        rec = cursor.first()
        while rec:
            yield rec[0]
            rec = cursor.next()

    def _make_pwd_hash(self, pwd):
        return _hash_sha256_str(_normalize_pwd(pwd))
        
    def _set_pwd_hash(self, pwd):
        # We need this to change the password later. For security, we
        # won't keep it in plain text in the memory (or, at least, not
        # in 'our' side of the Python VM)
        self._pwd_hash = self._make_pwd_hash(pwd)

