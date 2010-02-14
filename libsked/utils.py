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
Utility functions.
"""


import pygtk            # GTK+ stuff
pygtk.require('2.0')
import gtk
from gtk import glade
from gtk import gdk

import os
import webbrowser


def get_home_dir():
    return os.path.expanduser('~')

def data_path(fname = None):
    # Assumes that all libsked data files are in the package directory.
    if fname:
        return os.path.join(os.path.dirname(__file__), fname)
    else:
        return os.path.dirname(__file__)

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

def rename_file(oldn, newn):
    """Renames a file. It's an atomic operation on POSIX systems, thanks
    to underlying rename() implementation. It does not happen in Windows,
    so, we get a race condition."""
    if os.name == 'nt' and os.path.exists(oldn):
        # Windows don't allow us to atomically rename files.
        try:
            os.remove(newn)
        except OSError, exc:
            import errno
            if exc.errno != errno.ENOENT:
                raise exc
    # Rename the file.
    os.rename(oldn, newn)
