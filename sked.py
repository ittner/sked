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
from gtk import gdk
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
    ##TODO:  Add option caching here.
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

    def get_bool(self, key, default = 0):
        v = self.get_int(key, default)
        if v != 0:
            return True
        else:
            return False

    def set_bool(self, key, value):
        if value == True:
            self.set_int(key, 1)
        else:
            self.set_int(key, 0)
            
    def get_color(self, key, default = "#000000"):
        try:
            c = gdk.color_parse(self.get_str(key, default))
        except ValueError:
            c = gdk.color_parse(default)    # for invalid colors.
        return c

    def set_color(self, key, color):
        self.set_str(key, "#%.2X%.2X%.2X" % (color.red/256, color.green/256, color.blue/256))

    def _key_name(self, key):
        return "opt_" + key


# About box --------------------------------------------------------------

class AboutBox:
    ##TODO: Replace this for a standard Gtk about box.
    
    def __init__(self, parent = None):
        self._parent = parent
    
    def show(self):
        msg = "Sked version 1.0 (devel)\n" \
            + "(c) 2006 Alexandre Erwin Ittner <aittner@netuno.com.br>\n" \
            + "Distributed under the GNU GPL version 2 (or above)\n\n" \
            + "Revision:\n" + __CVSID__
        msgbox = gtk.MessageDialog(self._parent,
            gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
            gtk.MESSAGE_INFO, gtk.BUTTONS_OK, msg)
        msgbox.run()
        msgbox.destroy()



# Preferences window -----------------------------------------------------

