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


class EncryptedDatabase(object):
    
    def __init__(self, path):
        self._db = None
        self._path = os.path.normpath(path)
        self._ready = False

    def is_new(self):
        return not os.path.exists(self._path)
        
    def is_ready(self):
        return self._ready

    def try_open(self, pwd):
        try:
            self._db = db.DB()
            enckey = self._make_key(pwd)
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
        enckey = self._make_key(pwd)
        self._db.set_encrypt(enckey, db.DB_ENCRYPT_AES)
        self._db.open(self._path, None, db.DB_HASH, db.DB_CREATE)
        self._set_pwd_hash(pwd)
        self._ready = True

    def change_pwd(self, oldpwd, newpwd):
        # To do
        return False    # Failed.

    def close(self):
        self._db.close()
        self._db = None
        self._ready = False
        
    def has_key(self, key):
        if not self._ready:
            raise NotReadyError
        return self._db.has_key(self._make_db_key(key)) == 1
    
    def set_key(self, key, value):
        if not self._ready:
            raise NotReadyError
        self._db.put(self._make_db_key(key), cPickle.dumps([key, value], 2))

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
                return cPickle.loads(spair)
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
            pair = cPickle.loads(self._db.get(rec[0]))
            yield pair[0], pair[1]
            rec = cursor.next()

    def _make_db_key(self, key):
        return key.upper().encode("utf-8")

    def _normalize_pwd(self, pwd):
        return pwd.encode("utf-8")
        
    def _set_pwd_hash(self, pwd):
        # We need this to change the password later. For security, we
        # won't keep it in plain text in the memory (or, at least, not
        # in 'our' side of the Python VM)
        self._pwd_hash = _hash_sha256_str(self._normalize_pwd(pwd))        

    def _make_key(self, pwd):
        # Key strengthing to slow down dictionary based attacks.
        npwd = self._normalize_pwd(pwd)
        enckey = _hash_sha256_str(npwd)
        for i in range(1, 42):
            enckey = _hash_sha256_str(npwd, enckey)
        return enckey
