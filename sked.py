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
import gobject
import pango


import anydbm           # Berkeley DB abstraction layer.
import os               # Operating system stuff
import re               # Regular expressions
import webbrowser       # System web browser
from datetime import datetime   # for date validation.


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


# Database abstraction ---------------------------------------------------

class DatabaseManager:
    
    def __init__(self, fname):
        self._fname = fname
        self._db = anydbm.open(self._fname, 'c', 0600)

    def has_key(self, key):
        return self._db.has_key(key)

    def set_key(self, key, value):
        self._db[key] = value
        self._db.sync()
        
    def get_key(self, key, default = None):
        if self._db.has_key(key):
            return self._db[key]
        else:
            return default
    
    def del_key(self, key):
        if self._db.has_key(key):
            del self._db[key]
            self._db.sync()
            
    def get_filename(self):
        return self._fname


# Option manager ---------------------------------------------------------

class OptionManager:
    ##TODO:  Add option caching here.
    def __init__(self, db, defaults = {}):
        self._db = db
        self._defs = defaults

    def set_defaults(self, defaults):
        self._defs = defaults

    def get_str(self, key):
        keyn = self._key_name(key)
        return self._db.get_key(keyn, self._defv(key))
    
    def set_str(self, key, value):
        keyn = self._key_name(key)
        self._db.set_key(keyn, value)

    def get_int(self, key):
        s = self.get_str(key)
        if s != None:
            return int(s)
        else:
            return self._defv(key)

    def set_int(self, key, value):
        self.set_str(key, "%d" % value)

    def get_bool(self, key):
        v = self.get_int(key)
        if v != None:
            if v != 0:
                return True
            else:
                return False
        else:
            return self._defv(key)

    def set_bool(self, key, value):
        if value == True:
            self.set_int(key, 1)
        else:
            self.set_int(key, 0)
            
    def get_color(self, key):
        try:
            c = gdk.color_parse(self.get_str(key))
        except ValueError:
            c = gdk.color_parse(self._defv(key))    # for invalid colors.
        return c

    def set_color(self, key, color):
        self.set_str(key, "#%.2X%.2X%.2X" % (color.red/256, color.green/256, color.blue/256))

    def _key_name(self, key):
        return "opt_" + key

    def _defv(self, key):
        if self._defs.has_key(key):
            return self._defs[key]
        else:
            return None

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
        self.clbURL = self.glade.get_widget("clbURL")
        self.fbStandard = self.glade.get_widget("fbStandard")
        self.fbHeader1 = self.glade.get_widget("fbHeader1")
        self.fbHeader2 = self.glade.get_widget("fbHeader2")
        self.fbHeader3 = self.glade.get_widget("fbHeader3")
        self.fbCode = self.glade.get_widget("fbCode")
        self.fbLink = self.glade.get_widget("fbLink")
        self.fbNewLink = self.glade.get_widget("fbNewLink")
        self.fbFormat = self.glade.get_widget("fbFormat")
        self.fbURL = self.glade.get_widget("fbURL")

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
        self.spFormatTime.set_value(self.opt.get_int("format_time"))
        self.spSaveTime.set_value(self.opt.get_int("save_time"))
        self.spUndoLevels.set_value(self.opt.get_int("undo_levels"))
        self.cbShowEdit.set_active(self.opt.get_bool("show_edit_buttons"))

        self.clbStandard.set_color(self.opt.get_color("std_color"))
        self.clbHeader1.set_color(self.opt.get_color("header1_color"))
        self.clbHeader2.set_color(self.opt.get_color("header2_color"))
        self.clbHeader3.set_color(self.opt.get_color("header3_color"))
        self.clbCode.set_color(self.opt.get_color("code_color"))
        self.clbLink.set_color(self.opt.get_color("link_color"))
        self.clbNewLink.set_color(self.opt.get_color("new_link_color"))
        self.clbFormat.set_color(self.opt.get_color("format_color"))
        self.clbURL.set_color(self.opt.get_color("url_link_color"))

        self.fbStandard.set_font_name(self.opt.get_str("std_font"))
        self.fbHeader1.set_font_name(self.opt.get_str("header1_font"))
        self.fbHeader2.set_font_name(self.opt.get_str("header2_font"))
        self.fbHeader3.set_font_name(self.opt.get_str("header3_font"))
        self.fbCode.set_font_name(self.opt.get_str("code_font"))
        self.fbLink.set_font_name(self.opt.get_str("link_font"))
        self.fbNewLink.set_font_name(self.opt.get_str("new_link_font"))
        self.fbFormat.set_font_name(self.opt.get_str("format_font"))
        self.fbURL.set_font_name(self.opt.get_str("url_link_font"))
        
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
        self.opt.set_color("url_link_color", self.clbURL.get_color())

        self.opt.set_str("std_font", self.fbStandard.get_font_name())
        self.opt.set_str("header1_font", self.fbHeader1.get_font_name())
        self.opt.set_str("header2_font", self.fbHeader2.get_font_name())
        self.opt.set_str("header3_font", self.fbHeader3.get_font_name())
        self.opt.set_str("code_font", self.fbCode.get_font_name())
        self.opt.set_str("link_font", self.fbLink.get_font_name())
        self.opt.set_str("new_link_font", self.fbNewLink.get_font_name())
        self.opt.set_str("format_font", self.fbFormat.get_font_name())
        self.opt.set_str("url_link_font", self.fbURL.get_font_name())



