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

import os
import zlib
import struct
import shutil

import utils

from Crypto.Cipher import AES
import md5 as MD5
from Crypto.Util.randpool import RandomPool
from Crypto.Hash import SHA256


class AccessDeniedError(Exception):
    pass

class CorruptedDatabaseError(Exception):
    pass

class NotReadyError(Exception):
    pass


class FileSystemDatabase(object):
    """Bare-bones, slow, portable, DBM-like, filesystem database.
    Keys are stored as files. No name validation is done here. This class
    is only intended to serve higher level classes.
    """

    VERSION = "1"
    SUFFIX = ".entry"
    TMPSUFFIX = ".tmp"
    VERFILE = "version"
    
    def __init__(self, path):
        self.path = os.path.normpath(path)
        verfile = os.path.join(self.path, FileSystemDatabase.VERFILE)
        if os.path.exists(self.path):
            if not os.path.exists(verfile):
                raise CorruptedDatabaseError
            # Add version checking.
        else:
            try:
                os.makedirs(self.path)
                fp = open(verfile, "w")
                fp.write(FileSystemDatabase.VERSION)
                fp.close()
            except OSError:
                raise AccessDeniedError
        if not os.access(self.path, os.R_OK | os.W_OK | os.X_OK):
            raise AccessDeniedError

    def keys(self):
        slen = len(FileSystemDatabase.SUFFIX)
        for entry in os.listdir(self.path):
            if entry.endswith(FileSystemDatabase.SUFFIX):
                yield unicode(entry[:-slen])

    def has_key(self, key):
        path = os.path.join(self.path, key + FileSystemDatabase.SUFFIX)
        return os.access(path, os.F_OK)
    
    def get_key(self, key, default = None):
        path = os.path.join(self.path, key + FileSystemDatabase.SUFFIX)
        try:
            fp = open(path, "rb")
        except IOError:
            return default
        data = fp.read()
        fp.close()
        return data
    
    def set_key(self, key, value):
        path = os.path.join(self.path, key + FileSystemDatabase.SUFFIX)
        tpath = os.path.join(self.path, key + FileSystemDatabase.TMPSUFFIX)
        try:
            fp = open(tpath, "wb")
        except IOError:
            raise AccessDeniedError
        fp.write(value)
        fp.close()
        try:
            # Tries to rename the file atomically.
            utils.rename_file(tpath, path)
        except IOError:
            raise AccessDeniedError

    def del_key(self, key):
        path = os.path.join(self.path, key + FileSystemDatabase.SUFFIX)
        try:
            if os.access(path, os.F_OK):
                os.remove(path)
        except OSError:
            raise AccessDeniedError
    
    def get_path(self):
        return self.path


