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
History manager.
"""

from pages import Page

class HistoryManager(object):
    """
    Class for handling history items. Used for the main history, last page
    inserted, etc.
    """

    def __init__(self, db=None, name=None, max_items=None, unique=False):
        self._db = db
        self.name = name
        self.max_items = max_items
        self._unique = unique
        self._model = None
        self._items = []
        self.load()

    def load(self):
        """ (Re)load items from the database. """
        if self.name != None and self._db != None:
            self.set_items(self._db.get_key(self.name, []))
        
    def save(self):
        self._trim()
        if self.name:
            self._db.set_key(self.name, self._items)

    def get_items(self):
        return self._items
        
    def get_first(self):
        if len(self._items) > 0:
            return self._items[0]
        return None
    
    def add(self, item):
        if self._unique:
            uitem = item.upper()
            for tmp in self._items:
                if tmp.upper() == uitem:
                    self._items.remove(tmp)
                    break
        self._items.insert(0, item)
        self._trim()
        self._refresh_model()

    def set_model(self, model):
        """If a ListStore model is given, the HistoryHandler will synchronize
        it automatically. This model MUST be a ListStore with only one string.
            Ex. gtk.ListStore(gobject.TYPE_STRING)
        """
        self._model = model
        self._refresh_model()
        
    def _refresh_model(self):
        if self._model != None:
            self._model.clear()
            for item in self._items:
                self._model.append([item])

    def _trim(self):
        if self.max_items:
            self._items = self._items[:self.max_items]

    def set_items(self, items):
        self._items = items
        self._trim()
        self._refresh_model()

    def get_item(self, index):
        if abs(index) < len(self._items):
            return self._items[index]
        return None


class BackForwardManager(object):
    
    def __init__(self, max_items):
        self.max_items = max_items
        self._hst = [ ]
        self._pos = -1

    def go(self, pagename):
        if len(self._hst) == 0:
            self._hst.append(pagename)
            self._pos = 0
            return
        self._hst = self._hst[0:self._pos+1]
        if Page.normalize_name(self._hst[-1]) != Page.normalize_name(pagename):
            self._hst.append(pagename)
            if len(self._hst) > self.max_items:
                self._hst = self._hst[-self.max_items:]
            self._pos = len(self._hst) - 1

    def back(self):
        if self.can_back():
            self._pos -= 1
            return self._hst[self._pos]
        return None

    def forward(self):
        if self.can_forward():
            self._pos += 1
            return self._hst[self._pos]
        return None

    def can_back(self):
        return self._pos > 0
        
    def can_forward(self):
        return self._pos < len(self._hst) - 1