# Main application class -------------------------------------------------

class SkedApp:
    DB_FILENAME = "/.sked.db"
    DEF_PREFS = {
        "window_x"  : 0,
        "window_y"  : 0,
        "window_w"  : 700,
        "window_h"  : 400,
        "format_time"   : 3,
        "save_time"     : 15,
        "undo_levels"   : 16,
        "show_edit_buttons" : True,
        "std_color"     : "#000000",
        "header1_color" : "#000000",
        "header2_color" : "#000000",
        "header3_color" : "#000000",
        "code_color"    : "#000000",
        "format_color"  : "#AAAAAA",
        "link_color"    : "#0000FF",
        "new_link_color": "#FF0000",
        "url_link_color": "#0000FF",
        "std_font"      : "Sans 12",
        "header1_font"  : "Sans 18",
        "header2_font"  : "Sans 16",
        "header3_font"  : "Sans 14",
        "code_font"     : "Monospace 12",
        "format_font"   : "Sans 12",
        "link_font"     : "Sans 12",
        "new_link_font" : "Sans 12",
        "url_link_font" : "Sans 12",
        "ft_search"     : False,
        "show_calendar" : True,
        "show_history"  : True,
        "show_gsearch"  : False
    }

    def __init__(self):
        try:
            self.db = DatabaseManager(get_home_dir() + SkedApp.DB_FILENAME)
            self.opt = OptionManager(self.db, SkedApp.DEF_PREFS)
            self.load_interface()
            self.formatTimerID = None
            self.saveTimerID = None
            self.backl = []
            self.forwardl = []
        except Exception:
            alert = gtk.MessageDialog(None,
                gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
                gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE,
               "An initialization error has occurred. Namárië.")
            alert.run()
            self.quit()
    
    def start(self):
        self.curpage = None
        self.restore_window_geometry()
        self.update_options()
        self._on_cmd_date_change()
        self._update_back_forward()
        self.mainWindow.show()

    def save_window_geometry(self):
        x, y = self.mainWindow.get_position()
        w, h = self.mainWindow.get_size()
        self.opt.set_int("window_x", x)
        self.opt.set_int("window_y", y)
        self.opt.set_int("window_w", w)
        self.opt.set_int("window_h", h)

    def restore_window_geometry(self):
        x = self.opt.get_int("window_x")
        y = self.opt.get_int("window_y")
        w = self.opt.get_int("window_w")
        h = self.opt.get_int("window_h")
        self.mainWindow.move(x, y)
        self.mainWindow.resize(w, h)
        
    def update_options(self):
        self.format_time = 1000 * self.opt.get_int("format_time")
        self.save_time = 1000 * self.opt.get_int("save_time")
        self._update_sidebar()
        self._set_edit_buttons()
        self.set_text_tags()
        self.format_text()
        
    def _update_sidebar(self):
        show_calendar = self.opt.get_bool("show_calendar")
        self.calendar.set_property("visible", show_calendar)
        self.tgCalendar.set_property("active", show_calendar)
        
        show_history = self.opt.get_bool("show_history")
        self.bxHistory.set_property("visible", show_history)
        self.tgHistory.set_property("active", show_history)

        show_gsearch = self.opt.get_bool("show_gsearch")
        self.bxGlobalSearch.set_property("visible", show_gsearch)
        self.tgGlobalSearch.set_property("active", show_gsearch)
        
        ft_search = self.opt.get_bool("ft_search")
        self.tgFullTextSearch.set_property("active", ft_search)

    def quit(self, widget = None, data = None):
        self.save_current_page()
        self.save_window_geometry()
        self.mainWindow.destroy()
        gtk.main_quit()

    def load_interface(self):
        self.gladeFile = find_glade_xml("sked")
        self.glade = gtk.glade.XML(self.gladeFile, "wndMain")
        self.glade.signal_autoconnect({
            'on_cmd_about'       : self._on_cmd_about,
            'on_cmd_back'        : self._on_cmd_back,
            'on_cmd_backup'      : self._on_cmd_backup,
            'on_cmd_bold'        : self._on_cmd_bold,
            'on_cmd_calendar_tg' : self._on_cmd_calendar_tg,
            'on_cmd_change_pwd'  : self._on_cmd_change_pwd,
            'on_cmd_code'        : self._on_cmd_code,
            'on_cmd_copy'        : self._on_cmd_copy,
            'on_cmd_cut'         : self._on_cmd_cut,
            'on_cmd_delete'      : self._on_cmd_delete,
            'on_cmd_exit'        : self._on_cmd_exit,
            'on_cmd_forward'     : self._on_cmd_forward,
            'on_cmd_ft_search_tg': self._on_cmd_ft_search_tg,
            'on_cmd_goto'        : self._on_cmd_goto,
            'on_cmd_gsearch_tg'  : self._on_cmd_gsearch_tg,
            'on_cmd_header1'     : self._on_cmd_header1,
            'on_cmd_header2'     : self._on_cmd_header2,
            'on_cmd_header3'     : self._on_cmd_header3,
            'on_cmd_history_tg'  : self._on_cmd_history_tg,
            'on_cmd_home'        : self._on_cmd_home,
            'on_cmd_italic'      : self._on_cmd_italic,
            'on_cmd_link'        : self._on_cmd_link,
            'on_cmd_paste'       : self._on_cmd_paste,
            'on_cmd_preferences' : self._on_cmd_preferences,
            'on_cmd_redo'        : self._on_cmd_redo,
            'on_cmd_restore'     : self._on_cmd_restore,
            'on_cmd_today'       : self._on_cmd_today,
            'on_cmd_tomorrow'    : self._on_cmd_tomorrow,
            'on_cmd_undo'        : self._on_cmd_undo,
            'on_cmd_yesterday'   : self._on_cmd_yesterday,
            'on_text_change'     : self._on_text_change
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
        self.txPageName = self.glade.get_widget("txPageName")
        self.btBack = self.glade.get_widget("btBack")
        self.btForward = self.glade.get_widget("btForward")
        self.mnBack = self.glade.get_widget("mnBack")
        self.mnForward = self.glade.get_widget("mnForward")
        self.bxHistory = self.glade.get_widget("bxHistory")
        self.bxGlobalSearch = self.glade.get_widget("bxGlobalSearch")
        self.tgCalendar = self.glade.get_widget("tgCalendar")
        self.tgHistory = self.glade.get_widget("tgHistory")
        self.tgGlobalSearch = self.glade.get_widget("tgGlobalSearch")
        self.tgFullTextSearch = self.glade.get_widget("tgFullTextSearch")
        
        # We need this signal ID to block the signal on date setting.
        self.date_change_sigid = self.calendar.connect("day-selected",
            self._on_cmd_date_change)
            
        self.set_text_tags()

    def _on_cmd_about(self, widget = None, data = None):
        bx = AboutBox(self.mainWindow)
        bx.show()
        
    def _on_cmd_backup(self, widget = None, data = None):
        pass
        
    def _on_cmd_bold(self, widget = None, data = None):
        self.insert_formatting("*", "*")

    def _on_cmd_calendar_tg(self, widget = None, data = None):
        show_calendar = self.tgCalendar.get_active()
        self.calendar.set_property("visible", show_calendar)
        self.opt.set_bool("show_calendar", show_calendar)
        
    def _on_cmd_change_pwd(self, widget = None, data = None):
        pass
        
    def _on_cmd_code(self, widget = None, data = None):
        self.insert_formatting("|||", "|||")
        
    def _on_cmd_copy(self, widget = None, data = None):
        pass
        
    def _on_cmd_cut(self, widget = None, data = None):
        pass
        
    def _on_cmd_date_change(self, widget = None, data = None):
        self.reset_timers()
        page = self.get_date_str()
        if self.curpage != None and self.curpage != page:
            self.backl.append(self.curpage)
        self.forwardl = []
        self.change_page(page)
        self.update_calendar()
        self._update_back_forward()
        
    def _on_cmd_delete(self, widget = None, data = None):
        self.reset_timers()
        name = self.curpage
        self.change_page("index")
        self.db.del_key(self.page_name(name))
        self.mark_page_on_calendar()
        
    def _on_cmd_exit(self, widget = None, data = None):
        self.quit()

    def _on_cmd_ft_search_tg(self, widget = None, data = None):
        ft_search = self.tgFullTextSearch.get_active()
        self.opt.set_bool("ft_search", ft_search)

    def _on_cmd_gsearch_tg(self, widget = None, data = None):
        show_gsearch = self.tgGlobalSearch.get_active()
        self.bxGlobalSearch.set_property("visible", show_gsearch)
        self.opt.set_bool("show_gsearch", show_gsearch)
        
    def _on_cmd_goto(self, widget = None, data = None):
        self.reset_timers()
        page = self.txPageName.get_text()
        if page == "":
            page = "index"
        if self.curpage != None and self.curpage != page:
            self.backl.append(self.curpage)
        self.forwardl = []
        self.change_page(page)
        self._update_back_forward()
        self.mark_page_on_calendar()
        
    def _on_cmd_header1(self, widget = None, data = None):
        self.insert_formatting("===", "===")

    def _on_cmd_header2(self, widget = None, data = None):
        self.insert_formatting("==", "==")
        
    def _on_cmd_header3(self, widget = None, data = None):
        self.insert_formatting("=", "=")
        
    def _on_cmd_history_tg(self, widget = None, data = None):
        show_history = self.tgHistory.get_active()
        self.bxHistory.set_property("visible", show_history)
        self.opt.set_bool("show_history", show_history)

    def _on_cmd_home(self, widget = None, data = None):
        self.reset_timers()
        page = "index"
        if self.curpage != None and self.curpage != page:
            self.backl.append(self.curpage)
        self.forwardl = []
        self.change_page(page)
        self._update_back_forward()
        self.mark_page_on_calendar()
        
    def _on_cmd_italic(self, widget = None, data = None):
        self.insert_formatting("_", "_")
        
    def _on_cmd_link(self, widget = None, data = None):
        self.insert_formatting("[[", "]]")

    def _on_cmd_back(self, widget = None, data = None):
        if len(self.backl) > 0:
            self.reset_timers()
            page = self.backl.pop()
            self.forwardl.append(self.curpage)
            self.change_page(page)
            self.mark_page_on_calendar()
        self._update_back_forward()

    def _on_cmd_forward(self, widget = None, data = None):
        if len(self.forwardl) > 0:
            self.reset_timers()
            page = self.forwardl.pop()
            if self.curpage != None:
                self.backl.append(self.curpage)
            self.change_page(page)
            self.mark_page_on_calendar()
        self._update_back_forward()
        
    def _on_cmd_paste(self, widget = None, data = None):
        pass
        
    def _on_cmd_preferences(self, widget = None, data = None):
        wnd = PreferencesWindow(self)
        wnd.show()
        
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

    def _on_link(self, tag, widget, event, iter):
        if tag == None:
            return False
        if event.type == gtk.gdk.BUTTON_PRESS:
            start = iter.copy()
            # Search for the begining of the tag
            while not start.begins_tag(tag):
                start.backward_char()
            end = iter.copy()
            # Search for the end of the tag
            while not end.ends_tag(tag):
                end.forward_char()
            link = self.txBuffer.get_text(start, end)
            if link == None or link == "":
                return True
            link = link.decode("utf-8")
            if isinstance(tag, gtk.TextTag) \
            and tag.get_property("name") == "url":
                open_browser(link)
            else:
                self.change_page_link(link)
            return True
        return False
        
    def _on_text_change(self, widget = None, data = None):
        self.reset_timers()
        if not self.format_time or self.format_time == 0:
            self.format_text()
        else:
            self.set_timers()
        
    def _on_format_timer(self):
        self.format_text()
        gobject.source_remove(self.formatTimerID)
        self.formatTimerID = None
        return False    # Stops the timer
    
    def _on_save_timer(self):
        self.save_current_page()
        gobject.source_remove(self.saveTimerID)
        self.saveTimerID = None
        return False    # Stops the timer
        
    def set_timers(self):
        if not self.format_time:
            self.format_time = 1000 * self.opt.get_int("format_time")
        self.formatTimerID = gobject.timeout_add(self.format_time, self._on_format_timer)
        if not self.save_time:
            self.save_time = 1000 * self.opt.get_int("save_time")
        self.saveTimerID = gobject.timeout_add(self.save_time, self._on_save_timer)

    def reset_timers(self):
        if self.formatTimerID:
            gobject.source_remove(self.formatTimerID)
        if self.saveTimerID:
            gobject.source_remove(self.saveTimerID)

    def _set_edit_buttons(self):
        show = self.opt.get_bool("show_edit_buttons")
        self.btSep1.set_visible_horizontal(show)
        self.btUndo.set_visible_horizontal(show)
        self.btRedo.set_visible_horizontal(show)
        self.btCopy.set_visible_horizontal(show)
        self.btCut.set_visible_horizontal(show)
        self.btPaste.set_visible_horizontal(show)
        self.btDelete.set_visible_horizontal(show)
        
    def _update_back_forward(self):
        # Updates the forward/back buttons and menus.
        if len(self.backl) > 20:
            self.backl = self.backl[20:]
        if len(self.forwardl) > 20:
            self.forwardl = self.forwardl[20:]
        b = len(self.backl) > 0
        f = len(self.forwardl) > 0
        self.btForward.set_sensitive(f)
        self.btBack.set_sensitive(b)
        self.mnForward.set_sensitive(f)
        self.mnBack.set_sensitive(b)

    def get_text(self):
        start, end = self.txBuffer.get_bounds()
        return unicode(self.txBuffer.get_text(start, end), "utf-8")

    def insert_formatting(self, before, after):
        ##TODO: Fix this confuse code.
        smark = self.txBuffer.get_selection_bound()
        imark = self.txBuffer.get_insert()
        iiter = self.txBuffer.get_iter_at_mark(imark)
        siter = self.txBuffer.get_iter_at_mark(smark)
        poff = iiter.compare(siter)     # Catapoff! ;)
        if poff == 0:   # No selection.
            self.txBuffer.insert(iiter, before)
            # Previous iiter was invalidated. We need a new one.
            iiter = self.txBuffer.get_iter_at_mark(self.txBuffer.get_insert())
            ioff = iiter.get_offset()   # Cursor will back here.
            self.txBuffer.insert(self.txBuffer.get_iter_at_mark(smark), after)
            self.txBuffer.place_cursor(self.txBuffer.get_iter_at_offset(ioff))
            return
        if poff > 0:    # Inverse selection? Let's put it in the right order.
            tmp_mark = smark
            smark = imark
            imark = tmp_mark
        self.txBuffer.insert(self.txBuffer.get_iter_at_mark(imark), before)
        self.txBuffer.insert(self.txBuffer.get_iter_at_mark(smark), after)

    def set_text_tags(self):
        tagdata = [
            # Note: Later tags have higher priority.
            ['std', {
                'font' : self.opt.get_str("std_font"),
                'foreground' : self.opt.get_str("std_color")
            }],
            ['italic', {
                'style' : pango.STYLE_ITALIC
            }],
            ['bold', {
                'weight' : pango.WEIGHT_BOLD
            }],
            ['code', {
                'font' : self.opt.get_str("code_font"),
                'foreground' : self.opt.get_str("code_color")
            }],
            ['url', {
                'font' : self.opt.get_str("url_link_font"),
                'foreground' : self.opt.get_str("url_link_color"),
                'underline' : pango.UNDERLINE_SINGLE
            }],
            ['newdatelink', {
                'font' : self.opt.get_str("new_link_font"),
                'foreground' : self.opt.get_str("new_link_color"),
                'underline' : pango.UNDERLINE_SINGLE
            }],
            ['datelink', {   # Duplicates 'link' tag for better priority handling.
                'font' : self.opt.get_str("link_font"),
                'foreground' : self.opt.get_str("link_color"),
                'underline' : pango.UNDERLINE_SINGLE
            }],
            ['newlink', {
                'font' : self.opt.get_str("new_link_font"),
                'foreground' : self.opt.get_str("new_link_color"),
                'underline' : pango.UNDERLINE_SINGLE
            }],
            ['link', {
                'font' : self.opt.get_str("link_font"),
                'foreground' : self.opt.get_str("link_color"),
                'underline' : pango.UNDERLINE_SINGLE
            }],
            ['h3', {
                'font' : self.opt.get_str("header3_font"),
                'foreground' : self.opt.get_str("header3_color")
            }],
            ['h2', {
                'font' : self.opt.get_str("header2_font"),
                'foreground' : self.opt.get_str("header2_color")
            }],
            ['h1', {
                'font' : self.opt.get_str("header1_font"),
                'foreground' : self.opt.get_str("header1_color")
            }],
            ['format', {
                'font' : self.opt.get_str("format_font"),
                'foreground' : self.opt.get_str("format_color")
            }]
        ]
        table = self.txBuffer.get_tag_table()
        for pair in tagdata:
            tag = table.lookup(pair[0])
            if tag != None:
                table.remove(tag)
        evtags = ["link", "newlink", "url", "datelink", "newdatelink"]
        for pair in tagdata:
            tagname = pair[0]
            tag = self.txBuffer.create_tag(tagname, **pair[1])
            if tagname in evtags:
                tag.connect("event", self._on_link)

    def format_text(self):
        tx = self.get_text()
        start, end = self.txBuffer.get_bounds() # Apply defaults
        self.txBuffer.remove_all_tags(start, end)
        self.txBuffer.apply_tag_by_name("std", start, end)

        h_re = ur"^\s*(=+)(.+?)(=+)\s*$"        # === Headings ===
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

        bold_re = ur"(\*+)(.+?)(\*+)"       # *bold*
        for match in re.finditer(bold_re, tx):
            self._apply_tag_on_group(match, "format", 1)
            self._apply_tag_on_group(match, "bold", 2)
            self._apply_tag_on_group(match, "format", 3)
        
        italic_re = ur"(_+)(.+?)(_+)"       # _italic_
        for match in re.finditer(italic_re, tx):
            self._apply_tag_on_group(match, "format", 1)
            self._apply_tag_on_group(match, "italic", 2)
            self._apply_tag_on_group(match, "format", 3)

        link_re = ur"(\[\[ *)(.+?)( *\]\])" # [[Link]]
        for match in re.finditer(link_re, tx):
            if self.has_page(match.group(2)):
                style = "link"
            else:
                style = "newlink"
            self._apply_tag_on_group(match, "format", 1)
            self._apply_tag_on_group(match, style, 2)
            self._apply_tag_on_group(match, "format", 3)

        url_re = ur"(([a-zA-Z]+://|www\.)[a-zA-Z0-9._/%#&?~-]+)" # url
        for match in re.finditer(url_re, tx):
            self._apply_tag_on_group(match, "url", 1)

        code_re = ur"(\|\|\|)(.+?)(\|\|\|)" # |||code|||
        for match in re.finditer(code_re, tx, re.MULTILINE| re.DOTALL):
            self._apply_tag_on_group(match, "format", 1)
            self._apply_tag_on_group(match, "code", 2)
            self._apply_tag_on_group(match, "format", 3)

        link_re = ur"([0-3]?[0-9])\/([01]?[0-9])\/([0-9]{1,4})"
        for match in re.finditer(link_re, tx):
            if self.has_page(self.normalize_date_page_name(match.group(0))):
                self._apply_tag_on_group(match, "datelink", 0)
            else:
                self._apply_tag_on_group(match, "newdatelink", 0)

        link_re = ur"([0-9]{1,4})-([01]?[0-9])-([0-3]?[0-9])"
        for match in re.finditer(link_re, tx):
            if self.has_page(match.group(0)):
                self._apply_tag_on_group(match, "datelink", 0)
            else:
                self._apply_tag_on_group(match, "newdatelink", 0)

    def _apply_tag_on_group(self, match, tag, group):
        start = self.txBuffer.get_iter_at_offset(match.start(group))
        end = self.txBuffer.get_iter_at_offset(match.end(group))
        self.txBuffer.apply_tag_by_name(tag, start, end)
        
    def get_date_str(self):
        year, month, day = self.calendar.get_date()
        return "%04d-%02d-%02d" % (year, month + 1, day)

    def change_page(self, page):
        self.reset_timers()
        self.save_current_page()
        page = self.normalize_date_page_name(page)
        self.curpage = page
        self.txPageName.set_text(page)
        self.txBuffer.set_text(self.db.get_key(self.page_name(self.curpage), ""))
        self.format_text()
        
    def save_current_page(self):
        if self.curpage != None:
            tx = self.get_text().encode("utf-8")
            if tx != "":
                self.db.set_key(self.page_name(self.curpage), tx)
            else:
                self.db.del_key(self.page_name(self.curpage))

    def change_page_link(self, page):
        self.reset_timers()
        page = self.normalize_date_page_name(page)
        if self.curpage != None and not self.has_page(page):
            self.db.set_key(self.page_name(page), \
                "[[" + self.curpage + "]]\n===" + page + "===\n")
        if self.curpage != None and self.curpage != page:
            self.backl.append(self.curpage)
        self.forwardl = []
        self.change_page(page)
        self._update_back_forward()
        self.mark_page_on_calendar()
    
    def normalize_date_page_name(self, page):
        match = re.search("([0-9]{1,2})/([0-9]{1,2})/([0-9]{1,4})", page)
        if match != None:
            d = int(match.group(1))
            m = int(match.group(2))
            y = int(match.group(3))
            return "%04d-%02d-%02d" % (y, m, d)
        match = re.search("([0-9]{1,4})-([0-9]{1,2})-([0-9]{1,2})", page)
        if match != None:
            y = int(match.group(1))
            m = int(match.group(2))
            d = int(match.group(3))
            return "%04d-%02d-%02d" % (y, m, d)
        return page

    def has_page(self, page):
        return self.db.has_key(self.page_name(page))
        
    def page_name(self, page):
        # Gets an utf-8 encoded string-or-unicode-string and return a the page
        # name as an utf-8 encoded prefixed string. Sounds confuse for you? :)
        if isinstance(page, unicode):
            upage = page.upper()
        else:
            upage = unicode(page, "utf-8").upper()
        return "pag_" + upage.encode("utf-8")
        
    def mark_page_on_calendar(self):
        if self.curpage != None:
            page = self.normalize_date_page_name(self.curpage)
            match = re.search("([0-9]{4})-([01][0-9])-([0-3][0-9])", page)
            self.calendar.handler_block(self.date_change_sigid)
            if match == None:
                self.calendar.select_day(0)
            else:
                try:
                    d = int(match.group(3))
                    m = int(match.group(2))
                    y = int(match.group(1))
                    datetime(y, m, d)   # Throws an ValueError for bad dates.
                    self.calendar.select_month(m-1, y)
                    self.calendar.select_day(d)
                    self.update_calendar()
                except ValueError:      # Bad date?
                    self.calendar.select_day(0)
            self.calendar.handler_unblock(self.date_change_sigid)

    def update_calendar(self, widget = None):
        year, month, day = self.calendar.get_date()
        if ((year % 4 == 0) and (year % 100 != 0)) \
        or ((year % 4 == 0) and (year % 100 == 0) and (year % 400 == 0)):
            mdays = [ 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 ]
        else:
            mdays = [ 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31 ]

        self.calendar.freeze()
        self.calendar.clear_marks()
        for day in range(1, mdays[month] + 1):
            name = "%04d-%02d-%02d" % (year, month + 1, day)
            if self.has_page(name):
                self.calendar.mark_day(day)
        self.calendar.thaw()




# Initialization.
if __name__ == '__main__':
    app = SkedApp()
    app.start()
    gtk.main()