class PreferencesWindow:
    _wnd = None

    def __init__(self, parent):
        self.parent = parent
        self.opt = parent.opt
        self._load_interface()
        self._set_widget_values()
        
    def show(self):
        if PreferencesWindow._wnd != None:
            PreferencesWindow._wnd.set_focus()
        else:
            PreferencesWindow._wnd = self.wnd
            self.wnd.show()

    def _load_interface(self):
        self.gladeFile = find_glade_xml("sked")

        # Boring code ahead... Is there a better way to do it?
        self.glade = gtk.glade.XML(self.gladeFile, "wndPreferences")
        self.wnd = self.glade.get_widget("wndPreferences")
        self.spFormatTime = self.glade.get_widget("spFormatTime")
        self.spSaveTime = self.glade.get_widget("spSaveTime")
        self.spUndoLevels = self.glade.get_widget("spUndoLevels")
        self.cbShowEdit = self.glade.get_widget("cbShowEdit")
        self.clbStandard = self.glade.get_widget("clbStandard")
        self.clbHeader1 = self.glade.get_widget("clbHeader1")
        self.clbHeader2 = self.glade.get_widget("clbHeader2")
        self.clbHeader3 = self.glade.get_widget("clbHeader3")
        self.clbCode = self.glade.get_widget("clbCode")
        self.clbLink = self.glade.get_widget("clbLink")
        self.clbNewLink = self.glade.get_widget("clbNewLink")
        self.clbFormat = self.glade.get_widget("clbFormat")
        self.fbStandard = self.glade.get_widget("fbStandard")
        self.fbHeader1 = self.glade.get_widget("fbHeader1")
        self.fbHeader2 = self.glade.get_widget("fbHeader2")
        self.fbHeader3 = self.glade.get_widget("fbHeader3")
        self.fbCode = self.glade.get_widget("fbCode")
        self.fbLink = self.glade.get_widget("fbLink")
        self.fbNewLink = self.glade.get_widget("fbNewLink")
        self.fbFormat = self.glade.get_widget("fbFormat")

        self.glade.signal_autoconnect({
            'on_cmd_ok'     : self._on_cmd_ok,
            'on_cmd_cancel' : self._on_cmd_cancel
        })
        
    def _on_cmd_ok(self, widget = None, data = None):
        self._save_widget_values()
        self.wnd.destroy()
        PreferencesWindow._wnd = None
        self.parent.update_options()
        
    def _on_cmd_cancel(self, widget = None, data = None):
        self.wnd.destroy()
        PreferencesWindow._wnd = None

    def _set_widget_values(self):
        self.spFormatTime.set_value(self.opt.get_int("format_time", SkedApp.DEF_FORMAT_TIME))
        self.spSaveTime.set_value(self.opt.get_int("save_time", SkedApp.DEF_SAVE_TIME))
        self.spUndoLevels.set_value(self.opt.get_int("undo_levels", SkedApp.DEF_UNDO_LEVELS))
        self.cbShowEdit.set_active(self.opt.get_bool("show_edit_buttons", SkedApp.DEF_SHOW_EDIT_BUTTONS))

        self.clbStandard.set_color(self.opt.get_color("std_color", SkedApp.DEF_STD_COLOR))
        self.clbHeader1.set_color(self.opt.get_color("header1_color", SkedApp.DEF_STD_COLOR))
        self.clbHeader2.set_color(self.opt.get_color("header2_color", SkedApp.DEF_STD_COLOR))
        self.clbHeader3.set_color(self.opt.get_color("header3_color", SkedApp.DEF_STD_COLOR))
        self.clbCode.set_color(self.opt.get_color("code_color", SkedApp.DEF_STD_COLOR))
        self.clbLink.set_color(self.opt.get_color("link_color", SkedApp.DEF_LINK_COLOR))
        self.clbNewLink.set_color(self.opt.get_color("new_link_color", SkedApp.DEF_NEW_LINK_COLOR))
        self.clbFormat.set_color(self.opt.get_color("format_color", SkedApp.DEF_FORMAT_COLOR))

        self.fbStandard.set_font_name(self.opt.get_str("std_font", SkedApp.DEF_STD_FONT))
        self.fbHeader1.set_font_name(self.opt.get_str("header1_font", SkedApp.DEF_HEADER1_FONT))
        self.fbHeader2.set_font_name(self.opt.get_str("header2_font", SkedApp.DEF_HEADER2_FONT))
        self.fbHeader3.set_font_name(self.opt.get_str("header3_font", SkedApp.DEF_HEADER3_FONT))
        self.fbCode.set_font_name(self.opt.get_str("code_font", SkedApp.DEF_CODE_FONT))
        self.fbLink.set_font_name(self.opt.get_str("link_font", SkedApp.DEF_STD_FONT))
        self.fbNewLink.set_font_name(self.opt.get_str("new_link_font", SkedApp.DEF_STD_FONT))
        self.fbFormat.set_font_name(self.opt.get_str("format_font", SkedApp.DEF_STD_FONT))
        
    def _save_widget_values(self):
        self.opt.set_int("format_time", self.spFormatTime.get_value_as_int())
        self.opt.set_int("save_time", self.spSaveTime.get_value_as_int())
        self.opt.set_int("undo_levels", self.spUndoLevels.get_value_as_int())
        self.opt.set_bool("show_edit_buttons", self.cbShowEdit.get_active())

        self.opt.set_color("std_color", self.clbStandard.get_color())
        self.opt.set_color("header1_color", self.clbHeader1.get_color())
        self.opt.set_color("header2_color", self.clbHeader2.get_color())
        self.opt.set_color("header3_color", self.clbHeader3.get_color())
        self.opt.set_color("code_color", self.clbCode.get_color())
        self.opt.set_color("link_color", self.clbLink.get_color())
        self.opt.set_color("new_link_color", self.clbNewLink.get_color())
        self.opt.set_color("format_color", self.clbFormat.get_color())

        self.opt.set_str("std_font", self.fbStandard.get_font_name())
        self.opt.set_str("header1_font", self.fbHeader1.get_font_name())
        self.opt.set_str("header2_font", self.fbHeader2.get_font_name())
        self.opt.set_str("header3_font", self.fbHeader3.get_font_name())
        self.opt.set_str("code_font", self.fbCode.get_font_name())
        self.opt.set_str("link_font", self.fbLink.get_font_name())
        self.opt.set_str("new_link_font", self.fbNewLink.get_font_name())
        self.opt.set_str("format_font", self.fbFormat.get_font_name())



# Main application class -------------------------------------------------

