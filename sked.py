#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Sked - a toy scheduler with Python, PyGTK and Berkeley DB
(c) 2006 Alexandre Erwin Ittner <aittner@netuno.com.br>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston,
MA 02111-1307, USA.
"""

__CVSID__ = "$Id$"

import pygtk            # GTK+ stuff
pygtk.require('2.0')
import gtk
from gtk import glade
import pango

import anydbm           # Berkeley DB abstraction layer.
import os               # Operating system stuff
import re               # Regular expressions



# Generic functions ------------------------------------------------------

def get_home_dir():
    return os.path.expanduser('~')

def find_glade_xml(xmlfile):
    return search_share_path(xmlfile + ".glade")
    
def search_share_path(fname):
    prefixes = ['', 'usr/share/sked/', 'usr/local/share/sked/']
    for prefix in prefixes:
        if os.path.exists(prefix + fname):
            return prefix + fname;
    for prefix in prefixes:
        if os.path.exists('/' + prefix + fname):
            return '/' + prefix + fname;
    return None




# Database abstraction ---------------------------------------------------

class DatabaseManager:
    
    def __init__(self, fname):
        self._fname = fname
        self._db = anydbm.open(self._fname, 'c', 0600)

    def has_key(self, key):
        return self._db.has_key(key)

    def set_key(self, key, value):
        self._db[key] = value
        
    def get_key(self, key, default = None):
        if self._db.has_key(key):
            return self._db[key]
        else:
            return default
    
    def del_key(self, key):
        if self._db.has_key(key):
            del self._db[key]
            
    def get_filename(self):
        return self._fname


# Option manager ---------------------------------------------------------

class OptionManager:
    
    def __init__(self, db):
        self._db = db

    def get_str(self, key, default = None):
        keyn = self._key_name(key)
        return self._db.get_key(keyn, default)
    
    def set_str(self, key, value):
        keyn = self._key_name(key)
        self._db.set_key(keyn, value)

    def get_int(self, key, default = None):
        s = self.get_str(key, None)
        if s != None:
            return int(s)
        else:
            return default

    def set_int(self, key, value):
        self.set_str(key, "%d" % value)

    def _key_name(self, key):
        return "opt_" + key


# About box --------------------------------------------------------------

class AboutBox:
    # Replace this for a standard Gtk about box.
    
    def __init__(self, pattern = None):
        self._pattern = pattern
    
    def show(self):
        msg = "Sked version 1.0 (devel)\n" \
            + "(c) 2006 Alexandre Erwin Ittner <aittner@netuno.com.br>\n" \
            + "Distributed under the GNU GPL version 2 (or above)\n\n" \
            + "Revision:\n" + __CVSID__
        msgbox = gtk.MessageDialog(self._pattern,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            gtk.MESSAGE_INFO, gtk.BUTTONS_OK, msg)
        msgbox.run()
        msgbox.destroy()




# Main application class -------------------------------------------------

class SkedApp:
    DB_FILENAME = "/.sked.db"
    DEF_WINDOW_X = 0
    DEF_WINDOW_Y = 0
    DEF_WINDOW_W = 600
    DEF_WINDOW_H = 280

    def __init__(self):
        try:
            self.db = DatabaseManager(get_home_dir() + SkedApp.DB_FILENAME)
            self.opt = OptionManager(self.db)
            self.loadInterface()
        except Exception:
            alert = gtk.MessageDialog(None,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE,
                "An initialization error has occurred. Namárië.")
            alert.run()
            self.quit()
    
    def start(self):
        self.curdate = None
        self.restore_window_geometry()
        self.dateChanged()
        self.mainWindow.show()

    def save_window_geometry(self):
        x, y = self.mainWindow.get_position()
        w, h = self.mainWindow.get_size()
        self.opt.set_int("window_x", x)
        self.opt.set_int("window_y", y)
        self.opt.set_int("window_w", w)
        self.opt.set_int("window_h", h)

    def restore_window_geometry(self):
        x = self.opt.get_int("window_x", SkedApp.DEF_WINDOW_X)
        y = self.opt.get_int("window_y", SkedApp.DEF_WINDOW_Y)
        w = self.opt.get_int("window_w", SkedApp.DEF_WINDOW_W)
        h = self.opt.get_int("window_h", SkedApp.DEF_WINDOW_H)
        self.mainWindow.move(x, y)
        self.mainWindow.resize(w, h)

    def quit(self, widget = None, data = None):
        self.dateChanged()
        self.save_window_geometry()
        self.mainWindow.destroy()
        gtk.main_quit()

    def loadInterface(self):
        self.gladeFile = find_glade_xml("sked")
        self.glade = gtk.glade.XML(self.gladeFile, "wndMain")
        
        self.mainWindow = self.glade.get_widget("wndMain")
        self.mainWindow.connect("delete-event", self.quit)

        self.txNote = self.glade.get_widget("NoteText")
        self.txBuffer = self.txNote.get_buffer()

        self.calendar = self.glade.get_widget("Calendar")
        self.calendar.connect("day-selected", self.dateChanged)
        
        self.btQuit = self.glade.get_widget("btQuit")
        self.btQuit.connect("clicked", self.quit)
        
        self.btSave = self.glade.get_widget("btSave")
        self.btSave.connect("clicked", self.dateChanged)
        
        self.btInfo = self.glade.get_widget("btInfo")
        self.btInfo.connect("clicked", self.show_about_box)

        self.setTextTags()

    def setTextTags(self):
        tagdata = {
            'gray' : { 'foreground' : '#888888' },
            'bold' : { 'weight' : pango.WEIGHT_BOLD },
        }
        for tag in tagdata:
            self.txBuffer.create_tag(tag, **tagdata[tag])

    def formatText(self):
        start, end = self.txBuffer.get_bounds()
        tx = self.txBuffer.get_text(start, end)

        bold_re = ur"(\*)(.+?)(\*)"     # *bold*
        for mtc in re.finditer(bold_re, tx):
            start = self.txBuffer.get_iter_at_offset(mtc.start())
            end = self.txBuffer.get_iter_at_offset(mtc.end() - 1)
            self.txBuffer.apply_tag_by_name("bold", start, end)

    def show_about_box(self, widget = None):
        bx = AboutBox(self.mainWindow)
        bx.show()

    def getDateStr(self):
        year, month, day = self.calendar.get_date()
        return "%04d%02d%02d" % (year, month + 1, day)

    def dateChanged(self, widget = None):
        if self.curdate != None:
            start, end = self.txBuffer.get_bounds()
            tx = self.txBuffer.get_text(start, end)
            if tx != "":
                self.db.set_key(self.curdate, tx)
            else:
                self.db.del_key(self.curdate)
        self.curdate = self.getDateStr()
        self.txBuffer.set_text(self.db.get_key(self.curdate, ""))
        self.updateCalendar()
        self.formatText()

    def updateCalendar(self, widget = None):
        # gtk.Calendar doesn't appears to suport other calendars than the
        # Gregorian one (no Islamic, Chinese or Jewish calendars supported).
        # It's a portability bug.

        year, month, day = self.calendar.get_date()
        if ((year % 4 == 0) and (year % 100 != 0)) \
        or ((year % 4 == 0) and (year % 100 == 0) and (year % 400 == 0)):
            mdays = [ 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 ]
        else:
            mdays = [ 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 ]

        self.calendar.clear_marks()
        for day in range(1, mdays[month] + 1):
            key = "%04d%02d%02d" % (year, month + 1, day)
            if self.db.has_key(key):
                self.calendar.mark_day(day)




# Initialization.
if __name__ == '__main__':
    app = SkedApp()
    app.start()
    gtk.main()

