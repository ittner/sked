#!/usr/bin/python
#-*- coding: utf-8 -*-

# TODO: Sort these tests.

import os
import random

from libsked.database import EncryptedDatabase
from libsked.pages import Page, PageManager, HAVE_LEVENSHTEIN
from libsked.options import OptionManager
from libsked import xmlio
from libsked import utils


db_fname = "./test1.db"
db_pwd = u"I don't remember the password. Really!"


# Test some Page() methods and properties
pages = []

pages.append(Page("a", "-"))
pages.append(Page("b", "-"))
pages.append(Page("c", "-"))

for i in range(0, 1000):
    pages.append(Page(u"Test page nº" + str(i),  str(range(i, i+100))))

p = Page()
p.name = "nan a ana ana ana ana"
p.text = str(range(0, 1000))
p.cursor_pos = 42
pages.append(p)

p = Page()
p.name = u"Bazinga!"
p.text = str(range(0, 1000))
p.cursor_pos = 1000
p.text = u"««Ðããããããããããããããããããã»»"
if p.cursor_pos != len(p.text):
    raise Exception("Bad cursor pos")
pages.append(p)

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

# Create a new database
db = EncryptedDatabase(db_fname)
if not db.get_lock():
    raise Exception("db.get_lock")
if not db.is_new():
    raise Exception("db exists")
db.create(db_pwd)
if not db.is_ready():
    raise Exception("Create error")
db.close()
db.release_lock()


# Try to open the newly created DB
db = EncryptedDatabase(db_fname)
if not db.get_lock():
    raise Exception("db.get_lock")
if db.try_open("wrong" + db_pwd):
    raise Exception("Password error (wrong)")
if not db.try_open(db_pwd):
    raise Exception("Password error (right)")
if not db.is_ready():
    raise Exception("db not ready")

# Test the 'path' property.
if db.path != os.path.realpath(db_fname):
    raise Exception("db.path != realpath(db_path)")

# Write the test pages.
pm = PageManager(db)
for p in pages:
    pm.save(p, False)

# Save the first page again;
pm.save(pages[0])

# Test the password changing
db.change_pwd("new" + db_pwd)
db.close()
db.release_lock()


db = EncryptedDatabase(db_fname)
if not db.get_lock():
    raise Exception("db.get_lock")
if db.try_open("wrong" + db_pwd):
    raise Exception("Password error (wrong)")
if db.try_open(db_pwd):
    raise Exception("Password error (wrong 2)")
if not db.try_open("new" + db_pwd):
    raise Exception("Password error (right 2)")
if not db.is_ready():
    raise Exception("db not ready")

# Restore the old password
db.change_pwd(db_pwd)
db.close()
db.release_lock()



db = EncryptedDatabase(db_fname)
if not db.get_lock():
    raise Exception("db.get_lock")
if not db.try_open(db_pwd):
    raise Exception("Password error (right)")
if not db.is_ready():
    raise Exception("db not ready")


pm = PageManager(db)

# The database have len(pages) now.

pm.save(Page("Test", "Auto test blerg"))
if not pm.exists("teSt"):
    raise Exception("exists error")

# Test normalized names
if pm.load("test").name != "Test": raise Exception("bad name normalization")
if pm.load(" test").name != "Test": raise Exception("bad name normalization")
if pm.load("test ").name != "Test": raise Exception("bad name normalization")
if pm.load(" test ").name != "Test": raise Exception("bad name normalization")
if pm.load("tEst").name != "Test": raise Exception("bad name normalization")
if pm.load("  teST").name != "Test": raise Exception("bad name normalization")
if pm.load("  teST").name != "Test": raise Exception("bad name normalization")
if pm.load("teST ").name != "Test": raise Exception("bad name normalization")

pm.delete("tesT")
if pm.exists("teSt"):
    raise Exception("delete error")

# Test normalized dates too.
pm.save(Page("03/02/1983", "Date normalization"))
if pm.load("1983-2-3 ").name != "03/02/1983": raise Exception("bad dates")
if pm.load(" 1983-02-3 ").name != "03/02/1983": raise Exception("bad dates")
if pm.load("3/2/1983 ").name != "03/02/1983": raise Exception("bad dates")
if pm.load("3/02/1983 ").name != "03/02/1983": raise Exception("bad dates")
if pm.load("3/02/1983 ").name != "03/02/1983": raise Exception("bad dates")

