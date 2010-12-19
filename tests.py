#!/usr/bin/python
#-*- coding: utf-8 -*-

import unittest

import os
import random

from libsked import database
from libsked import pages
from libsked import options
from libsked import xmlio
from libsked import utils
from libsked import macros
from libsked import history


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
        p = pages.Page()
        p.name = "nan a ana ana ana ana"
        p.text = str(range(0, 1000))
        p.cursor_pos = 42

    def test_page_fields_2(self):
        p = pages.Page("teste", "peste")
        self.assertEquals(p.name, "teste", "Failed to set name")
        self.assertEquals(p.text, "peste", "Failed to set text")

    def test_cursor_pos_change_ascii(self):
        p = pages.Page()
        p.name = "Bazinga!"
        p.text = str(range(0, 1000))
        p.cursor_pos = 1000
        p.text = "aaaaaaaa"
        self.assertEquals(p.cursor_pos, len(p.text), "Bad cursor_pos")

    def test_cursor_pos_change_unicode(self):
        p = pages.Page()
        p.name = u"Bazinga!"
        p.text = str(range(0, 1000))
        p.cursor_pos = 1000
        p.text = u"««Ðããããããããããããããããããã»»"
        self.assertEquals(p.cursor_pos, len(p.text), "Bad cursor_pos")

    def test_normalized_name_ascii(self):
        p = pages.Page("Warning! ThiS iS A TeST ", "blurp")
        self.assertEquals(p.normalized_name, "warning! this is a test",
            "Failed to normalize ascii name")

    def test_normalized_name_unicode(self):
        p = pages.Page(u"Atenção! ISTo É um Teste ", "blurp")
        self.assertEquals(p.normalized_name, u"atenção! isto é um teste",
            "Failed to normalize unicode name")

    def test_is_date_name(self):
        self.assertEquals(pages.Page.is_date_name("03/02/1983"), True)
        self.assertEquals(pages.Page.is_date_name("3/2/1983"), True)
        self.assertEquals(pages.Page.is_date_name("3/02/1983"), True)
        self.assertEquals(pages.Page.is_date_name("1983-02-03"), True)
        self.assertEquals(pages.Page.is_date_name("1983-2-3"), True)
        self.assertEquals(pages.Page.is_date_name("1983-2-03"), True)
        self.assertEquals(pages.Page.is_date_name("Some name"), False)
        self.assertEquals(pages.Page.is_date_name(u"Aleatório"), False)

    def test_name_date_parsing(self):
        self.assertEquals(pages.Page.parse_date_name("03/02/1983"),
            (u"1983-02-03", 1983, 02, 03), "Failed to parse date name 1")
        self.assertEquals(pages.Page.parse_date_name("1983-02-03"),
            (u"1983-02-03", 1983, 02, 03), "Failed to parse date name 2")
        self.assertEquals(pages.Page.parse_date_name("1983-2-3"),
            (u"1983-02-03", 1983, 02, 03), "Failed to parse date name 3")
        self.assertEquals(pages.Page.parse_date_name("3/2/1983"),
            (u"1983-02-03", 1983, 02, 03), "Failed to parse date name 4")
        self.assertEquals(pages.Page.parse_date_name("nil"),
            ("nil", None, None, None), "Failed to parse date name 5")


