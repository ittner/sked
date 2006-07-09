# -*- coding: utf-8 -*-

# Sked - a wikish scheduler with Python and PyGTK
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
History manager.
"""

__CVSID__ = "$Id$"

class HistoryManager:
    """
    Class for handling history items. Used for the main history, back, forward,
    last page inserted, etc.
    """

    def __init__(self, skapp, dbkey = None, unique = False):
        self._maxitems = skapp.opt.get_int("max_history")
        self._unique = unique
        self._dbkey = dbkey
        self._db = None
        self._items = []
        if self._dbkey != None:
            self._db = skapp.db
            str = self._db.get_key(self._dbkey, None)
            if str != None:
                try:
                    self._items = str.split(u"\n")
                except:
                    pass

    def save(self):
        self._trim()
        if self._dbkey:
            self._db.set_key(self._dbkey, u"\n".join(self._items))

    def get_items(self):
        return self._items
        
    def get_first(self):
        if len(self._items) > 0:
            return self._items[0]
        return None
    
    def pop(self):
        return self._items.pop(0)

    def add(self, item):
        if self._unique:
            uitem = item.upper()
            for tmp in self._items:
                if tmp.upper() == uitem:
                    self._items.remove(tmp)
                    break
        self._items.insert(0, item)
        self._trim()

    def sort(self):
        sort(self._items)

    def _trim(self):
        self._items = self._items[:self._maxitems]