pm.delete("1983-02-03")
if pm.exists("03/02/1983"):
    raise Exception("delete error (date)")

# The database have len(pages) now.

db.close()
db.release_lock()





db = EncryptedDatabase(db_fname)
if not db.get_lock():
    raise Exception("db.get_lock")
if not db.try_open(db_pwd):
    raise Exception("Password error (right)")
if not db.is_ready():
    raise Exception("db not ready")

pm = PageManager(db)

# Read the pages back
for p in pages:
    newp = pm.load(p.name)
    if p.name != newp.name:
        raise Exception("Corrupted name")
    if p.text != newp.text:
        raise Exception("Corrupted text")
    if p.cursor_pos != newp.cursor_pos:
        raise Exception("Corrupted cursor_pos")

# Rewrite pages some times
for p in pages:
    pm.save(Page(p.name, "Nothing"))
for p in pages:
    pm.save(Page(p.name, p.name))
for p in pages:
    pm.save(Page(p.name, p.text))

# Delete all pages
for p in pages:
    pm.delete(p.name)
for p in pm.iterate():
    raise Exception("No pages were expected here")

# Save some random pages
for i in range(1, 100):
    pm.save(random.choice(pages))
# Put all the pages back
for p in pages:
    pm.save(p, False)
pm.save(pages[0])   # Forces a sync()

# Empty pages are deleted. Names are case-insensitive.
pm.save(Page("Trash", "Blerg!"))
pm.save(Page("traSh", ""))

# The database have len(pages) now.

db.close()
db.release_lock()




db = EncryptedDatabase(db_fname)
if not db.get_lock():
    raise Exception("db.get_lock")
if not db.try_open(db_pwd):
    raise Exception("Password error (right)")
if not db.is_ready():
    raise Exception("db not ready")

pm = PageManager(db)

for p in pages:
    newp = pm.load(p.name)
    if p.name != newp.name:
        raise Exception("Corrupted name")
    if p.text != newp.text:
        raise Exception("Corrupted text")
    if p.cursor_pos != newp.cursor_pos:
        raise Exception("Corrupted cursor_pos")

# The database have len(pages) now.

xml_fname = db_fname + "_test_export.xml"
xmlio.export_xml_file(pm, xml_fname)

db.close()
db.release_lock()



# Test XML importer

db2 =  EncryptedDatabase(db_fname + "_test_import.db")
if not db2.get_lock():
    raise Exception("db2.get_lock")
if not db2.is_new():
    raise Exception("db2 exists")
db2.create(db_pwd)
if not db2.is_ready():
    raise Exception("db2 not ready")

pm2 = PageManager(db2)
xmlio.import_xml_file(pm2, xml_fname)

for p in pages:
    newp = pm2.load(p.name)
    if p.name != newp.name:
        raise Exception("Corrupted name after import")
    if p.text != newp.text:
        raise Exception("Corrupted text after import")

db2.close()
db2.release_lock()



# Test search system

db = EncryptedDatabase(db_fname)
if not db.get_lock():
    raise Exception("db.get_lock")
if not db.try_open(db_pwd):
    raise Exception("Password error (right)")
if not db.is_ready():
    raise Exception("db not ready")

pm = PageManager(db)

# Delete all pages
for p in pm.iterate():
    pm.delete(p.name)
for p in pm.iterate():
    raise Exception("No pages were expected here")

pm.save(Page(u"test lowercase", u"lowercase text"))
pm.save(Page(u"TEST UPPERCASE", u"UPPERCASE TEXT"))
pm.save(Page(u"test acentuação minúsculas", u"text unicode minúsculas"))
pm.save(Page(u"test ACENTUAÇÃO MAIÚSCULAS", u"TEXT UNICODE MAIÚSCULAS"))
pm.save(Page(u"Nothing", u"test Text text TEXT"))
pm.save(Page(u"None", u"test Text text TEXT"))
pm.save(Page(u"Foo Ni!",         u"Baz Oba Tic pack"))
pm.save(Page(u"Bar Ni! Ni!",     u"Bar Eba tic pick"))
pm.save(Page(u"Baz Ni! Ni! Ni!", u"Foo eba Tac puck"))


res = pm.search(u"test", pm.SEARCH_ALL, False, False, True, None)
if len(res) != 4: raise Exception("Search fail", res)

res = pm.search(u"test", pm.SEARCH_ANY, False, False, True, None)
if len(res) != 4:  raise Exception("Search fail", res)

