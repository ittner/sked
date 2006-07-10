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
Importing utility for old databases.
$Id$
"""

import os
import utils
import database
import interface
import anydbm

import pygtk
pygtk.require('2.0')
import gtk



def importdb():
    oldpath = os.path.join(utils.get_home_dir(), ".sked.db")
    try:
        idb = anydbm.open(oldpath, "r")
    except:
        alert = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR,
            gtk.BUTTONS_OK, "No old database found.")
        alert.run()
        alert.destroy()
        gtk.main_quit()
        return
    path = os.path.join(utils.get_home_dir(), ".sked")
    db = database.EncryptedDatabase(path)
    if db.is_new():
        dlg = interface.NewPasswordDialog()
        dlg.set_title("Sked - Importing database")
        dlg.set_text("You are using this program for the first time. "
            "Please enter a password to lock the database")
        pwd = dlg.run()
        if pwd:
            db.set_password(pwd)
    else:
        pwd = u""
        firstime = True
        while not db.try_password(pwd):
            if not firstime:
                alert = gtk.MessageDialog(None, gtk.DIALOG_MODAL,
                    gtk.MESSAGE_ERROR, gtk.BUTTONS_OK,
                    "Wrong password. Please try again.")
                alert.run()
                alert.destroy()
            dlg = interface.PasswordDialog()
            firstime = False
            dlg.set_title("Sked - Password required")
            dlg.set_text("The database is locked. Please enter the password.")
            pwd = dlg.run()
            if pwd == None:
                break
    if db.is_ready():
        for k in idb:
            nk = k.encode("utf-8")
            if nk.startswith("pag_"):
                db.set_key(nk, idb[k].encode("utf-8"))
        alert = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_INFO,
            gtk.BUTTONS_OK, "Done.")
        alert.run()
        alert.destroy()
        gtk.main_quit()
        return
    else:
        alert = gtk.MessageDialog(None, gtk.DIALOG_MODAL, gtk.MESSAGE_ERROR,
            gtk.BUTTONS_OK, "Database not ready.")
        alert.run()
        alert.destroy()
        gtk.main_quit()
    return

if __name__ == "__main__":
    importdb()
    gtk.main()
