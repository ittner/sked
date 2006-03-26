#!/usr/bin/env python
# -*- coding: utf-8 -*-


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
        except:
            alert = gtk.MessageDialog(buttons = gtk.BUTTONS_CLOSE,
                message_format = "Initialization error. Namárie.")
            alert.run()
            self.quit()
    
    def start(self):
        self.mainWindow.show()
        gtk.main()
        
    def quit(self):
        gtk.main_quit()

    def loadInterface(self):
        self.gladeFile = self.findGladeXML("sked")
        self.glade = gtk.glade.XML(self.gladeFile, 'wndMain')
        self.mainWindow = self.glade.get_widget('wndMain')
        self.calendar = self.glade.get_widget('Calendar')

    def openDB(self):
        self.dbFile = self.getHomeDir() + ".sked.db"
        self.db = anydbm.open(self.dbFile, "n", 0600)

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
    app.run()


