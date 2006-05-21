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

"""
Utility functions.
"""

__CVSID__ = "$Id$"

import pygtk            # GTK+ stuff
pygtk.require('2.0')
import gtk
from gtk import glade
from gtk import gdk
import gobject
import pango

import os               # Operating system stuff
import webbrowser       # System web browser
import datetime         # Date validation


def get_home_dir():
    return os.path.expanduser('~')

def search_share_path(fname):
    prefixes = ['', 'usr/share/sked/', 'usr/local/share/sked/']
    for prefix in prefixes:
        if os.path.exists(prefix + fname):
            return prefix + fname;
    for prefix in prefixes:
        if os.path.exists('/' + prefix + fname):
            return '/' + prefix + fname;
    return None

def open_browser(url):
    try:
        webbrowser.open(url)
    except:
        msgbox = gtk.MessageDialog(None, 
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            gtk.MESSAGE_INFO, gtk.BUTTONS_OK,
            "Failed to start the default browser.")
        msgbox.run()
        msgbox.destroy()

