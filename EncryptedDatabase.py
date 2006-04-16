# -*- coding: utf-8 -*-
#
# Sked - a wikish scheduler with Python, PyGTK and Berkeley DB
# (c) 2006 Alexandre Erwin Ittner <aittner@netuno.com.br>
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
Secure database for Sked entries.
$Id$
"""

import zlib
from Crypto.Cipher import AES
from Crypto.Hash import MD5     # Alias for md5.md5
from Crypto.Util.randpool import RandomPool

class CorruptedDatabaseError(Exception):
    pass

class NotReadyError(Exception):
    pass


class DatabaseManager:
    """ Standard secure database manager for Sked.
    Features:
        - Database keys and values must be Unicode;
        - Database key searches are case insensitive;
        - AES 128 bit CBC encryption;
        - Encryption key is hashed from the password;
        - MD5 key hashing;
        - zlib compression.
        
    database data format:
        key = md5(password)
        compressed = gzip(len(name) + name + len(text) + text)
        plain = len(compressed) + compressed + padding_string
        encrypted = hash(plain) + encrypt(plain, key)
        index = md5(name + dbsalt)
        db[index] = cipher_data

        Note: Lengths are 32 bit little-endian unsigned ints.
    
    Usage:
        db = DatabaseManager("fname")
        if db.is_new():
            db.set_password(ask_pwd())
        else:
            pwd = ""
            while not db.try_password(pwd):
                pwd = ask_pwd()
        # ready to use.
    """

    def __init__(self, fname):
        self._ready = False
        self._db = anydbm.open(fname, 'c')

    def is_new(self):
        return not self._db.has_key("version")
        
    def is_ready(self):
        return self._ready

    def try_password(self, pwd):
        if self.is_new():
            raise NotReadyError
        key = self._hash(pwd)
        encmass = self._db["mass"]
        masshash = self._db["hash"]
        mass = self._decrypt(encmass, key)
        if masshash == self._hash(mass):
            self._mass = mass
            self._key = key
            self._dbsalt = self._decrypt(self._db["salt"])
            self._ready = True
            return True
        return False

    def set_password(self, pwd):
        if self.is_new():
            self._key = self._hash(pwd)
            self._dbsalt = self._rand_str(16)
            self._mass = self._rand_str(128)
            self._db["version"] = "1"
            self._db["salt"] = self._encrypt(self._dbsalt)
            self._db["mass"] = self._encrypt(self._mass)
            self._db["hash"] = self._hash(self._mass)
            self._ready = True
            self._db.sync()
        else:
            if not self._ready:
                raise NotReadyError
            # change password...
    
    def has_key(self, key):
        if not self._ready:
            raise NotReadyError
        rkey = self._make_db_key(key)
        return self._db.has_key(rkey)
    
    def set_key(self, key, value):
        if not self._ready:
            raise NotReadyError
        rkey = self._make_db_key(key)
        keyvalue = self._packstr(key) + self._packstr(value)
        compressed = self._packstr(self._compress(keyvalue))
        plain = compressed + self._randstr(len(compressed) % 16)
        encrypted = self._hash(plain) + self._encrypt(plain)
        self._db[rkey] = encrypted

    def get_key(self, key, default = None):
        if not self._ready:
            raise NotReadyError
        ret = self._get_pair(self._make_db_key(key))
        if ret == None:
            return default
        return ret[1]
        
    def iterate(self):
        if not self._ready:
            raise NotReadyError
        for rkey in self._db:
            if rkey.startswith("_"):
                pair = self._get_pair(rkey)
                yield pair[0], pair[1]

    def _get_pair(self, rkey):
        if not self._db.has_key(rkey):
            return None
        encrypted = self._db[rkey]
        hash = encrypted[0:16]
        plain = self._decrypt(encrypted[16:])
        if self._hash(plain) != hash:
            raise CorruptedDatabaseError  # or wrong password...
        compressed = self._unpackstr(plain)
        keyvalue = self._decompress(compressed)
        keyname = self._unpackstr(keyvalue)
        value = self._unpackstr(keyvalue[4 + len(keyvalue):])
        return [keyname, value]

    def _make_db_key(self, key):
        return "_" + self._hash(key.upper().encode("utf-8") + self._dbsalt)
    
    def _hash(self, data):
        hs = MD5.new()
        hs.update(data)
        return hs.digest()

    def _compress(self, data):
        return zlib.compress(data)
        
    def _decompress(self, data):
        return zlib.decompress(data)
        
    def _encrypt(self, data, key = None):
        if key == None:
            key = self._key
        pass
        
    def _decrypt(self, data, key = None):
        if key == None:
            key = self._key
        pass

    def _packstr(self, data):
        # <32 bit little endian unsigned int><data>
        return struct.pack("<I", len(data)) + data

    def _unpackstr(self, data):
        # <32 bit little endian unsigned int><data>
        [len] = struct.unpack("<I", data[0:4])
        return data[4:len+4]

    def _randstr(self, bytes = 16):
        pass