class DatabaseLowLevelTestCase(BaseSkedTestCase):

    def setUp(self):
        remove_if_exists(self.DB_NAME)

    def test_hash_functions(self):
        self.assertEquals(database.hash_sha256_str(""), 
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "bad hash result")
        self.assertEquals(database.hash_sha256_str("test"), 
            "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
            "bad hash result")
            
    def test_password_s2k_ascii(self):
        self.assertEquals(database.make_key(""),
            "d4457f2702abef71d5f048a59ad9f0eee83b6dd04426e69aecedf9318af64ed4",
            "bad s2k result")
        self.assertEquals(database.make_key("test"),
            "a38491ab8207c39957e0d7259c2b5760c5c0c5b42d91d21e2e34366ad9e42a31",
            "bad s2k result")

    def test_password_s2k_unicode(self):
        self.assertEquals(database.make_key(u"Paßwö®Ð"),
            "614bc54de3bfc8260708cdc8c81298048e9232ced19c595dfa48752668dabe71",
            "bad s2k result")
        pwd = "Pa\xc3\x9fw\xc3\xb6\xc2\xae\xc3\x90"
        pwd = pwd.decode("utf-8")
        self.assertEquals(database.make_key(pwd),
            "614bc54de3bfc8260708cdc8c81298048e9232ced19c595dfa48752668dabe71",
            "bad s2k result")

    def test_creation(self):
        db = database.EncryptedDatabase(self.DB_NAME)
        self.assertEquals(db.get_lock(), True, "Failed to get lock")
        self.assertEquals(db.is_new, True, "DB should be new")
        db.create(self.PASSWORD)
        self.assertEquals(db.is_ready, True, "DB not ready")
        db.close()
        db.release_lock()

    def test_open(self):
        self.test_creation()
        db = database.EncryptedDatabase(self.DB_NAME)
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
        db = database.EncryptedDatabase(self.DB_NAME)
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
        self.db = database.EncryptedDatabase(self.DB_NAME)
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


class DatabaseAccessTestCase(BaseDBAccessTestCase):

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

    def test_check_password(self):
        self.assertEquals(self.db.check_password(self.PASSWORD), True)
        self.assertEquals(self.db.check_password("Wrong Password"), False)

    def test_iterate_pairs(self):
        keys = [ ]
        for x in range(0, 200):
            k = str(x)
            self.db.set_key(k, "nothing")
            keys.append(k)
        newkeys = [ ]
        for kv in self.db.pairs():
            newkeys.append(kv[0])
            self.assertEquals(kv[1], "nothing", "Corrupted data")
        self.assertEquals(len(newkeys), len(keys), "Missing pairs")

    def test_iterate_keys(self):
        keys = [ ]
        for x in range(0, 200):
            k = str(x)
            self.db.set_key(k, "nothing")
            keys.append(k)
        newkeys = [ ]
        for k in self.db.keys():
            newkeys.append(k)
        self.assertEquals(len(newkeys), len(keys), "Missing keys")

    def test_complex_object_serialization(self):
        x1 = ( 1, 2, 3, "test", u"€1,99", None, True )
        x2 = [ 1, 2, 3, "test", u"€1,99", None, True ]
        x3 = [ [ [ 42 ] ] ]
        x4 = [ "mice", "dolphins", "humans" ]
        self.db.set_key("x1", x1)
        self.db.set_key("x2", x2)
        self.db.set_key("x3", x3)
        self.db.set_key("x4", x4)
        self.assertEquals(self.db.get_key("x1"), x1)
        self.assertEquals(self.db.get_key("x2"), x2)
        self.assertEquals(self.db.get_key("x3"), x3)
        self.assertEquals(self.db.get_key("x4"), x4)