res = pm.search(u"test", pm.SEARCH_EXACT, False, False, True, None)
if len(res) != 4:  raise Exception("Search fail", res)

res = pm.search(u"acentuação", pm.SEARCH_ALL, False, False, True, None)
if len(res) != 2:  raise Exception("Search fail", res)

res = pm.search(u"TEST", pm.SEARCH_ALL, True, False, True, None)
if len(res) != 1:  raise Exception("Search fail", res)

res = pm.search(u"text", pm.SEARCH_ALL, False, True, True, None)
if len(res) != 6: raise Exception("Search fail", res)

res = pm.search(u"úscULas", pm.SEARCH_ALL, False, False, True, None)
if len(res) != 2: raise Exception("Search fail", res)

res = pm.search(u"úsculas", pm.SEARCH_ALL, True, False, True, None)
if len(res) != 1: raise Exception("Search fail", res)

res = pm.search(u"NotHinG NoNe", pm.SEARCH_ALL, False, False, True, None)
if len(res) != 0: raise Exception("Search fail", res)

res = pm.search(u"NotHinG NoNe", pm.SEARCH_ANY, False, False, True, None)
if len(res) != 2: raise Exception("Search fail", res)

res = pm.search(u"Ni!", pm.SEARCH_EXACT, False, False, True, None)
if len(res) != 3: raise Exception("Search fail", res)

res = pm.search(u"Ni! Ni!", pm.SEARCH_EXACT, False, False, True, None)
if len(res) != 2: raise Exception("Search fail", res)

res = pm.search(u"Ni! Ni! Ni!", pm.SEARCH_EXACT, False, False, True, None)
if len(res) != 1: raise Exception("Search fail", res)

res = pm.search(u"tic eba", pm.SEARCH_ALL, False, True, True, None)
if len(res) != 1: raise Exception("Search fail", res)

res = pm.search(u"tic eba", pm.SEARCH_ANY, False, True, True, None)
if len(res) != 3: raise Exception("Search fail", res)

res = pm.search(u"foo Ni!", pm.SEARCH_ALL, False, False, True, None)
if len(res) != 1: raise Exception("Search fail", res)

res = pm.search(u"foo Ni!", pm.SEARCH_ALL, False, True, True, None)
if len(res) != 2: raise Exception("Search fail", res)

retlist = []
pm.search(u"ni!", pm.SEARCH_ANY, False, False, False, retlist.append)
if len(retlist) != 3: raise Exception("Search fail", retlist)

db.close()
db.release_lock()



# Test the levenshtein search

if HAVE_LEVENSHTEIN:
    db = EncryptedDatabase(db_fname)
    if not db.get_lock():
        raise Exception("db.get_lock")
    if not db.try_open(db_pwd):
        raise Exception("Password error (right)")
    if not db.is_ready():
        raise Exception("db not ready")

    pm = PageManager(db)

    # Delete all pages
    for p in pm.iterate():
        pm.delete(p.name)
    for p in pm.iterate():
        raise Exception("No pages were expected here")

    pm.save(Page(u"Levenshtein xxxxxxx", u"No text"))
    pm.save(Page(u"Levenshtein xxxxxx.", u"No text"))
    pm.save(Page(u"Levenshtein xxxxx..", u"No text"))
    pm.save(Page(u"Levenshtein xxxx...", u"No text"))
    pm.save(Page(u"Levenshtein xxx....", u"No text"))
    pm.save(Page(u"Levenshtein xx.....", u"No text"))
    pm.save(Page(u"Levenshtein x......", u"No text"))
    pm.save(Page(u"Levenshtein .......", u"No text"))
    
    results = pm.levenshtein_search("Levenshtein xxxxxxx", 20)
    if results[0][0] != u"Levenshtein xxxxxxx":
        raise Exception("Levenshtein search failed (1)", results[0])
    if results[1][0] != u"Levenshtein xxxxxx.":
        raise Exception("Levenshtein search failed (1)", results[1])
    if results[2][0] != u"Levenshtein xxxxx..":
        raise Exception("Levenshtein search failed (1)", results[2])
    if results[3][0] != u"Levenshtein xxxx...":
        raise Exception("Levenshtein search failed (1)", results[3])
    
    db.close()
    db.release_lock()
else:
    print("No Levenshtein module found. Similarity searches not available.")

