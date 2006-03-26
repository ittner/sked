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

import anydbm           # Berkeley DB abstractionlayer.
import os               # Operating system stuff


class SkedApp:
    def __init__(self):
        try:
            self.openDB()
            self.loadInterface()
        except Exception:
            alert = gtk.MessageDialog(None,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE,
                "An initialization error has occurred. Namárie.")
            alert.run()
            self.quit()
    
    def start(self):
        self.curdate = None
        self.dateChanged()
        self.mainWindow.show()
        
    def quit(self, widget = None, data = None):
        self.dateChanged()
        self.mainWindow.destroy()
        gtk.main_quit()

    def loadInterface(self):
        self.gladeFile = self.findGladeXML("sked")
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
        self.btInfo.connect("clicked", self.info)

    def openDB(self):
        self.dbFile = self.getHomeDir() + "/.sked.db"
        self.db = anydbm.open(self.dbFile, 'c', 0600)

    def info(self, widget = None):
        msg = "Sked version 1.0\n" \
            + "(c) 2006 Alexandre Erwin Ittner <aittner@netuno.com.br>\n" \
            + "Distributed under the GNU GPL version 2 (or above)\n\n" \
            + "Revision:\n" + __CVSID__
        msgbox = gtk.MessageDialog(self.mainWindow,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            gtk.MESSAGE_INFO, gtk.BUTTONS_OK, msg)
        msgbox.run()
        msgbox.destroy()

    def getDateStr(self):
        year, month, day = self.calendar.get_date()
        return "%04d%02d%02d" % (year, month, day)

    def dateChanged(self, widget = None):
        if self.curdate != None:
            start, end = self.txBuffer.get_bounds()
            tx = self.txBuffer.get_text(start, end)
            if tx != "":
                self.db[self.curdate] = tx
            else:
                if self.db.has_key(self.curdate):
                    del self.db[self.curdate]
        self.curdate = self.getDateStr()
        if self.db.has_key(self.curdate):
            self.txBuffer.set_text(self.db[self.curdate])
        else:
            self.txBuffer.set_text("")

    def getHomeDir(self):
        return os.path.expanduser('~')

    def findGladeXML(self, xmlfile):
        return self.searchSharedPath(xmlfile + ".glade")
    
    def searchSharedPath(self, fname):
        prefixes = ['', 'usr/shared/sked/', 'usr/local/shared/sked/']
        for prefix in prefixes:
            if os.path.exists(prefix + fname):
                return prefix + fname;
        for prefix in prefixes:
            if os.path.exists('/' + prefix + fname):
                return '/' + prefix + fname;
        return None



# Initialization.
if __name__ == '__main__':
    app = SkedApp()
    app.start()
    gtk.main()