class OptionsTestCase(BaseDBAccessTestCase):
    
    def test_basic_operations(self):
        opt = options.OptionManager(self.db)
        opt.set_str("option1", "value1")
        self.assertEquals(opt.get_str("option1"), "value1")
        opt.set_str("option2", u"Üñï©øÐ€")
        self.assertEquals(opt.get_str("option2"), u"Üñï©øÐ€")
        opt.set_int("answer", 42)
        self.assertEquals(opt.get_int("answer"), 42)
        opt.set_bool("true", True)
        opt.set_bool("false", False)
        self.assertEquals(opt.get_bool("true"), True)
        self.assertEquals(opt.get_bool("false"), False)

    def test_color_parser(self):
        opt = options.OptionManager(self.db)
        opt.set_str("color1", "#000000")
        c = opt.get_color("color1")
        self.assert_(c.red == 0 and c.green == 0 and c.blue == 0)

    def test_persistence(self):
        opt1 = options.OptionManager(self.db)
        opt1.set_str("option1", "value1")
        opt1.set_str("option2", u"Üñï©øÐ€")
        opt1.set_int("answer", 42)
        opt1.set_bool("true", True)
        opt1.set_bool("false", False)
        opt1.save()
        opt2 = options.OptionManager(self.db)
        self.assertEquals(opt2.get_str("option1"), "value1")
        self.assertEquals(opt2.get_str("option2"), u"Üñï©øÐ€")
        self.assertEquals(opt2.get_int("answer"), 42)
        self.assertEquals(opt2.get_bool("true"), True)
        self.assertEquals(opt2.get_bool("false"), False)

    def test_iteration_order(self):
        opt = options.OptionManager(self.db)
        opt.set_str("c", "x")
        opt.set_str("aa", "x")
        opt.set_str("b", "x")
        opt.set_str("a", "x")
        l = [ ]
        for kv in opt.iterate():
            l.append(kv)
        self.assertEquals(l, [('a','x'), ('aa', 'x'), ('b', 'x'), ('c', 'x')])


def _make_some_pages():
    # make some random pages. All them must have a unique name
    pagelist = [ ]
    pagelist.append(pages.Page("a", "-"))
    pagelist.append(pages.Page("b", "-"))
    pagelist.append(pages.Page("c", "-"))

    for i in range(0, 1000):
        pagelist.append(pages.Page(u"Test page nº" + str(i), str(range(i, i+100))))

    pagelist.append(pages.Page("Very long page", str(range(0,100000))))
    pagelist.append(pages.Page(u"Unicode must work",
        u"Any valid char may be used ¹²³§ĸæß€þ/ø\nßḉ§£€»©µn”“aa·”“ŧ"))
    pagelist.append(pages.Page(u"Acentuação", u"Weiß    "))
    pagelist.append(pages.Page(u"XML Chars 1 ><>&\"", u"XML &amp; Chars ><>&\""))
    pagelist.append(pages.Page(u"XML Chars 2 &amp; && 2 ><>&\"",
        u"XML &amp; Chars &&& ! <!-- --> ><>&\"aa '"))

    # Pages named with dates
    pagelist.append(pages.Page("13/02/2010", "nanana"))
    pagelist.append(pages.Page("2010-01-1", "nanana"))
    pagelist.append(pages.Page("3/10/1990", "nanana"))
    pagelist.append(pages.Page("13/01/2010", "nanana"))
    return pagelist



class BasePMTestCase(BaseDBAccessTestCase):

    def setUp(self):
        BaseDBAccessTestCase.setUp(self)
        self.pm = pages.PageManager(self.db)


