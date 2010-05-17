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

"""
Options and configuration management module.
"""

from gtk import gdk

class OptionManager:
    """
    Class for handling appliation's options.
    """

    def __init__(self, db, defaults = {}):
        self._db = db
        self._opts = {}
        self.set_defaults(defaults)
        self.load()

    def set_defaults(self, defaults):
        self._defs = {}
        for k in defaults:
            self._defs[k] = defaults[k]
            
    def save(self):
        self._db.set_key("options", self._opts)
    
    def load(self):
        s = self._db.get_key("options")
        if s:
            self._opts = s

    def get_str(self, key):
        if self._opts.has_key(key):
            return self._opts[key]
        elif self._defs.has_key(key):
            return self._defs[key]
        else:
            return None
    
    def set_str(self, key, value):
        self._opts[key] = value

    def get_int(self, key):
        s = self.get_str(key)
        if s != None:
            return int(s)
        return None

    def set_int(self, key, value):
        self.set_str(key, "%d" % value)

    def get_bool(self, key):
        v = self.get_int(key)
        if v != None:
            if v != 0:
                return True
            else:
                return False
        else:
            return None

    def set_bool(self, key, value):
        if value == True:
            self.set_int(key, 1)
        else:
            self.set_int(key, 0)
            
    def get_color(self, key):
        try:
            c = gdk.color_parse(self.get_str(key))
        except ValueError:
            if self._defs.has_key(key):
                c = gdk.color_parse(self._defs[key])    # for invalid colors.
        return c

    def set_color(self, key, color):
        self.set_str(key, "#%.2X%.2X%.2X" %
            (color.red/256, color.green/256, color.blue/256))


