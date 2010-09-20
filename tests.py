#!/usr/bin/python
#-*- coding: utf-8 -*-

import unittest

import os
import random

from libsked.database import EncryptedDatabase
from libsked.pages import Page, PageManager, HAVE_LEVENSHTEIN
from libsked.options import OptionManager
from libsked import xmlio
from libsked import utils


def remove_if_exists(fname):
    if os.path.exists(fname):
        os.remove(fname)



class BaseSkedTestCase(unittest.TestCase):
    DB_NAME = "./test1.db"
    OTHER_DB_NAME = "./test2.db"
    PASSWORD = u"database paßword"
    XML_FNAME = "./test1_dbio.xml"


class PageTestCase(BaseSkedTestCase):

    def test_page_fields(self):
        p = Page()
        p.name = "nan a ana ana ana ana"
        p.text = str(range(0, 1000))
        p.cursor_pos = 42

    def test_page_fields_2(self):
        p = Page("teste", "peste")
        self.assertEquals(p.name, "teste", "Failed to set name")
        self.assertEquals(p.text, "peste", "Failed to set text")

    def test_cursor_pos_change_ascii(self):
        p = Page()
        p.name = "Bazinga!"
        p.text = str(range(0, 1000))
        p.cursor_pos = 1000
        p.text = "aaaaaaaa"
        self.assertEquals(p.cursor_pos, len(p.text), "Bad cursor_pos")

    def test_cursor_pos_change_unicode(self):
        p = Page()
        p.name = u"Bazinga!"
        p.text = str(range(0, 1000))
        p.cursor_pos = 1000
        p.text = u"««Ðããããããããããããããããããã»»"
        self.assertEquals(p.cursor_pos, len(p.text), "Bad cursor_pos")

    def test_normalized_name_ascii(self):
        p = Page("Warning! ThiS iS A TeST ", "blurp")
        self.assertEquals(p.normalized_name, "warning! this is a test",
            "Failed to normalize ascii name")

    def test_normalized_name_unicode(self):
        p = Page(u"Atenção! ISTo É um Teste ", "blurp")
        self.assertEquals(p.normalized_name, u"atenção! isto é um teste",
            "Failed to normalize unicode name")



class DatabaseInitTestCase(BaseSkedTestCase):

    def setUp(self):
        remove_if_exists(self.DB_NAME)

    def test_creation(self):
        db = EncryptedDatabase(self.DB_NAME)
        self.assertEquals(db.get_lock(), True, "Failed to get lock")
        self.assertEquals(db.is_new, True, "DB should be new")
        db.create(self.PASSWORD)
        self.assertEquals(db.is_ready, True, "DB not ready")
        db.close()
        db.release_lock()

    def test_open(self):
        self.test_creation()
        db = EncryptedDatabase(self.DB_NAME)
        self.assertEquals(db.get_lock(), True, "Failed to get lock")
        self.assertEquals(db.is_new, False, "DB should exists now")
        self.assertEquals(db.try_open(u"wrong" + self.PASSWORD), False,
            "database was open with wrong password")
        self.assertEquals(db.try_open(self.PASSWORD), True,
            "Failed to open the database with the right password")
        self.assertEquals(db.is_ready, True, "DB not ready")
        db.close()
        db.release_lock()

    def test_reopen(self):
        self.test_creation()
        db = EncryptedDatabase(self.DB_NAME)
        self.assertEquals(db.get_lock(), True, "Failed to get lock")
        self.assertEquals(db.is_new, False, "DB should exists now")
        self.assertEquals(db.try_open(u"wrong" + self.PASSWORD), False,
            "database was open with wrong password")
        self.assertEquals(db.try_open(self.PASSWORD), True,
            "Failed to open the database with the right password")
        self.assertEquals(db.is_ready, True, "DB not ready")
        db.close()
        db.release_lock()

        self.assertEquals(db.get_lock(), True, "Failed to re-get lock")
        self.assertEquals(db.try_open(self.PASSWORD), True,
            "Failed to reopen the database")
        self.assertEquals(db.is_ready, True, "DB not ready after reopen")
        db.close()
        db.release_lock()