class PageManagerTestCase(BasePMTestCase):

    def test_page_save_load(self):
        # Here 'P == NP' must be true :)
        p = pages.Page("Test", "blerg")
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
            self.pm.save(pages.Page(origname, "blerg"))
            for name in othernames:
                p = self.pm.load(name)
                self.assertNotEquals(p, None,
                    "Failed to load a page with normalized names")
                self.assertEquals(p.name, origname,
                    "Loaded corrupted page with normalized names")

    def test_page_load_normalized_date_names(self):
        for tup in self.PAGE_NAMES_DATE:
            origname, othernames = tup[0], tup[1]
            self.pm.save(pages.Page(origname, "blerg"))
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
                self.pm.save(pages.Page(origname, "blerg"))
                self.assertNotEquals(self.pm.load(name), None,
                    "Failed to create page to delete")
                self.pm.delete(name)
                self.assertEquals(self.pm.load(name), None,
                    "Failed to delete page")

    def test_exists(self):
        cases = self.PAGE_NAMES_TEXT + self.PAGE_NAMES_DATE
        for tup in cases:
            origname, othernames = tup[0], tup[1]
            self.pm.save(pages.Page(origname, "blerg"))
            for name in othernames:
                self.assertEquals(self.pm.exists(name), True)

    def test_not_exists(self):
        self.assertEquals(self.pm.exists("Acre"), False)

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

    def test_iterate_names(self):
        pages = _make_some_pages()
        names = [ p.normalized_name for p in pages ]
        for p in pages:
            self.pm.save(p)
        loaded = [ ]
        for n in self.pm.iterate_names():
            loaded.append(n)
            self.assertEquals(n in names, True, "Unexpected name")
        self.assertEquals(len(names), len(loaded), "iterate_names() failed")

    def test_page_rewrite(self):
        pagelist = _make_some_pages()
        for p in pagelist:
            self.pm.save(pages.Page(p.name, "Nothing"))
        for p in pagelist:
            self.pm.save(pages.Page(p.name, p.name))
        # Save some random pages
        for i in range(1, 100):
            self.pm.save(random.choice(pagelist))
        for p in pagelist:
            self.pm.save(p)
        for p in pagelist:
            np = self.pm.load(p.name)
            self.assertNotEquals(np, None, "failed to load page")
            self.assertEquals(np.name, p.name, "corrupted page name")
            self.assertEquals(np.text, p.text, "corrupted page text")

    def test_page_rewrite_nonsync(self):
        pagelist = _make_some_pages()
        for p in pagelist:
            self.pm.save(pages.Page(p.name, "Nothing"), False)
        for p in pagelist:
            self.pm.save(pages.Page(p.name, p.name), False)
        # Save some random pages
        for i in range(1, 100):
            self.pm.save(random.choice(pagelist), False)
        for p in pagelist:
            self.pm.save(p, False)
        for p in pagelist:
            np = self.pm.load(p.name)
            self.assertNotEquals(np, None, "failed to load page")
            self.assertEquals(np.name, p.name, "corrupted page name")
            self.assertEquals(np.text, p.text, "corrupted page text")




class SearchTestCase(BasePMTestCase):

    def test_search_system(self):
        self.pm.save(pages.Page(u"test lowercase", u"lowercase text"))
        self.pm.save(pages.Page(u"TEST UPPERCASE", u"UPPERCASE TEXT"))
        self.pm.save(pages.Page(u"test acentuação minúsculas", u"text unicode minúsculas"))
        self.pm.save(pages.Page(u"test ACENTUAÇÃO MAIÚSCULAS", u"TEXT UNICODE MAIÚSCULAS"))
        self.pm.save(pages.Page(u"Nothing", u"test Text text TEXT"))
        self.pm.save(pages.Page(u"None", u"test Text text TEXT"))
        self.pm.save(pages.Page(u"Foo Ni!",         u"Baz Oba Tic pack"))
        self.pm.save(pages.Page(u"Bar Ni! Ni!",     u"Bar Eba tic pick"))
        self.pm.save(pages.Page(u"Baz Ni! Ni! Ni!", u"Foo eba Tac puck"))

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

    def test_search_levenshtein(self):
        self.pm.save(pages.Page(u"Levenshtein xxxxxxx", u"No text"))
        self.pm.save(pages.Page(u"Levenshtein xxxxxx.", u"No text"))
        self.pm.save(pages.Page(u"Levenshtein xxxxx..", u"No text"))
        self.pm.save(pages.Page(u"Levenshtein xxxx...", u"No text"))
        self.pm.save(pages.Page(u"Levenshtein xxx....", u"No text"))
        self.pm.save(pages.Page(u"Levenshtein xx.....", u"No text"))
        self.pm.save(pages.Page(u"Levenshtein x......", u"No text"))
        self.pm.save(pages.Page(u"Levenshtein .......", u"No text"))

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
        pagelist = _make_some_pages()
        for p in pagelist:
            self.pm.save(p)

        opt = options.OptionManager(self.db)
        opt.set_str("test", "test"),
        opt.set_str("complex", u"& <+-×÷> «acentuação»"),
        opt.set_int("answer", 42)
        opt.save()
        saved_options = [ pair for pair in opt.iterate() ]

        h1 = history.HistoryManager(self.db, "history1")
        h1.add("Test page 1")
        h1.add(u"Página com acentuação") 
        h1.save()
        h2 = history.HistoryManager(self.db, "history2")
        h2.add("<Test & page 2>")
        h2.add(u"Página com acentuação") 
        h2.save()
        saved_histories = [ h1.get_items(), h2.get_items() ]
        xmlio.export_xml_file(self.XML_FNAME, self.pm, opt, [ h1, h2 ])

        db2 =  database.EncryptedDatabase(self.OTHER_DB_NAME)
        self.assertEquals(db2.get_lock(), True, "Cannot get lock on db2")
        self.assertEquals(db2.is_new, True, "db2 not new")
        db2.create(self.PASSWORD)
        self.assertEquals(db2.is_ready, True, "db2 not ready")

        pm2 = pages.PageManager(db2)
        opt2 = options.OptionManager(db2)
        xmlio.import_xml_file(self.XML_FNAME, db2, pm2, opt2, True)

        for p in pagelist:
            np = pm2.load(p.name)
            self.assertNotEquals(np, None, "Failed to reload page")
            self.assertEquals(np.name, p.name, "Corrupted name on import")
            self.assertEquals(np.text, p.text, "Corrupted text on import")

        loaded_options = [ pair for pair in opt2.iterate() ]
        self.assertEquals(loaded_options, saved_options, "Corrupted options")

        loaded_histories = [
            history.HistoryManager(db2, "history1").get_items(),
            history.HistoryManager(db2, "history2").get_items()
        ]
        self.assertEquals(loaded_histories, saved_histories)
        
        db2.close()
        db2.release_lock()



