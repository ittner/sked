# -*- coding: utf-8 -*-

# Sked - a wikish scheduler with Python and PyGTK
# (c) 2006-09 Alexandre Erwin Ittner <alexandre@ittner.com.br>
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

__CVSID__ = "$Id$"

from bsddb import db
import os
import zlib
import cPickle
import hashlib

import utils


class AccessDeniedError(Exception):
    pass

class CorruptedDatabaseError(Exception):
    pass

class NotReadyError(Exception):
    pass


def _hash_sha256_str(sa, sb = ""):
    md = hashlib.sha256()
    md.update(sa)
    md.update(sb)
    return md.hexdigest()

def _normalize_pwd(pwd):
    return pwd.encode("utf-8")

def make_key(pwd):
    # Key strengthing to slow down dictionary based attacks.
    npwd = _normalize_pwd(pwd)
    enckey = _hash_sha256_str(npwd)
    for i in range(1, 42):
        enckey = _hash_sha256_str(npwd, enckey)
    return enckey


class EncryptedDatabase(object):
    """Implements a Sked secure database over a Berkeley DB4.x encrypted 
    database. Key and data MUST be valid Unicode strings. The database
    format is:
    
    dbkey  = key.upper().encode("utf-8")
    dbdata = pickle.dumps([ key, zlib.compress(data.encode("utf-8")) ], 2)
    
    """

    def __init__(self, path = None):
        self._db = None
        if path:
            self._path = path
        else:
            self._path = os.path.join(utils.get_home_dir(), ".sked.db")
        self.lock_path = self._path + ".lock"
        self._ready = False
        self._lock_fd = None

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
        if os.path.exists(self.lock_path) or self._lock_fd != None:
            return False
        self._lock_fd = open(self.lock_path, "a")
        return True

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
        return self._db.has_key(self._make_db_key(key)) == 1
    
    def set_key(self, key, value):
        if not self._ready:
            raise NotReadyError
        cval = zlib.compress(value.encode("utf-8"))
        self._db.put(self._make_db_key(key), cPickle.dumps([key, cval], 2))

    def get_key(self, key, default = None):
        ret = self.get_pair(key, None)
        if ret == None:
            return default
        return ret[1]

    def get_pair(self, key, default = None):
        if not self._ready:
            raise NotReadyError
        try:
            spair = self._db.get(self._make_db_key(key))
            if spair != None:
                pair = cPickle.loads(spair)
                pair[1] = zlib.decompress(pair[1]).decode("utf-8")
                return pair
        except db.DBNotFoundError:
            pass
        return default

    def del_key(self, key):
        rkey = self._make_db_key(key)
        if self._db.has_key(rkey) == 1:
            self._db.delete(rkey)

    def pairs(self):
        if not self._ready:
            raise NotReadyError
        cursor = self._db.cursor()
        rec = cursor.first()
        while rec:
            pair = cPickle.loads(rec[1])
            yield pair[0], zlib.decompress(pair[1]).decode("utf-8")
            rec = cursor.next()

    def _make_db_key(self, key):
        return key.upper().encode("utf-8")

    def _make_pwd_hash(self, pwd):
        return _hash_sha256_str(_normalize_pwd(pwd))
        
    def _set_pwd_hash(self, pwd):
        # We need this to change the password later. For security, we
        # won't keep it in plain text in the memory (or, at least, not
        # in 'our' side of the Python VM)
        self._pwd_hash = self._make_pwd_hash(pwd)