class BaseDBAccessTestCase(BaseSkedTestCase):

    def setUp(self):
        remove_if_exists(self.DB_NAME)
        self.db = EncryptedDatabase(self.DB_NAME)
        if not self.db.get_lock():
            raise Exception("Failed to get lock")
        if not self.db.is_new:
            raise Exception("DB already exists")
        self.db.create(self.PASSWORD)
        if not self.db.is_ready:
            raise Exception("DB not ready")

    def tearDown(self):
        self.db.close()
        self.db.release_lock()
        remove_if_exists(self.DB_NAME)

    def test_data_read_write(self):
        for x in range(0, 200):
            self.db.set_key(str(x), str(x))
        for x in range(0, 200):
            v = str(x)
            nv = self.db.get_key(v)
            self.assertEquals(nv, v, "Corrupted data")

    def test_data_read_write_async(self):
        for x in range(0, 200):
            self.db.set_key(str(x), str(x), False)
        for x in range(0, 200):
            v = str(x)
            nv = self.db.get_key(v)
            self.assertEquals(nv, v, "Corrupted data")
        self.db.sync()

    def test_change_password(self):
        new_password = "blerg"
        for x in range(0, 200):
            self.db.set_key(str(x), str(x))
        self.db.change_pwd(new_password)
        self.db.close()

        self.assertEquals(self.db.try_open(self.PASSWORD), False,
            "DB.open with old password after change")

        self.assertEquals(self.db.try_open(new_password), True,
            "Failed to reopen the DB after password change")

        self.assertEquals(self.db.is_ready, True,
            "DB not ready after password change")

        for x in range(0, 200):
            v = str(x)
            nv = self.db.get_key(v)
            self.assertEquals(nv, v, "Corrupted data")



def _make_some_pages():
    # make some random pages. All them must have a unique name
    pages = [ ]
    pages.append(Page("a", "-"))
    pages.append(Page("b", "-"))
    pages.append(Page("c", "-"))

    for i in range(0, 1000):
        pages.append(Page(u"Test page nº" + str(i), str(range(i, i+100))))

    pages.append(Page("Very long page", str(range(0,100000))))
    pages.append(Page(u"Unicode must work",
        u"Any valid char may be used ¹²³§ĸæß€þ/ø\nßḉ§£€»©µn”“aa·”“ŧ"))
    pages.append(Page(u"Acentuação", u"Weiß    "))
    pages.append(Page(u"XML Chars 1 ><>&\"", u"XML &amp; Chars ><>&\""))
    pages.append(Page(u"XML Chars 2 &amp; && 2 ><>&\"",
        u"XML &amp; Chars &&& ! <!-- --> ><>&\"aa '"))

    # Pages named with dates
    pages.append(Page("13/02/2010", "nanana"))
    pages.append(Page("2010-01-1", "nanana"))
    pages.append(Page("3/10/1990", "nanana"))
    pages.append(Page("13/01/2010", "nanana"))
    return pages



class BasePMTestCase(BaseDBAccessTestCase):

    def setUp(self):
        BaseDBAccessTestCase.setUp(self)
        self.pm = PageManager(self.db)