class MacrosTestCase(BaseSkedTestCase):
    
    def test_evaluation_simple(self):
        mm = macros.MacroManager()
        mm.add("a", "Error!")
        mm.add("a", "AAAA")
        mm.add("aa", "X")
        mm.add("b", "B")
        mm.add("c", "x\\nx")
        self.assertEquals(mm.find_and_evaluate("zzz a"), "zzz AAAA")
        self.assertEquals(mm.find_and_evaluate("zzz\na"), "zzz\nAAAA")
        self.assertEquals(mm.find_and_evaluate("zzz\nb"), "zzz\nB")
        self.assertEquals(mm.find_and_evaluate("zzz c"), "zzz x\nx")
        self.assertEquals(mm.find_and_evaluate("zzz c  "), "zzz x\nx")
        self.assertEquals(mm.find_and_evaluate("zzz c\n\n"), "zzz x\nx")
        self.assertEquals(mm.find_and_evaluate("zzz\n\n"), None)

    def test_evaluation_empty(self):
        mm = macros.MacroManager()
        mm.add("a", "Error!")
        mm.remove("a")
        self.assertEquals(mm.find_and_evaluate("zzz a"), None)
        self.assertEquals(mm.find_and_evaluate("zzz\na"), None)
        self.assertEquals(mm.find_and_evaluate("zzz\nb"), None)

    def test_evaluation_dict(self):
        def ret_b(): return "B"
        mm = macros.MacroManager()
        mm.add("a", "AA\\aAA")
        mm.add("aa", "X")
        mm.add("b", "X\\b")
        mm.add("c", "x\\n\\b")
        repl = {
            "a": "X",
            "b":  ret_b
        }
        self.assertEquals(mm.find_and_evaluate("zzz a", repl), "zzz AAXAA")
        self.assertEquals(mm.find_and_evaluate("zzz\nb", repl), "zzz\nXB")
        self.assertEquals(mm.find_and_evaluate("zzz c", repl), "zzz x\nB")

    def test_evaluation_save_load(self):
        mm = macros.MacroManager()
        mm.add("a", "AAAA")
        mm.add("aa", "X")
        mm.add("b", "B")
        mm.add("c", "x\\nx")
        s = mm.dump_string()
        mm2 = macros.MacroManager.new_from_string(s)
        self.assertEquals(mm2.find_and_evaluate("zzz a"), "zzz AAAA")
        self.assertEquals(mm2.find_and_evaluate("zzz\na"), "zzz\nAAAA")
        self.assertEquals(mm2.find_and_evaluate("zzz\nb"), "zzz\nB")
        self.assertEquals(mm2.find_and_evaluate("zzz c"), "zzz x\nx")

    def test_load_iterate(self):
        s = """ {
            "a": "AAAA",
            "b": "B",
            "c": "x\\\\nx",
            "d": "None"
        } """
        mm = macros.MacroManager.new_from_string(s)
        d = dict()
        for k, v in mm.iterate():
            d[k] = v
        self.assertEquals(d["a"], "AAAA")
        self.assertEquals(d["b"], "B")
        self.assertEquals(d["c"], "x\\nx")
        self.assertEquals(d["d"], "None")

    def test_iterate_order(self):
        mm = macros.MacroManager()
        mm.add("a", "X")
        mm.add("c", "X")
        mm.add("b", "X")
        mm.add("aa", "X")
        mm.add("xxxx", "X")
        mm.add("ab", "X")
        ret = [ ]
        for k, v in mm.iterate():
            ret.append(k)
        self.assertEquals(ret, [ "a", "aa", "ab", "b", "c", "xxxx" ])