class EncryptedDatabase(object):
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
        db.set_key(index, encrypted)

        Note: Lengths are 32 bit little-endian unsigned ints.
    
    Usage:
        db = EncryptedDatabase("path/to/db")
        if db.is_new():
            db.set_password(ask_pwd())
        else:
            pwd = ""
            while not db.try_password(pwd):
                pwd = ask_pwd()
        # ready to use.
    """

    VERSION = "AES-128-CBC-MD5-GZIP-1"

    def __init__(self, path):
        self._ready = False
        self._rnd = RandomPool(hash=SHA256)
        self._db = FileSystemDatabase(path)

    def is_new(self):
        return not self._db.has_key("_version")
        
    def is_ready(self):
        return self._ready

    def try_password(self, pwd):
        if self.is_new():
            raise NotReadyError
        key = self._hash(pwd.encode("utf-8"))
        encmass = self._db.get_key("_mass", 16 * "0")
        masshash = self._db.get_key("_hash", 16 * "0")
        mass = self._decrypt(encmass, masshash, key)
        if masshash == self._hash(mass):
            self._mass = mass
            self._key = key
            saltvec = self._hash(masshash)
            self._dbsalt = self._decrypt(self._db.get_key("_salt"), saltvec)
            self._ready = True
            return True
        return False

    def set_password(self, pwd):
        if self.is_new():
            self._key = self._hash(pwd.encode("utf-8"))
            self._dbsalt = self._rand_str(16)
            self._mass = self._rand_str(128)
            masshash = self._hash(self._mass)
            saltvec = self._hash(masshash)
            self._db.set_key("_version", EncryptedDatabase.VERSION)
            self._db.set_key("_salt", self._encrypt(self._dbsalt, saltvec))
            self._db.set_key("_mass", self._encrypt(self._mass, masshash))
            self._db.set_key("_hash", masshash)
            self._ready = True
        else:
            # Too may dependencies on self._db ...
            if not self._ready:
                raise NotReadyError
            curdir = self._db.get_path()
            tmpdir = self._tmpnam(curdir + ".new.")
            tmpdb = EncryptedDatabase(tmpdir)
            tmpdb.set_password(pwd)
            if not tmpdb.is_ready():
                raise AccessDeniedError
            for k, v in self.pairs():
                tmpdb.set_key(k, v)
            oldtmp = self._tmpnam(curdir + ".old.")
            os.rename(curdir, oldtmp)
            os.rename(tmpdir, curdir)
            self._key = tmpdb._key
            self._dbsalt = tmpdb._dbsalt
            self._mass = tmpdb._mass
            self._hash = tmpdb._hash
            shutil.rmtree(oldtmp)

    def check_password(self, pwd):
        return self._hash(pwd.encode("utf-8")) == self._key

    def has_key(self, key):
        if not self._ready:
            raise NotReadyError
        rkey = self._make_db_key(key)
        return self._db.has_key(rkey)
    
    def set_key(self, key, value):
        if not self._ready:
            raise NotReadyError
        rkey = self._make_db_key(key)
        keyvalue = self._packstr(key.encode("utf-8")) + \
            self._packstr(value.encode("utf-8"))
        compressed = self._packstr(self._compress(keyvalue))
        plain = compressed + self._rand_str(16 - len(compressed) % 16)
        hash = self._hash(plain)
        encrypted = hash + self._encrypt(plain, hash)
        self._db.set_key(rkey, encrypted)

    def get_key(self, key, default = None):
        ret = self.get_pair(key, None)
        if ret == None:
            return default
        return ret[1]

    def get_pair(self, key, default = None):
        if not self._ready:
            raise NotReadyError
        ret = self._get_pair(self._make_db_key(key))
        if ret == None:
            return default
        return ret
        
    def del_key(self, key):
        rkey = self._make_db_key(key)
        if self._db.has_key(rkey):
            self._db.del_key(rkey)

    def pairs(self):
        if not self._ready:
            raise NotReadyError
        for rkey in self._db.keys():
            if not rkey.startswith("_"):
                pair = self._get_pair(rkey)
                yield pair[0], pair[1]

    def _get_pair(self, rkey):
        if not self._db.has_key(rkey):
            return None
        encrypted = self._db.get_key(rkey)
        hash = encrypted[0:16]
        plain = self._decrypt(encrypted[16:], hash)
        if self._hash(plain) != hash:
            raise CorruptedDatabaseError  # or wrong password...
        compressed = self._unpackstr(plain)
        keyvalue = self._decompress(compressed)
        keyname = self._unpackstr(keyvalue)
        value = self._unpackstr(keyvalue[4 + len(keyname):])
        return [unicode(keyname, "utf-8"), unicode(value, "utf-8")]

    def _make_db_key(self, key):
        return self._hexhash(key.upper().encode("utf-8") + self._dbsalt)

    def _hexhash(self, data):
        hs = MD5.new()
        hs.update(data)
        return hs.hexdigest()

    def _hash(self, data):
        hs = MD5.new()
        hs.update(data)
        return hs.digest()

    def _compress(self, data):
        return zlib.compress(data)
        
    def _decompress(self, data):
        return zlib.decompress(data)
        
    def _encrypt(self, data, vec, key = None):
        if key == None:
            key = self._key
        enc = AES.new(key, AES.MODE_CBC, vec)
        return enc.encrypt(data)
        
    def _decrypt(self, data, vec, key = None):
        if key == None:
            key = self._key
        enc = AES.new(key, AES.MODE_CBC, vec)
        return enc.decrypt(data)

    def _packstr(self, data):
        # <32 bit little endian unsigned int><data>
        return struct.pack("<I", len(data)) + data

    def _unpackstr(self, data):
        # <32 bit little endian unsigned int><data>
        [len] = struct.unpack("<I", data[0:4])
        return data[4:len+4]

    def _rand_str(self, bytes = 16):
        return self._rnd.get_bytes(bytes)

    def _tmpnam(self, prefix = ""):
        # Avoids os.tempnam(). WARNING! There is a race condition here!
        name = prefix + self._hexhash(self._rand_str())
        while os.access(name, os.F_OK):   # path exists? Try again.
            name = prefix + self._hexhash(self._rand_str())
        return name