class PageManagerTestCase(BasePMTestCase):

    def test_page_save_load(self):
        # Here 'P == NP' must be true :)
        p = Page("Test", "blerg")
        self.pm.save(p)
        np = self.pm.load(p.name)
        self.assertEquals(np.name, p.name, "Failed to load page name")
        self.assertEquals(np.text, p.text, "Failed to load page text")
        self.assertEquals(np.cursor_pos, p.cursor_pos,
            "Failed to load page cursor position")

    PAGE_NAMES_TEXT = [
        ( "Test", [ "Test", "test", " test", "test ", " test ", "tEst",
            "  teST", "  teST", "teST ", "    test" ] ),
        ( u"Não", [ u"Não", u"NÃO", u"nÃo", u"NÃo", u"   não", u" NãO  " ]),
        ( u"Straße", [ u"Straße", u"sTraße", u"  Straße", u"StRaßE" ])
    ]

    PAGE_NAMES_DATE = [
        ( "03/02/1983", [ "03/02/1983", "1983-02-03", "1983-2-3 ",
            " 1983-02-3 ", "3/2/1983 ", "3/02/1983 ", "3/02/1983 " ] ),
        ( "2001-02-03", [ "2001-02-03", "3/2/2001", "03/2/2001", "2001-2-3" ])
    ]

    def test_page_load_normalized_names(self):
        for tup in self.PAGE_NAMES_TEXT:
            origname, othernames = tup[0], tup[1]
            self.pm.save(Page(origname, "blerg"))
            for name in othernames:
                p = self.pm.load(name)
                self.assertNotEquals(p, None,
                    "Failed to load a page with normalized names")
                self.assertEquals(p.name, origname,
                    "Loaded corrupted page with normalized names")

    def test_page_load_normalized_date_names(self):
        for tup in self.PAGE_NAMES_DATE:
            origname, othernames = tup[0], tup[1]
            self.pm.save(Page(origname, "blerg"))
            for name in othernames:
                p = self.pm.load(name)
                self.assertNotEquals(p, None,
                    "Failed to load a page with normalized date names")
                self.assertEquals(p.name, origname,
                    "Loaded corrupted page with normalized date names")

    def test_page_delete_names(self):
        cases = self.PAGE_NAMES_TEXT + self.PAGE_NAMES_DATE
        for tup in cases:
            origname, othernames = tup[0], tup[1]
            for name in othernames:
                self.pm.save(Page(origname, "blerg"))
                self.assertNotEquals(self.pm.load(name), None,
                    "Failed to create page to delete")
                self.pm.delete(name)
                self.assertEquals(self.pm.load(name), None,
                    "Failed to delete page")

    def test_page_load_many(self):
        pages = _make_some_pages()
        for p in pages:
            self.pm.save(p)
        for p in pages:
            np = self.pm.load(p.name)
            self.assertNotEquals(np, None, "failed to load page")
            self.assertEquals(np.name, p.name, "corrupted page name")
            self.assertEquals(np.text, p.text, "corrupted page text")

    def test_page_delete_many(self):
        pages = _make_some_pages()
        for p in pages:
            self.pm.save(p)
        for p in pages:
            np = self.pm.load(p.name)
            self.assertNotEquals(np, None, "failed to load page")
            self.assertEquals(np.name, p.name, "corrupted page name")
            self.assertEquals(np.text, p.text, "corrupted page text")
        for p in pages:
            self.pm.delete(p.name)
        for p in self.pm.iterate():
            self.assert_("Delete failed. No pages were expected here")

    def test_iterate(self):
        pages = _make_some_pages()
        for p in pages:
            self.pm.save(p)
        loaded = [ ]
        for p in self.pm.iterate():
            loaded.append(p)
        self.assertEquals(len(pages), len(loaded), "iterate() failed")

    def test_page_rewrite(self):
        pages = _make_some_pages()
        for p in pages:
            self.pm.save(Page(p.name, "Nothing"))
        for p in pages:
            self.pm.save(Page(p.name, p.name))
        # Save some random pages
        for i in range(1, 100):
            self.pm.save(random.choice(pages))
        for p in pages:
            self.pm.save(p)
        for p in pages:
            np = self.pm.load(p.name)
            self.assertNotEquals(np, None, "failed to load page")
            self.assertEquals(np.name, p.name, "corrupted page name")
            self.assertEquals(np.text, p.text, "corrupted page text")

    def test_page_rewrite_nonsync(self):
        pages = _make_some_pages()
        for p in pages:
            self.pm.save(Page(p.name, "Nothing"), False)
        for p in pages:
            self.pm.save(Page(p.name, p.name), False)
        # Save some random pages
        for i in range(1, 100):
            self.pm.save(random.choice(pages), False)
        for p in pages:
            self.pm.save(p, False)
        for p in pages:
            np = self.pm.load(p.name)
            self.assertNotEquals(np, None, "failed to load page")
            self.assertEquals(np.name, p.name, "corrupted page name")
            self.assertEquals(np.text, p.text, "corrupted page text")