class HistoryTestCase(BaseDBAccessTestCase):

    def test_access_methods(self):
        h = history.HistoryManager(None)
        h.add("1")
        self.assertEquals(h.get_first(), "1")
        h.add("2")
        self.assertEquals(h.get_first(), "2")
        self.assertEquals(h.get_item(0), "2")
        self.assertEquals(h.get_item(1), "1")
        self.assertEquals(h.get_items(), ["2", "1"])
        h.set_items(["4", "5", "6"])
        self.assertEquals(h.get_first(), "4")
        self.assertEquals(h.get_item(1), "5")
        self.assertEquals(h.get_item(2), "6")
        self.assertEquals(h.get_item(3), None)

    def test_max_size(self):
        h = history.HistoryManager(None, None, 3)
        h.add("trash")
        h.add("1")
        h.add("2")
        h.add("3")
        self.assertEquals(h.get_items(), ["3", "2", "1"])

    def test_uniqueness(self):
        h = history.HistoryManager(None, None, 3, True)
        h.add("1")
        h.add("2")
        h.add("3")
        h.add("2")
        h.add("1")
        self.assertEquals(h.get_items(), ["1", "2", "3"])

    def test_uniqueness_case_insensitive(self):
        # Ensure that history uniqueness are case insensitive for both
        # ASCII and Unicode strings.
        h = history.HistoryManager(None, None, 3, True)
        h.add("TEST")
        h.add(u"ATENÇÃO")
        h.add("Test")
        h.add(u"Atenção")
        self.assertEquals(h.get_items(), [u"Atenção", "Test"])

    def test_storage_format(self):
        # This format should not change unoticed.
        h = history.HistoryManager(self.db, "test1")
        h.add("Item1")
        h.add("Item2")
        h.save()
        l = self.db.get_key("test1")
        self.assertEquals(l, ["Item2", "Item1"])

    def test_save_load_roundtrip(self):
        h1 = history.HistoryManager(self.db, "test1")
        h1.add("Item1")
        h1.add("Item2")
        h1.add(u"Atenção")  # Must be Unicode safe
        h1.save()
        h2 = history.HistoryManager(self.db, "test1")
        self.assertEquals(h2.get_items(), [u"Atenção", "Item2", "Item1"])



