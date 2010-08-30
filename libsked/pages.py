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

import re

# Uses the module python-levenshtein for similarity searches, if available.
HAVE_LEVENSHTEIN=False
try:
    import Levenshtein
    HAVE_LEVENSHTEIN=True
except: pass


class PageManager(object):
    _ENCODING = "utf-8"
    _PREFIX = "page:"
    SEARCH_ALL = 1
    SEARCH_ANY = 2
    SEARCH_EXACT = 3
    SEARCH_LEVENSHTEIN = 4

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
                ( page.name, page.text, page.cursor_pos ), sync)

    def delete(self, pagename):
        """ Deletes the given page from the database. """
        self.db.del_key(self._db_key(pagename))

    def iterate(self):
        """ Iterates through the pages in the DB """
        for rec in self.db.pairs():
            if rec[0].startswith(PageManager._PREFIX):
                yield self._decode_page(rec[1])

    def _iterate_names(self):
        """ Private method to iterate through normalized page names of a
        database. The names are normalized and returned as Unicode strings
        (not as byte arrays), intended for use by search functions.
        """
        prefixlen = len(PageManager._PREFIX)
        for key in self.db.keys():
            if key.startswith(PageManager._PREFIX):
                yield key[prefixlen:].decode(PageManager._ENCODING)

    def levenshtein_search(self, term, max_results=30):
        """ Searches for pages for names near to the given term according
        to the Levenshtein distance. This method returns a list with up to
        'max_results' page names sorted according to its similarity to the
        search term.
        """
        
        if not HAVE_LEVENSHTEIN: raise Exception("Module not available")
        term = Page.normalize_name(term).decode("utf-8")
        
        # To avoid either giant result queues and too many small list sorting
        # operations. The best value for this parameter is a bit heuristic.
        optimal_queue_len = max(100, 3*max_results)
        worst_result = 2**31    # Interval reasoning to discard bad results.

        results = [ ]
        for curname in self._iterate_names():
            ldist = Levenshtein.distance(term, curname)
            if ldist < worst_result:
                results.append((curname, ldist))
                if len(results) > optimal_queue_len:
                    results = sorted(results, key=lambda result: result[1])
                    results = results[0:max_results]
                    worst_result = results[-1][1]
        results = sorted(results, key=lambda result: result[1])
        results = results[0:max_results]

        # Get the real (non-normalized) names for the pages found.
        retvals = [ ]
        for temp in results:
            retvals.append(self.load(temp[0]).name)
        return retvals
        
    def search(self, terms, mode = SEARCH_ALL, case_sensitive = False,
        full_text = False, return_set = True, callback = None):
        """ Search for pages. 'terms' is a Unicode string with the search
        terms, 'mode' is one of
            SEARCH_ALL, to find pages with all search terms,
            SEARCH_ANY, to find pages with any of the search terms, or,
            SEARCH_EXACT, to find pages with the exact phrase.
        Unless SEARCH_EXACT is given, this method will interpret 'terms' as
        a series of search terms separated with a space (ie u"term1 term2").
        'case_sensitive' is a boolean for case sensitivity, 'full_text', if
        True, forces this method to search the full page text (instead of
        searching the names only), 'return_set', a boolean, instructs this
        method to return a set with the page-objects found. Unless is None,
        'callback' will be called for each page found, giving it as the only
        argument.
        
        BUGS: Very, very slow.
        """
        
        # Prepare search terms
        terms = terms.strip()
        if len(terms) < 1:
            raise ValueError("No search terms were given")
        if not case_sensitive:
            terms = terms.lower()
        if mode == PageManager.SEARCH_ALL or mode == PageManager.SEARCH_ANY:
            term_list = re.split('\s+', terms)
        elif mode == PageManager.SEARCH_EXACT:
            term_list = [ terms ]
        else:
            raise ValueError("Bad search mode", mode)
            
        retset = set()
        for page in self.iterate():
            # Prepare current page terms
            if case_sensitive:
                name = page.name
                if full_text: text = page.text
            else:
                name = page.name.lower()
                if full_text: text = page.text.lower()

            # Search
            match = False
            if mode == self.SEARCH_ALL:
                match = True
                for word in term_list:
                    if name.find(word) < 0 and (full_text == False or text.find(word) < 0):
                        match = False
                        break
            elif mode == self.SEARCH_ANY:
                for word in term_list:
                    if name.find(word) > -1 or (full_text and text.find(word) > -1):
                        match = True
                        break
            elif mode == self.SEARCH_EXACT:
                word = term_list[0]
                if name.find(word) > -1 or (full_text and text.find(word) > -1):
                    match = True

            if match:
                if callback != None: callback(page)
                if return_set: retset.add(page) 

        if return_set:
            return retset

    def _decode_page(self, dbrecord):
        p = Page()
        p.name = dbrecord[0].decode(PageManager._ENCODING)
        p.text = dbrecord[1].decode(PageManager._ENCODING)
        p.cursor_pos = dbrecord[2]
        return p

    def _db_key(self, pagename):
        return PageManager._PREFIX + Page.normalize_name(pagename)



class Page(object):
    
    def __init__(self, name = None, text = None):
        """ Creates a new page entry with default values. """
        self._cursor_pos = 0
        self.name = name or u""
        self.text = text or u""

    @staticmethod
    def normalize_name(name):
        name = name.strip().lower()
        # force dates to the YYYY-MM-DD format.
        match = re.search("([0-9]{1,2})/([0-9]{1,2})/([0-9]{1,4})", name)
        if match != None:
            d = int(match.group(1))
            m = int(match.group(2))
            y = int(match.group(3))
            name = u"%04d-%02d-%02d" % (y, m, d)
        else:
            match = re.search("([0-9]{1,4})-([0-9]{1,2})-([0-9]{1,2})", name)
            if match != None:
                y = int(match.group(1))
                m = int(match.group(2))
                d = int(match.group(3))
                name = u"%04d-%02d-%02d" % (y, m, d)
        return name.encode("utf-8")

    def _set_name(self, name):
        self._name = name
        self.normalized_name = Page.normalize_name(name)

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

    def __repr__(self):
        return "Page:'" + self.normalized_name + "'"

    def clone(self):
        p = Page(self.name, self.text)
        p.cursor_pos = self.cursor_pos
        return p