class SearchTestCase(BasePMTestCase):

    def teste_search_system(self):
        self.pm.save(Page(u"test lowercase", u"lowercase text"))
        self.pm.save(Page(u"TEST UPPERCASE", u"UPPERCASE TEXT"))
        self.pm.save(Page(u"test acentuação minúsculas", u"text unicode minúsculas"))
        self.pm.save(Page(u"test ACENTUAÇÃO MAIÚSCULAS", u"TEXT UNICODE MAIÚSCULAS"))
        self.pm.save(Page(u"Nothing", u"test Text text TEXT"))
        self.pm.save(Page(u"None", u"test Text text TEXT"))
        self.pm.save(Page(u"Foo Ni!",         u"Baz Oba Tic pack"))
        self.pm.save(Page(u"Bar Ni! Ni!",     u"Bar Eba tic pick"))
        self.pm.save(Page(u"Baz Ni! Ni! Ni!", u"Foo eba Tac puck"))

        res = self.pm.search(u"test", self.pm.SEARCH_ALL, False, False, True, None)
        self.assertEquals(len(res), 4, str(res))

        res = self.pm.search(u"test", self.pm.SEARCH_ANY, False, False, True, None)
        self.assertEquals(len(res), 4, str(res))

        res = self.pm.search(u"test", self.pm.SEARCH_EXACT, False, False, True, None)
        self.assertEquals(len(res), 4, str(res))

        res = self.pm.search(u"acentuação", self.pm.SEARCH_ALL, False, False, True, None)
        self.assertEquals(len(res), 2, str(res))

        res = self.pm.search(u"TEST", self.pm.SEARCH_ALL, True, False, True, None)
        self.assertEquals(len(res), 1, str(res))

        res = self.pm.search(u"text", self.pm.SEARCH_ALL, False, True, True, None)
        self.assertEquals(len(res), 6, str(res))

        res = self.pm.search(u"úscULas", self.pm.SEARCH_ALL, False, False, True, None)
        self.assertEquals(len(res), 2, str(res))

        res = self.pm.search(u"úsculas", self.pm.SEARCH_ALL, True, False, True, None)
        self.assertEquals(len(res), 1, str(res))

        res = self.pm.search(u"NotHinG NoNe", self.pm.SEARCH_ALL, False, False, True, None)
        self.assertEquals(len(res), 0, str(res))

        res = self.pm.search(u"NotHinG NoNe", self.pm.SEARCH_ANY, False, False, True, None)
        self.assertEquals(len(res), 2, str(res))

        res = self.pm.search(u"Ni!", self.pm.SEARCH_EXACT, False, False, True, None)
        self.assertEquals(len(res), 3, str(res))

        res = self.pm.search(u"Ni! Ni!", self.pm.SEARCH_EXACT, False, False, True, None)
        self.assertEquals(len(res), 2, str(res))

        res = self.pm.search(u"Ni! Ni! Ni!", self.pm.SEARCH_EXACT, False, False, True, None)
        self.assertEquals(len(res), 1, str(res))

        res = self.pm.search(u"tic eba", self.pm.SEARCH_ALL, False, True, True, None)
        self.assertEquals(len(res), 1, str(res))

        res = self.pm.search(u"tic eba", self.pm.SEARCH_ANY, False, True, True, None)
        self.assertEquals(len(res), 3, str(res))

        res = self.pm.search(u"foo Ni!", self.pm.SEARCH_ALL, False, False, True, None)
        self.assertEquals(len(res), 1, str(res))

        res = self.pm.search(u"foo Ni!", self.pm.SEARCH_ALL, False, True, True, None)
        self.assertEquals(len(res), 2, str(res))

        retlist = [ ]
        self.pm.search(u"ni!", self.pm.SEARCH_ANY, False, False, False, retlist.append)
        self.assertEquals(len(retlist), 3, "Failed search with callbacks")

    def teste_search_levenshtein(self):
        self.pm.save(Page(u"Levenshtein xxxxxxx", u"No text"))
        self.pm.save(Page(u"Levenshtein xxxxxx.", u"No text"))
        self.pm.save(Page(u"Levenshtein xxxxx..", u"No text"))
        self.pm.save(Page(u"Levenshtein xxxx...", u"No text"))
        self.pm.save(Page(u"Levenshtein xxx....", u"No text"))
        self.pm.save(Page(u"Levenshtein xx.....", u"No text"))
        self.pm.save(Page(u"Levenshtein x......", u"No text"))
        self.pm.save(Page(u"Levenshtein .......", u"No text"))

        results = self.pm.levenshtein_search("Levenshtein xxxxxxx", 20)
        self.assertEquals(results[0], u"Levenshtein xxxxxxx", "Levenshtein search failed (1)")
        self.assertEquals(results[1], u"Levenshtein xxxxxx.", "Levenshtein search failed (2)")
        self.assertEquals(results[2], u"Levenshtein xxxxx..", "Levenshtein search failed (3)")
        self.assertEquals(results[3], u"Levenshtein xxxx...", "Levenshtein search failed (4)")



class XmlIOTestCase(BasePMTestCase):

    def tearDown(self):
        BasePMTestCase.tearDown(self)
        remove_if_exists(self.DB_NAME)
        remove_if_exists(self.XML_FNAME)
        remove_if_exists(self.OTHER_DB_NAME)

    def test_xml_export(self):
        pages = _make_some_pages()
        for p in pages:
            self.pm.save(p)
        xmlio.export_xml_file(self.XML_FNAME, self.pm, None, None)

    def test_xml_import(self):
        self.test_xml_export()
        xmlio.import_xml_file(self.XML_FNAME, self.db, self.pm, None, None)

    def test_xml_roundtrip(self):
        pages = _make_some_pages()
        for p in pages:
            self.pm.save(p)
        xmlio.export_xml_file(self.XML_FNAME, self.pm, None, None)

        db2 =  EncryptedDatabase(self.OTHER_DB_NAME)
        self.assertEquals(db2.get_lock(), True, "Cannot get lock on db2")
        self.assertEquals(db2.is_new, True, "db2 not new")
        db2.create(self.PASSWORD)
        self.assertEquals(db2.is_ready, True, "db2 not ready")

        pm2 = PageManager(db2)
        xmlio.import_xml_file(self.XML_FNAME, db2, pm2, None, None)

        for p in pages:
            np = pm2.load(p.name)
            self.assertNotEquals(np.name, None, "Failed to reload page")
            self.assertEquals(np.name, p.name, "Corrupted name on import")
            self.assertEquals(np.text, p.text, "Corrupted text on import")

        db2.close()
        db2.release_lock()


if __name__ == '__main__':
    unittest.main()