class SkedApp:
    DB_FILENAME = "/.sked.db"
    DEF_WINDOW_X = 0
    DEF_WINDOW_Y = 0
    DEF_WINDOW_W = 700
    DEF_WINDOW_H = 400
    DEF_FORMAT_TIME = 3
    DEF_SAVE_TIME = 15
    DEF_UNDO_LEVELS = 16
    DEF_SHOW_EDIT_BUTTONS = True
    DEF_STD_COLOR = "#000000"   # For text, headers and code
    DEF_LINK_COLOR = "#0000FF"
    DEF_NEW_LINK_COLOR = "#FF0000"
    DEF_FORMAT_COLOR = "#AAAAAA"
    DEF_STD_FONT = "Sans,Normal 12"
    DEF_HEADER1_FONT = "Sans,Normal 18"
    DEF_HEADER2_FONT = "Sans,Normal 16"
    DEF_HEADER3_FONT = "Sans,Normal 14"
    DEF_CODE_FONT = "Monospace,Normal 12"

    def __init__(self):
        try:
            self.db = DatabaseManager(get_home_dir() + SkedApp.DB_FILENAME)
            self.opt = OptionManager(self.db)
            if self.opt.get_bool("have_defaults", False) == False:
                self.set_default_options()
            self.load_interface()
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
        self.update_options()
        self.mainWindow.show()
        
    def set_default_options(self):
        self.opt.set_bool("have_defaults", True)
        self.opt.set_int("format_time", SkedApp.DEF_FORMAT_TIME)
        self.opt.set_int("save_time", SkedApp.DEF_SAVE_TIME)
        self.opt.set_int("undo_levels", SkedApp.DEF_UNDO_LEVELS)
        self.opt.set_bool("show_edit_buttons", SkedApp.DEF_SHOW_EDIT_BUTTONS)
        self.opt.set_str("std_color", SkedApp.DEF_STD_COLOR)
        self.opt.set_str("header1_color", SkedApp.DEF_STD_COLOR)
        self.opt.set_str("header2_color", SkedApp.DEF_STD_COLOR)
        self.opt.set_str("header3_color", SkedApp.DEF_STD_COLOR)
        self.opt.set_str("code_color", SkedApp.DEF_STD_COLOR)
        self.opt.set_str("format_color", SkedApp.DEF_FORMAT_COLOR)
        self.opt.set_str("link_color", SkedApp.DEF_LINK_COLOR)
        self.opt.set_str("new_link_color", SkedApp.DEF_NEW_LINK_COLOR)
        self.opt.set_str("std_font", SkedApp.DEF_STD_FONT)
        self.opt.set_str("header1_font", SkedApp.DEF_HEADER1_FONT)
        self.opt.set_str("header2_font", SkedApp.DEF_HEADER2_FONT)
        self.opt.set_str("header3_font", SkedApp.DEF_HEADER3_FONT)
        self.opt.set_str("code_font", SkedApp.DEF_CODE_FONT)
        self.opt.set_str("link_font", SkedApp.DEF_STD_FONT)
        self.opt.set_str("new_link_font", SkedApp.DEF_STD_FONT)
        self.opt.set_str("format_font", SkedApp.DEF_STD_FONT)

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
        
    def update_options(self):
        self._set_edit_buttons()

    def quit(self, widget = None, data = None):
        self.dateChanged()
        self.save_window_geometry()
        self.mainWindow.destroy()
        gtk.main_quit()

    def load_interface(self):
        self.gladeFile = find_glade_xml("sked")
        self.glade = gtk.glade.XML(self.gladeFile, "wndMain")
        self.glade.signal_autoconnect({
            'on_cmd_about'      : self._on_cmd_about,
            'on_cmd_backup'     : self._on_cmd_backup,
            'on_cmd_bold'       : self._on_cmd_bold,
            'on_cmd_change_pwd' : self._on_cmd_change_pwd,
            'on_cmd_code'       : self._on_cmd_code,
            'on_cmd_copy'       : self._on_cmd_copy,
            'on_cmd_cut'        : self._on_cmd_cut,
            'on_cmd_date_change': self._on_cmd_date_change,
            'on_cmd_delete'     : self._on_cmd_delete,
            'on_cmd_exit'       : self._on_cmd_exit,
            'on_cmd_goto'       : self._on_cmd_goto,
            'on_cmd_header1'    : self._on_cmd_header1,
            'on_cmd_header2'    : self._on_cmd_header2,
            'on_cmd_header3'    : self._on_cmd_header3,
            'on_cmd_home'       : self._on_cmd_home,
            'on_cmd_italic'     : self._on_cmd_italic,
            'on_cmd_link'       : self._on_cmd_link,
            'on_cmd_next'       : self._on_cmd_next,
            'on_cmd_paste'      : self._on_cmd_paste,
            'on_cmd_preferences': self._on_cmd_preferences,
            'on_cmd_previous'   : self._on_cmd_previous,
            'on_cmd_redo'       : self._on_cmd_redo,
            'on_cmd_restore'    : self._on_cmd_restore,
            'on_cmd_today'      : self._on_cmd_today,
            'on_cmd_tomorrow'   : self._on_cmd_tomorrow,
            'on_cmd_undo'       : self._on_cmd_undo,
            'on_cmd_yesterday'  : self._on_cmd_yesterday
        })

        self.mainWindow = self.glade.get_widget("wndMain")
        self.txNote = self.glade.get_widget("NoteText")
        self.txBuffer = self.txNote.get_buffer()
        self.calendar = self.glade.get_widget("Calendar")
        self.btSep1 = self.glade.get_widget("btSep1")
        self.btUndo = self.glade.get_widget("btUndo")
        self.btRedo = self.glade.get_widget("btRedo")
        self.btCopy = self.glade.get_widget("btCopy")
        self.btCut = self.glade.get_widget("btCut")
        self.btPaste = self.glade.get_widget("btPaste")
        self.btDelete = self.glade.get_widget("btDelete")
        self.set_text_tags()

    def _on_cmd_about(self, widget = None, data = None):
        bx = AboutBox(self.mainWindow)
        bx.show()
        
    def _on_cmd_backup(self, widget = None, data = None):
        pass
        
    def _on_cmd_bold(self, widget = None, data = None):
        pass
        
    def _on_cmd_change_pwd(self, widget = None, data = None):
        pass
        
    def _on_cmd_code(self, widget = None, data = None):
        pass
        
    def _on_cmd_copy(self, widget = None, data = None):
        pass
        
    def _on_cmd_cut(self, widget = None, data = None):
        pass
        
    def _on_cmd_date_change(self, widget = None, data = None):
        self.dateChanged()
        
    def _on_cmd_delete(self, widget = None, data = None):
        pass
        
    def _on_cmd_exit(self, widget = None, data = None):
        self.quit()
        
    def _on_cmd_goto(self, widget = None, data = None):
        pass
        
    def _on_cmd_header1(self, widget = None, data = None):
        pass
        
    def _on_cmd_header2(self, widget = None, data = None):
        pass
        
    def _on_cmd_header3(self, widget = None, data = None):
        pass
        
    def _on_cmd_home(self, widget = None, data = None):
        pass
        
    def _on_cmd_italic(self, widget = None, data = None):
        pass
        
    def _on_cmd_link(self, widget = None, data = None):
        pass
        
    def _on_cmd_next(self, widget = None, data = None):
        pass
        
    def _on_cmd_paste(self, widget = None, data = None):
        pass
        
    def _on_cmd_preferences(self, widget = None, data = None):
        wnd = PreferencesWindow(self)
        wnd.show()
        
    def _on_cmd_previous(self, widget = None, data = None):
        pass
        
    def _on_cmd_redo(self, widget = None, data = None):
        pass
        
    def _on_cmd_restore(self, widget = None, data = None):
        pass
        
    def _on_cmd_today(self, widget = None, data = None):
        pass
        
    def _on_cmd_tomorrow(self, widget = None, data = None):
        pass
        
    def _on_cmd_undo(self, widget = None, data = None):
        pass

    def _on_cmd_yesterday(self, widget = None, data = None):
        pass

    def _set_edit_buttons(self):
        show = self.opt.get_bool("show_edit_buttons", False)
        self.btSep1.set_visible_horizontal(show)
        self.btUndo.set_visible_horizontal(show)
        self.btRedo.set_visible_horizontal(show)
        self.btCopy.set_visible_horizontal(show)
        self.btCut.set_visible_horizontal(show)
        self.btPaste.set_visible_horizontal(show)
        self.btDelete.set_visible_horizontal(show)

    def get_text(self):
        start, end = self.txBuffer.get_bounds()
        return unicode(self.txBuffer.get_text(start, end), "utf-8")

    def set_text_tags(self):
        tagdata = {
            'std': {
                'font' : self.opt.get_str("std_font", SkedApp.DEF_STD_FONT),
                'foreground' : self.opt.get_str("std_color", SkedApp.DEF_STD_COLOR)
            },
            'h1': {
                'font' : self.opt.get_str("header1_font", SkedApp.DEF_HEADER1_FONT),
                'foreground' : self.opt.get_str("header1_color", SkedApp.DEF_FORMAT_COLOR)
            },
            'h2': {
                'font' : self.opt.get_str("header2_font", SkedApp.DEF_HEADER2_FONT),
                'foreground' : self.opt.get_str("header2_color", SkedApp.DEF_FORMAT_COLOR)
            },
            'h3': {
                'font' : self.opt.get_str("header3_font", SkedApp.DEF_HEADER3_FONT),
                'foreground' : self.opt.get_str("header3_color", SkedApp.DEF_FORMAT_COLOR)
            },
            'code': {
                'font' : self.opt.get_str("code_font", SkedApp.DEF_CODE_FONT),
                'foreground' : self.opt.get_str("code_color", SkedApp.DEF_STD_COLOR)
            },
            'link': {
                'font' : self.opt.get_str("link_font", SkedApp.DEF_STD_FONT),
                'foreground' : self.opt.get_str("link_color", SkedApp.DEF_FORMAT_COLOR),
                'underline' : pango.UNDERLINE_SINGLE
            },
            'newlink': {
                'font' : self.opt.get_str("new_link_font", SkedApp.DEF_STD_FONT),
                'foreground' : self.opt.get_str("new_link_color", SkedApp.DEF_FORMAT_COLOR),
                'underline' : pango.UNDERLINE_SINGLE
            },
            'format': {
                'font' : self.opt.get_str("format_font", SkedApp.DEF_STD_FONT),
                'foreground' : self.opt.get_str("format_color", SkedApp.DEF_FORMAT_COLOR)
            },
            'bold' : { 'weight' : pango.WEIGHT_BOLD },
            'italic' : { 'style' : pango.STYLE_ITALIC }
        }
        for tag in tagdata:
            self.txBuffer.create_tag(tag, **tagdata[tag])

    def format_text(self):
        tx = self.get_text()

        h_re = ur"^\s*(=+)(.+?)(=+)\s*$"     # === Headings ===
        for match in re.finditer(h_re, tx, re.MULTILINE):
            cntl = len(match.group(1))
            cntr = len(match.group(3))
            if cntl == cntr and cntl == 3:
                h = "h1"
            elif cntl == cntr and cntl == 2:
                h = "h2"
            elif cntl == cntr and cntl == 1:
                h = "h3"
            else:
                h = None
            if h != None:
                self._apply_tag_on_group(match, "format", 1)
                self._apply_tag_on_group(match, h, 2)
                self._apply_tag_on_group(match, "format", 3)

        bold_re = ur"(\*+)(.+?)(\*+)"     # *bold*
        for match in re.finditer(bold_re, tx):
            self._apply_tag_on_group(match, "format", 1)
            self._apply_tag_on_group(match, "bold", 2)
            self._apply_tag_on_group(match, "format", 3)
        
        italic_re = ur"(_+)(.+?)(_+)"     # _italic_
        for match in re.finditer(italic_re, tx):
            self._apply_tag_on_group(match, "format", 1)
            self._apply_tag_on_group(match, "italic", 2)
            self._apply_tag_on_group(match, "format", 3)

        link_re = ur"(\[\[ *)(.+?)( *\]\])"     # [[Link]]
        for match in re.finditer(link_re, tx):
            self._apply_tag_on_group(match, "format", 1)
            self._apply_tag_on_group(match, "link", 2)
            self._apply_tag_on_group(match, "format", 3)

        code_re = ur"(\|\|\|)(.+?)(\|\|\|)"         # |||code|||
        for match in re.finditer(code_re, tx, re.MULTILINE| re.DOTALL):
            self._apply_tag_on_group(match, "format", 1)
            self._apply_tag_on_group(match, "code", 2)
            self._apply_tag_on_group(match, "format", 3)

        link_re = ur"([0-3][0-9])\/([01][0-9])\/([0-9]{4})"
        for match in re.finditer(link_re, tx):
            self._apply_tag_on_group(match, "link", 0)

        link_re = ur"([0-9]{4})-([01][0-9])-([0-3][0-9])"
        for match in re.finditer(link_re, tx):
            self._apply_tag_on_group(match, "link", 0)


    def _apply_tag_on_group(self, match, tag, group):
        start = self.txBuffer.get_iter_at_offset(match.start(group))
        end = self.txBuffer.get_iter_at_offset(match.end(group))
        self.txBuffer.apply_tag_by_name(tag, start, end)

    def getDateStr(self):
        year, month, day = self.calendar.get_date()
        return "%04d%02d%02d" % (year, month + 1, day)

    def dateChanged(self, widget = None):
        if self.curdate != None:
            tx = self.get_text()
            if tx != "":
                self.db.set_key(self.curdate, tx)
            else:
                self.db.del_key(self.curdate)
        self.curdate = self.getDateStr()
        self.txBuffer.set_text(self.db.get_key(self.curdate, ""))
        self.updateCalendar()
        self.format_text()

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