class BackForwardTestCase(BaseSkedTestCase):
    
    def test_init_state(self):
        bf = history.BackForwardManager(3)
        self.assertEquals(bf.can_back(), False)
        self.assertEquals(bf.can_forward(), False)
        self.assertEquals(bf.back(), None)
        self.assertEquals(bf.forward(), None)

    def test_basic_interaction(self):
        bf = history.BackForwardManager(3)
        # Simulates a basic user interaction.
        # User goes to some page...
        bf.go("Page 1")
        self.assertEquals(bf.can_back(), False)
        self.assertEquals(bf.can_forward(), False)
        # ... and then open another page.
        bf.go("Page 2")
        self.assertEquals(bf.can_back(), True)
        self.assertEquals(bf.can_forward(), False)
        # ... backs to the previous page...
        self.assertEquals(bf.back(), "Page 1")
        self.assertEquals(bf.can_back(), False)
        self.assertEquals(bf.can_forward(), True)
        # ... and forwards to the last page seen. 
        self.assertEquals(bf.forward(), "Page 2")
        self.assertEquals(bf.can_back(), True)
        self.assertEquals(bf.can_forward(), False)

    def test_sequences(self):
        bf = history.BackForwardManager(5)
        bf.go("Page 1")
        bf.go("Page 2")
        bf.go("Page 3")
        bf.go("Page 4")
        self.assertEquals(bf.back(), "Page 3")
        self.assertEquals(bf.back(), "Page 2")
        self.assertEquals(bf.forward(), "Page 3")

    def test_end_of_list(self):
        bf = history.BackForwardManager(5)
        bf.go("Page 1")
        bf.go("Page 2")
        self.assertEquals(bf.back(), "Page 1")
        self.assertEquals(bf.back(), None)
        self.assertEquals(bf.back(), None)
        self.assertEquals(bf.forward(), "Page 2")
        self.assertEquals(bf.forward(), None)
        self.assertEquals(bf.forward(), None)
        self.assertEquals(bf.back(), "Page 1")

    def test_uniqueness(self):
        bf = history.BackForwardManager(5)
        bf.go("Page 1")
        bf.go("Page 2")
        bf.go("Page 2")
        bf.go("Page 2")
        self.assertEquals(bf.back(), "Page 1")

    def test_treeish_interaction(self):
        bf = history.BackForwardManager(10)
        bf.go("Page 1")
        bf.go("Page 2")
        bf.go("Page 3")
        bf.go("Page 4")
        self.assertEquals(bf.back(), "Page 3")
        self.assertEquals(bf.back(), "Page 2")
        bf.go("Page 10")
        bf.go("Page 11")
        self.assertEquals(bf.back(), "Page 10")
        self.assertEquals(bf.back(), "Page 2")
        self.assertEquals(bf.back(), "Page 1")
        self.assertEquals(bf.can_back(), False)
        self.assertEquals(bf.can_forward(), True)
        self.assertEquals(bf.forward(), "Page 2")
        self.assertEquals(bf.forward(), "Page 10")
        self.assertEquals(bf.forward(), "Page 11")

    def test_get_current(self):
        bf = history.BackForwardManager(10)
        self.assertEquals(bf.get_current(), None)
        bf.go("Page 1")
        self.assertEquals(bf.get_current(), "Page 1")
        bf.go("Page 2")
        self.assertEquals(bf.get_current(), "Page 2")
        bf.back()
        self.assertEquals(bf.get_current(), "Page 1")

    def test_go_current(self):
        bf = history.BackForwardManager(10)
        bf.go("Page 1")
        bf.go("Page 2")
        bf.go("Page 3")
        self.assertEquals(bf.back(), "Page 2")
        # "Going to the current place" shall not change the position
        bf.go("Page 2")
        bf.go("PAge 2")
        self.assertEquals(bf.forward(), "Page 3")

class BackForwardPersistenceTestCase(BaseDBAccessTestCase):

    def test_basic_persistence(self):
        bf = history.BackForwardManager(10, self.db, "test_bf")
        bf.go("Page 1")
        bf.go("Page 2")
        bf.go("Page 3")
        bf.go("Page 4")
        bf.save()
        bf2 = history.BackForwardManager(10, self.db, "test_bf")
        self.assertEquals(bf2.back(), "Page 3")
        self.assertEquals(bf2.back(), "Page 2")
        self.assertEquals(bf2.back(), "Page 1")

if __name__ == '__main__':
    unittest.main()
