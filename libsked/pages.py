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
Page management module.
"""

class PageManager(object):
    _ENCODING = "utf-8"
    _PREFIX = "page:"

    def __init__(self, db):
        """ Creates a new page manager using the given database. """
        self.db = db

    def exists(self, pagename):
        """ Returns True if the database have a page with the given name. """
        return self.db.has_key(self._db_key(pagename))

    def load(self, pagename):
        """ Loads the given page from the database. Returns the page object
        or None if the page do not exists. """
        rec = self.db.get_key(self._db_key(pagename), None)
        if not rec:
            return None
        return self._decode_page(rec)

    def save(self, page, sync = True):
        """ Saves the page to the database. Name is always taken from
        the 'name' property. If 'sync' is False, the database will not
        be flushed/sinc()ed. """
        if page.text == None or page.text == u"":
            self.delete(page.name)
        else:
            self.db.set_key(PageManager._PREFIX + page.normalized_name,
                [ page.name, page.text, page.cursor_pos ], sync)

    def delete(self, pagename):
        """ Deletes the given page from the database. """
        self.db.del_key(self._db_key(pagename))

    def iterate(self):
        """ Iterates through the pages in the DB """
        for rec in self.db.pairs():
            if rec[0].startswith(PageManager._PREFIX):
                yield self._decode_page(rec[1])

    def _decode_page(self, dbrecord):
        p = Page()
        p.name = dbrecord[0].decode(PageManager._ENCODING)
        p.text = dbrecord[1].decode(PageManager._ENCODING)
        p.cursor_pos = dbrecord[2]
        return p

    def _db_key(self, pagename):
        return PageManager._PREFIX + Page._normalize_name(pagename)



class Page(object):
    
    def __init__(self, name = None, text = None):
        """ Creates a new page entry with default values. """
        self._cursor_pos = 0
        self.name = name or u""
        self.text = text or u""

    @staticmethod
    def _normalize_name(name):
        return name.strip().lower().encode("utf-8")

    def _set_name(self, name):
        self._name = name
        self.normalized_name = Page._normalize_name(name)

    def _get_name(self):
        return self._name

    name = property(_get_name, _set_name)

    def _revalidate_cursor_pos(self):
        """ Forces the cursor position to the text limits """
        if self._cursor_pos < 0:
            self._cursor_pos = 0
        l = len(self.text)
        if self._cursor_pos > l:
            self._cursor_pos = l

    def _get_cursor_pos(self):
        return self._cursor_pos or 0

    def _set_cursor_pos(self, position):
        self._cursor_pos = position
        self._revalidate_cursor_pos()

    cursor_pos = property(_get_cursor_pos, _set_cursor_pos)

    def _set_text(self, text):
        self._text = text
        self._revalidate_cursor_pos()

    def _get_text(self):
        return self._text

    text = property(_get_text, _set_text)
