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
Main application module.
"""


import pygtk            # GTK+ stuff
pygtk.require('2.0')
import gtk
from gtk import gdk
import gobject
import pango

#try:    # Check for Gtk+ spellcheking
#    import gtkspell
#    HAS_SPELL = True
#except:
#    HAS_SPELL = False
HAS_SPELL = False   # <--- Fix format/spellcheck conflict first.

import os               # Operating system stuff
import re               # Regular expressions
import webbrowser       # System web browser
import datetime         # Date validation
import cPickle          # For options only

import utils
import database
import interface
import xmlio
from history import HistoryManager
from model import *


# Main application class -------------------------------------------------

class SkedApp(interface.BaseDialog):
    ANY_WORD = 1    # Search modes
    ALL_WORDS = 2
    EXACT_PHRASE = 3
    DEF_PREFS = {
        "window_x"  : 0,
        "window_y"  : 0,
        "window_w"  : 700,
        "window_h"  : 500,
        "window_state" : 0, # can be gdk.WINDOW_STATE_MAXIMIZED | ICONIFIED
        "format_time"   : 2,
        "save_time"     : 15,
        "undo_levels"   : 16,
        "show_edit_buttons" : True,
        "std_color"     : "#000000",
        "header1_color" : "#000000",
        "header2_color" : "#000000",
        "header3_color" : "#000000",
        "code_color"    : "#9F5B3A",
        "format_color"  : "#AAAAAA",
        "link_color"    : "#0000FF",
        "new_link_color": "#FF0000",
        "url_link_color": "#0000FF",
        "std_font"      : "Sans 10",
        "header1_font"  : "Sans Bold 16",
        "header2_font"  : "Sans Bold 14",
        "header3_font"  : "Sans Bold 12",
        "code_font"     : "Monospace 10",
        "format_font"   : "Sans 6",
        "link_font"     : "Sans 10",
        "new_link_font" : "Sans 10",
        "url_link_font" : "Sans 10",
        "ft_search"     : False,
        "search_mode"   : ALL_WORDS,
        "show_calendar" : True,
        "show_history"  : True,
        "show_gsearch"  : False,
        "max_history"   : 50,
        "last_directory": utils.get_home_dir()
    }

    def __init__(self, db):
        #try:
            self.db = db
            self.opt = OptionManager(self.db, SkedApp.DEF_PREFS)
            self.formatTimerID = None
            self.saveTimerID = None
            self.backl = []
            self.forwardl = []
            self.undol = []
            self.redol = []
            self.last_undo_cnt = 0;
            self.window_state = 0
            self.history = HistoryManager(self, u"history", True)
            self.history_model = gtk.ListStore(gobject.TYPE_STRING)
            self.history.set_model(self.history_model)
            self.gsearch_model = gtk.ListStore(gobject.TYPE_STRING)
            self._load_interface()
        #except Exception:
        #    interface.error_dialog(None, \
        #        u"An initialization error has occurred. Namárië.")
        #    self.quit()
            
    def start(self, page=None):
        self.curpage = None
        self.restore_window_geometry()
        self.update_options()
        if page == None:
            self.on_cmd_date_change()
        else:
            self.hl_change_page(page)
        self._update_back_forward()
        self._update_undo_redo()
        self.window.show()

    def save_window_geometry(self):
        self.opt.set_int("window_state", self.window_state)
        if self.window_state == 0:
            x, y = self.window.get_position()
            w, h = self.window.get_size()
            self.opt.set_int("window_x", x)
            self.opt.set_int("window_y", y)
            self.opt.set_int("window_w", w)
            self.opt.set_int("window_h", h)

    def restore_window_geometry(self):
        self.window_state = self.opt.get_int("window_state")
        x = self.opt.get_int("window_x")
        y = self.opt.get_int("window_y")
        w = self.opt.get_int("window_w")
        h = self.opt.get_int("window_h")
        if self.window_state & gdk.WINDOW_STATE_MAXIMIZED:
            self.window.maximize()
            self.window.set_default_size(w, h)
        elif self.window_state & gdk.WINDOW_STATE_ICONIFIED:
            self.window.iconify()
            self.window.set_default_size(w, h)
        else:
            self.window.move(x, y)
            self.window.resize(w, h)
    
    def update_options(self):
        self.format_time = 1000 * self.opt.get_int("format_time")
        self.save_time = 1000 * self.opt.get_int("save_time")
        self.max_history = self.opt.get_int("max_history")
        self.undo_levels = self.opt.get_int("undo_levels")
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
        self.mnFullText.set_property("active", ft_search)
        search_mode = self.opt.get_int("search_mode")
        if search_mode == SkedApp.ANY_WORD:
            self.mnAnyWord.set_property("active", True)
        elif search_mode == SkedApp.EXACT_PHRASE:
            self.mnExactPhrase.set_property("active", True)
        else:   # Default. Also, any invalid option will get here.
            self.mnAllWords.set_property("active", True)
            
    def on_window_state(self, widget, event, data = None):
        if widget == self.window:
            st = gdk.WINDOW_STATE_MAXIMIZED | gdk.WINDOW_STATE_ICONIFIED
            self.window_state = event.new_window_state & st
        
    def quit(self, widget = None, data = None):
        self.save_current_page()
        self.save_window_geometry()
        self.history.save()
        self.opt.save()
        self.window.destroy()
        gtk.main_quit()

    def _load_interface(self):
        self.ui_init("main-window.ui")
        self.window = self.ui.get_object("wndMain")
        self.txNote = self.ui.get_object("NoteText")
        self.txBuffer = self.txNote.get_buffer()
        self.calendar = self.ui.get_object("Calendar")
        self.btSep1 = self.ui.get_object("btSep1")
        self.btUndo = self.ui.get_object("btUndo")
        self.btRedo = self.ui.get_object("btRedo")
        self.btCopy = self.ui.get_object("btCopy")
        self.btCut = self.ui.get_object("btCut")
        self.btPaste = self.ui.get_object("btPaste")
        self.btDelete = self.ui.get_object("btDelete")
        self.cbPageName = self.ui.get_object("cbPageName")
        self.txPageName = self.cbPageName.child
        self.btBack = self.ui.get_object("btBack")
        self.btForward = self.ui.get_object("btForward")
        self.mnBack = self.ui.get_object("mnBack")
        self.mnForward = self.ui.get_object("mnForward")
        self.mnUndo = self.ui.get_object("mnUndo")
        self.mnRedo = self.ui.get_object("mnRedo")
        self.bxHistory = self.ui.get_object("bxHistory")
        self.bxGlobalSearch = self.ui.get_object("bxGlobalSearch")
        self.tgCalendar = self.ui.get_object("tgCalendar")
        self.tgHistory = self.ui.get_object("tgHistory")
        self.tgGlobalSearch = self.ui.get_object("tgGlobalSearch")
        self.txGlobalSearch = self.ui.get_object("txGlobalSearch")

        self.btSearchOptions = self.ui.get_object("btSearchOptions")
        self.mnSearchOptions = self.ui.get_object("mnSearchOptions")
        self.mnFullText = self.ui.get_object("mnFullTextSearch")
        self.mnAnyWord = self.ui.get_object("mnAnyWordSearch")
        self.mnAllWords = self.ui.get_object("mnAllWordsSearch")
        self.mnExactPhrase = self.ui.get_object("mnExactPhraseSearch")

        self.bxLocalSearch = self.ui.get_object("bxLocalSearch")
        self.txLocalSearch = self.ui.get_object("txLocalSearch")
        self.txStatus = self.ui.get_object("statusBar")

        self.ui.connect_signals(self)
        self._status_bar_ctx = None
        
        if HAS_SPELL:
            self.spell = gtkspell.Spell(self.txNote)
        else:
            self.spell = None

        self.cbPageName.set_model(self.history_model)
        self.cbPageName.set_text_column(0)

        self.lsHistory = self.ui.get_object("lsHistory")
        self.lsHistory.set_model(self.history_model)
        self.history_column = gtk.TreeViewColumn("Page Name")
        self.lsHistory.append_column(self.history_column)
        self.history_renderer = gtk.CellRendererText()
        self.history_column.pack_start(self.history_renderer, True)
        self.history_column.add_attribute(self.history_renderer, "text", 0)
        
        self.lsGlobalSearch = self.ui.get_object("lsGlobalSearch")
        self.lsGlobalSearch.set_model(self.gsearch_model)
        self.gsearch_column = gtk.TreeViewColumn("Page Name")
        self.lsGlobalSearch.append_column(self.gsearch_column)
        self.gsearch_renderer = gtk.CellRendererText()
        self.gsearch_column.pack_start(self.gsearch_renderer, True)
        self.gsearch_column.add_attribute(self.gsearch_renderer, "text", 0)
    
        # We need this signal ID to block the signal on date setting.
        self.date_change_sigid = self.calendar.connect("day-selected",
            self.on_cmd_date_change)
    
        # Also, we need to prevent the text buffer from dispatching signals
        # during some operations.
        self.text_change_sigid = self.txBuffer.connect("changed",
            self._on_text_change)
        self.text_delete_sigid = self.txBuffer.connect("delete-range",
            self._on_text_delete)
    
        display = gdk.display_manager_get().get_default_display()
        self.clipboard = gtk.Clipboard(display, "CLIPBOARD")
        self.set_text_tags()
        try:
            self.window.set_icon_from_file(utils.data_path("sked.png"))
        except: pass

    def on_cmd_about(self, widget = None, data = None):
        abt = interface.AboutDialog(self.window)
        abt.show()
        
    def on_cmd_export(self, widget = None, data = None):
        # Should be in another class?
        dlg = gtk.FileChooserDialog("Export data", None,
            gtk.FILE_CHOOSER_ACTION_SAVE,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
            gtk.STOCK_OK, gtk.RESPONSE_OK))
            
        dlg.set_default_response(gtk.RESPONSE_OK)
        dir = self.opt.get_str("last_directory") or utils.get_home_dir()
        dlg.set_current_folder(dir)
        
        filter = gtk.FileFilter()
        filter.set_name("Non-encrypted XML files")
        filter.add_pattern("*.xml")
        dlg.add_filter(filter)
       
        # Add support for compressed XML files here.
        while True:
            ret = dlg.run()
            if ret == gtk.RESPONSE_OK:
                fname = dlg.get_filename()
                prename, ext = os.path.splitext(fname)
                if ext == "":
                    fname = fname + ".xml"
                if os.path.exists(fname):
                    if not interface.confirm_file_overwrite(dlg, fname):
                        continue
                self.opt.set_str("last_directory", dlg.get_current_folder())
                dlg.destroy()
                break
            else:
                dlg.destroy()
                return

        if not interface.confirm_yes_no(self.window, u"The database will " \
            "be exported without encryption. Do you want to proceed?"):
            return
        try:
            self.set_status(u'Exporting to "' + fname + u'". Please wait...')
            xmlio.export_xml_file(self.db, fname, u"pag_")
            self.set_status(u'Done')
        except:
            interface.error_dialog(dlg, u"Failed to write the file. Please " \
                "check if the file is not being used and if you have " \
                "sufficient access rights.")
        # Done.
        
    def on_cmd_import(self, widget = None, data = None):
        # Should be in another class?
        dlg = gtk.FileChooserDialog("Import data", None,
            gtk.FILE_CHOOSER_ACTION_OPEN,
            (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
            gtk.STOCK_OK, gtk.RESPONSE_OK))

        dlg.set_default_response(gtk.RESPONSE_OK)
        dir = self.opt.get_str("last_directory") or utils.get_home_dir()
        dlg.set_current_folder(dir)
        
        filter = gtk.FileFilter()
        filter.set_name("Non-encrypted XML files")
        filter.add_pattern("*.xml")
        dlg.add_filter(filter)
       
        # Add support for compressed XML files here.
        fname = None
        while True:
            ret = dlg.run()
            if ret == gtk.RESPONSE_OK:
                fname = dlg.get_filename()
                self.opt.set_str("last_directory", dlg.get_current_folder())
                dlg.destroy()
                break
            else:
                dlg.destroy()
                return

        if not interface.confirm_yes_no(self.window, u"Entries loaded from " \
            "the file will replace entries with the same name on database. " \
            "Do you want to proceed?"):
            return
        try:
            self.set_status(u'Importing from "' + fname + u'". Please wait...')
            xmlio.import_xml_file(self.db, fname)
            self.set_status(u'Done')
            # Reload current page (it can be replaced after importing).
            self.reload_current_page()
        except:
            interface.error_dialog(dlg, u"Failed to read the file. Please " \
                "check if the XML file is well formed and if you have " \
                "sufficient access rights.")
        # Done.

    def on_cmd_bold(self, widget = None, data = None):
        self.insert_formatting("*", "*")

    def on_cmd_calendar_tg(self, widget = None, data = None):
        show_calendar = self.tgCalendar.get_active()
        self.calendar.set_property("visible", show_calendar)
        self.opt.set_bool("show_calendar", show_calendar)
        
    def on_cmd_change_pwd(self, widget = None, data = None):
        dlg = interface.PasswordChangeDialog(self.window, self.db.check_password)
        newpwd = dlg.run()
        if newpwd or newpwd == "":
            self.db.change_pwd(newpwd)
        
    def on_cmd_code(self, widget = None, data = None):
        self.insert_formatting("|||", "|||")
        
    def on_cmd_copy(self, widget = None, data = None):
        self.txBuffer.copy_clipboard(self.clipboard)
        
    def on_cmd_cut(self, widget = None, data = None):
        self.txBuffer.cut_clipboard(self.clipboard,
            self.txNote.get_editable())
        
    def on_cmd_date_change(self, widget = None, data = None):
        self.reset_timers()
        page = self.get_date_str()
        if self.curpage != None and self.curpage.upper() != page.upper():
            self.backl.append(self.curpage)
        self.forwardl = []
        self.change_page(page)
        self.update_calendar()
        self._update_back_forward()
        
    def on_cmd_delete(self, widget = None, data = None):
        self.reset_timers()
        page = self.curpage
        if page == None: return
        ret = interface.confirm_yes_no(self.window, \
            u"Delete the page \"" + page + u"\" forever?")
        if ret:
            self.enqueue_undo()
            if len(self.backl) > 0:
                lastpage = self.backl.pop()
            else:
                lastpage = "index"
            self.hl_change_page(lastpage)
            self.db.del_key(self.page_name(page))
            if page == lastpage:
                self.set_text("")
        
    def on_cmd_exit(self, widget = None, data = None):
        self.quit()
        
    def on_cmd_lsearch_next(self, widget = None, data = None):
        tx = self.txLocalSearch.get_text().decode("utf-8")
        iiter = self.txBuffer.get_iter_at_mark(self.txBuffer.get_insert())
        ret = iiter.forward_search(tx, 0)
        if not ret:
            siter, eiter = self.txBuffer.get_bounds()
            ret = siter.forward_search(tx, 0)
        if ret:
            self.txBuffer.select_range(ret[1], ret[0])
            self.txNote.scroll_to_iter(ret[0], 0.0)

    def on_cmd_lsearch_prev(self, widget = None, data = None):
        tx = self.txLocalSearch.get_text().decode("utf-8")
        iiter = self.txBuffer.get_iter_at_mark(self.txBuffer.get_insert())
        ret = iiter.backward_search(tx, 0)
        if not ret:
            siter, eiter = self.txBuffer.get_bounds()
            ret = eiter.backward_search(tx, 0)
        if ret:
            self.txBuffer.select_range(ret[0], ret[1])
            self.txNote.scroll_to_iter(ret[0], 0.0)
        
    def on_cmd_lsearch_show(self, widget = None, data = None):
        self.bxLocalSearch.set_property("visible", True)
        self.txLocalSearch.grab_focus()

    def on_cmd_lsearch_hide(self, widget = None, data = None):
        self.bxLocalSearch.set_property("visible", False)
        
    def on_cmd_lsearch_tg(self, widget = None, data = None):
        pass
        
    def on_lsearch_keypress(self, widget = None, event = None, data = None):
        if widget == self.txLocalSearch and event.type == gdk.KEY_PRESS \
        and event.keyval == gtk.keysyms.Escape:
            self.on_cmd_lsearch_hide()
            return True
        return False
        
    def on_cmd_ft_search(self, widget = None, data = None):
        ft_search = self.mnFullText.get_active()
        self.opt.set_bool("ft_search", ft_search)
        
    def on_cmd_search_mode(self, widget = None, data = None):
        mode = SkedApp.ALL_WORDS    # default.
        if self.mnAnyWord.get_property("active") == True:
            mode = SkedApp.ANY_WORD
        elif self.mnAllWords.get_property("active") == True:
            mode = SkedApp.ALL_WORDS
        elif self.mnExactPhrase.get_property("active") == True:
            mode = SkedApp.EXACT_PHRASE
        self.opt.set_int("search_mode", mode)

    def on_cmd_gsearch_tg(self, widget = None, data = None):
        show_gsearch = self.tgGlobalSearch.get_active()
        self.bxGlobalSearch.set_property("visible", show_gsearch)
        self.opt.set_bool("show_gsearch", show_gsearch)
        
    def on_cmd_gsearch_mn(self, widget = None, data = None):
        if self.tgGlobalSearch.get_active() == False:
            self.tgGlobalSearch.set_active(True)
        #self.tgHistory.set_active(False)
        self.txGlobalSearch.grab_focus()
        
    def on_cmd_gsearch(self, widget = None, data = None):
        ## Big, ugly and sloooooooow! Optimization needed!!
        text = self.txGlobalSearch.get_text().decode("utf-8")
        text = text.strip().upper()
        if self.mnAnyWord.get_property("active") == True:
            mode = SkedApp.ANY_WORD
            slist = re.split('\s+', text)
        elif self.mnAllWords.get_property("active") == True:
            mode = SkedApp.ALL_WORDS
            slist = re.split('\s+', text)
        elif self.mnExactPhrase.get_property("active") == True:
            mode = SkedApp.EXACT_PHRASE
            slist = [ text ]
        else:
            interface.error_dialog(self.window, \
                "You must select a search mode.")
            return
        if len(slist) == 0 or slist[0] == "":
            interface.error_dialog(self.window, \
                "You must supply a search string.")
            return
        fts = self.mnFullText.get_active()
        self.gsearch_model.clear()
        for key, data in self.db.pairs():
            if not key.startswith("pag_"):
                continue
            page = key[4:]
            upage = page.upper()
            if fts:
                data = data.upper()
            if mode == SkedApp.ANY_WORD:
                for word in slist:
                    if upage.find(word) != -1:
                        self.gsearch_model.append([page])
                        break
                    if fts:
                        if data.find(word) != -1:
                            self.gsearch_model.append([page])
                            break
            elif mode == SkedApp.ALL_WORDS:
                has = True
                for word in slist:
                    if upage.find(word) == -1:
                        if fts:
                            if data.find(word) == -1:
                                has = False
                                break
                        else:
                            has = False
                            break
                if has:
                    self.gsearch_model.append([page])
            else:
                if upage.find(slist[0]) != -1:
                    self.gsearch_model.append([page])
                elif fts:
                    if data.find(slist[0]) != -1:
                        self.gsearch_model.append([page])

    def on_cmd_sort_lines(self, widget = None, data = None):
        smark = self.txBuffer.get_selection_bound()
        imark = self.txBuffer.get_insert()
        iiter = self.txBuffer.get_iter_at_mark(imark)
        siter = self.txBuffer.get_iter_at_mark(smark)
        poff = iiter.compare(siter)     # Catapoff! ;)
        if poff == 0:   # No selection.
            return
        elif poff > 0:  # Inverse selection? Let's put it in the right order.
            tmp_iter = siter
            siter = iiter
            iiter = tmp_iter
        text = self.txBuffer.get_text(siter, iiter).decode("utf-8")
        arr = text.split(u"\n")
        arr.sort()
        text = u"\n".join(arr)
        self.txBuffer.delete(siter, iiter)
        self.txBuffer.insert(siter, text)
        self.format_text()
    
    def on_cmd_goto(self, widget = None, data = None):
        self.hl_change_page(self.txPageName.get_text().decode("utf-8"))
        
    def on_cmd_header1(self, widget = None, data = None):
        self.insert_formatting("===", "===")

    def on_cmd_header2(self, widget = None, data = None):
        self.insert_formatting("==", "==")
        
    def on_cmd_header3(self, widget = None, data = None):
        self.insert_formatting("=", "=")

    def on_cmd_history_go(self, widget = None, path = None, column = None):
        return self.on_cmd_listbox_go(widget, path, column)

    def on_cmd_listbox_go(self, widget = None, path = None, column = None):
        # Should be used for global search too.
        model, iter = widget.get_selection().get_selected()
        page = model.get_value(iter, 0)
        if page != None:
            self.hl_change_page(page)

    def on_cmd_history_tg(self, widget = None, data = None):
        show_history = self.tgHistory.get_active()
        self.bxHistory.set_property("visible", show_history)
        self.opt.set_bool("show_history", show_history)

    def on_cmd_home(self, widget = None, data = None):
        self.hl_change_page("index")
        
    def on_cmd_italic(self, widget = None, data = None):
        self.insert_formatting("//", "//")
        
    def on_cmd_insert_page(self, widget = None, data = None):
        dlg = interface.InsertPageTextDialog(self)
        page = dlg.run()
        if page:
            pkey = self.page_name(page)
            pair = self.db.get_pair(pkey)
            if pair:
                self.insert_text_cursor(pair[1])

    def on_cmd_underline(self, widget = None, data = None):
        self.insert_formatting("_", "_")
        
    def on_cmd_link(self, widget = None, data = None):
        self.insert_formatting("[[", "]]")

    def on_cmd_back(self, widget = None, data = None):
        if len(self.backl) > 0:
            self.reset_timers()
            page = self.backl.pop()
            self.forwardl.append(self.curpage)
            self.change_page(page)
            self.mark_page_on_calendar()
        self._update_back_forward()

    def on_cmd_forward(self, widget = None, data = None):
        if len(self.forwardl) > 0:
            self.reset_timers()
            page = self.forwardl.pop()
            if self.curpage != None:
                self.backl.append(self.curpage)
            self.change_page(page)
            self.mark_page_on_calendar()
        self._update_back_forward()
        
    def on_cmd_paste(self, widget = None, data = None):
        self.txBuffer.paste_clipboard(self.clipboard, None,
            self.txNote.get_editable())
        
    def on_cmd_preferences(self, widget = None, data = None):
        wnd = interface.PreferencesDialog(self)
        wnd.show()
        
    def on_cmd_redo(self, widget = None, data = None):
        if len(self.redol) > 0:
            ls = self.redol.pop()
            self.enqueue_undo()
            self.hl_change_page(ls[0])
            self.set_text(ls[1])
        self.format_text()

    def on_cmd_rename_page(self, widget = None, data = None):
        dlg = interface.RenamePageDialog(self)
        newpage = dlg.run()
        if newpage != None:
            cpagename = self.page_name(self.curpage)
            self.db.set_key(self.page_name(newpage), self.get_text())
            self.hl_change_page(newpage)
            if dlg.create_redirect:
                self.db.set_key(cpagename, "Renamed to [[" + newpage + "]]\n")
            else:
                self.db.del_key(cpagename)

    def on_cmd_search_menu(self, widget = None, event = None):
        self.mnSearchOptions.popup(None, None, None, 0, 0)

    def on_cmd_find_and_replace(self, widget = None, event = None):
        pass

    def on_cmd_today(self, widget = None, data = None):
        dt = datetime.datetime.today()
        self.hl_change_page("%04d-%02d-%02d" % (dt.year, dt.month, dt.day))
        
    def on_cmd_tomorrow(self, widget = None, data = None):
        dt = datetime.datetime.today() + datetime.timedelta(1)
        self.hl_change_page("%04d-%02d-%02d" % (dt.year, dt.month, dt.day))
        
    def on_cmd_undo(self, widget = None, data = None):
        if len(self.undol) > 0:
            ls = self.undol.pop()
            self.enqueue_redo()
            self.hl_change_page(ls[0])
            self.set_text(ls[1])
        self.format_text()

    def on_cmd_yesterday(self, widget = None, data = None):
        dt = datetime.datetime.today() - datetime.timedelta(1)
        self.hl_change_page("%04d-%02d-%02d" % (dt.year, dt.month, dt.day))

    def _on_link(self, tag, widget, event, iter):
        if tag == None:
            return False
        if event.type == gtk.gdk.BUTTON_PRESS:
            if event.button != 1:
                return False    # Not the left button.
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
                utils.open_browser(link)
            else:
                self.change_page_link(link)
            return True
        return False
        
    def _on_text_change(self, widget = None, data = None):
        # Add an undo-point if the text was changed 32 times.
        self.last_undo_cnt += 1
        if self.last_undo_cnt >= 32:
            self.enqueue_undo()
        self.reset_timers()
        self.set_timers()
        if self.curpage:
            self.set_status(u'Page "' + self.curpage + u'" changed')

    def _on_text_delete(self, widget = None, s = None, e = None, dt = None):
        # big amount of text being deleted? Prepare for undo!
        if abs(s.get_offset() - e.get_offset()) > 32:
            self.enqueue_undo()
        
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

    def set_status(self, text):
        if self._status_bar_ctx == None:
            self._status_bar_ctx = self.txStatus.get_context_id("skedmain")
        else:
            self.txStatus.pop(self._status_bar_ctx)
        self.txStatus.push(self._status_bar_ctx, text)

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
        if len(self.backl) > self.max_history:
            self.backl = self.backl[-self.max_history:]
        if len(self.forwardl) > self.max_history:
            self.forwardl = self.forwardl[-self.max_history:]
        b = len(self.backl) > 0
        f = len(self.forwardl) > 0
        self.btForward.set_sensitive(f)
        self.btBack.set_sensitive(b)
        self.mnForward.set_sensitive(f)
        self.mnBack.set_sensitive(b)
    
    def _update_undo_redo(self):
        u = len(self.undol) > 0
        r = len(self.redol) > 0
        self.btUndo.set_sensitive(u)
        self.btRedo.set_sensitive(r)
        self.mnUndo.set_sensitive(u)
        self.mnRedo.set_sensitive(r)

    def enqueue_undo(self):
        self.last_undo_cnt = 0
        ls = [ self.curpage, self.get_text() ]
        if len(self.undol) > 0:
            ols = self.undol[-1]
            if ols[0] != ls[0] or ols[1] != ls[1]:
                self.undol.append(ls)
        else:
            self.undol.append(ls)
        if len(self.undol) > self.undo_levels:
            self.undol = self.undol[-self.undo_levels:]
        self._update_undo_redo()
        
    def enqueue_redo(self):
        ls = [ self.curpage, self.get_text() ]
        if len(self.redol) > 0:
            ols = self.redol[-1]
            if ols[0] != ls[0] or ols[1] != ls[1]:
                self.redol.append(ls)
        else:
            self.redol.append(ls)
        if len(self.redol) > self.undo_levels:
            self.redol = self.redol[-self.undo_levels:]
        self._update_undo_redo()

    def get_text(self):
        start, end = self.txBuffer.get_bounds()
        return self.txBuffer.get_text(start, end).decode("utf-8")

    def set_text(self, text):
        self.txBuffer.handler_block(self.text_change_sigid)
        self.txBuffer.handler_block(self.text_delete_sigid)
        self.txBuffer.set_text(text)
        self.txBuffer.handler_unblock(self.text_change_sigid)
        self.txBuffer.handler_unblock(self.text_delete_sigid)

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
        self.format_text()
    
    def insert_text_cursor(self, text):
        imark = self.txBuffer.get_insert()
        iiter = self.txBuffer.get_iter_at_mark(imark)
        self.txBuffer.insert(iiter, text)

    def set_text_tags(self):
        tagdata = [
            # Note: Later tags have higher priority.
            ['std', {
                'font' : self.opt.get_str("std_font"),
                'foreground' : self.opt.get_str("std_color")
            }],
            ['underline', {
                'underline' : pango.UNDERLINE_SINGLE
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

        bold_re = ur"\W(\*+)([^*\n\r]+?)(\*+)\W"    # *bold*
        for match in re.finditer(bold_re, tx):
            self._apply_tag_on_group(match, "format", 1)
            self._apply_tag_on_group(match, "bold", 2)
            self._apply_tag_on_group(match, "format", 3)
        
        italic_re = ur"\W(//+)([^/\n\r]+?)(//+)\W"  # //italic//
        for match in re.finditer(italic_re, tx):
            self._apply_tag_on_group(match, "format", 1)
            self._apply_tag_on_group(match, "italic", 2)
            self._apply_tag_on_group(match, "format", 3)
        
        underl_re = ur"\W(_+)([^_\n\r]+?)(_+)\W"    # _underline_
        for match in re.finditer(underl_re, tx):
            self._apply_tag_on_group(match, "format", 1)
            self._apply_tag_on_group(match, "underline", 2)
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

        url_re = ur"(([a-zA-Z]+://|www\.)[^\s<>\"']+[^\s>\"'\).,;?!]+)" # url
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
        if self.spell:
            self.spell.recheck_all()

    def _apply_tag_on_group(self, match, tag, group):
        start = self.txBuffer.get_iter_at_offset(match.start(group))
        end = self.txBuffer.get_iter_at_offset(match.end(group))
        self.txBuffer.apply_tag_by_name(tag, start, end)

    def get_date_str(self):
        year, month, day = self.calendar.get_date()
        return "%04d-%02d-%02d" % (year, month + 1, day)

    def hl_change_page(self, page):
        # Higher level page changer. Handles calendar, back/fwd buttons, etc.
        self.reset_timers()
        if page == "":
            page = "index"
        if self.curpage != None and self.curpage.upper() != page.upper():
            self.backl.append(self.curpage)
        self.forwardl = []
        self.change_page(page)
        self._update_back_forward()
        self.mark_page_on_calendar()

    def change_page(self, page):
        self.reset_timers()
        self.save_current_page()
        page = self.normalize_date_page_name(page)
        pair = self.db.get_pair(self.page_name(page), None)
        if pair:
            page = pair[0][4:]  # pag_pageName
            text = pair[1]
        else:
            text = ""
        self.history.add(page)
        self.curpage = page
        self.txPageName.set_text(self.curpage)
        self.set_text(text)
        self.format_text()
        self.set_status(page)
        
    def save_current_page(self):
        if self.curpage != None:
            #self.enqueue_undo()  ## Buggy ##
            tx = self.get_text()
            if tx != u"":
                self.db.set_key(self.page_name(self.curpage), tx)
            else:
                self.db.del_key(self.page_name(self.curpage))
            self.set_status(u'Page "' + self.curpage + u'" saved')

    def reload_current_page(self):
        """ Reloads current page from DB.  Changes will be discarted. """
        page = self.normalize_date_page_name(self.curpage)
        pair = self.db.get_pair(self.page_name(page), None)
        if pair:
            page = pair[0][4:]  # pag_pageName
            text = pair[1]
            self.curpage = page
            self.txPageName.set_text(self.curpage)
            self.set_text(text)
            self.format_text()

    def change_page_link(self, page):
        self.reset_timers()
        page = self.normalize_date_page_name(page)
        if self.curpage != None and not self.has_page(page):
            self.db.set_key(self.page_name(page), \
                "[[" + self.curpage + "]]\n===" + page + "===\n")
        self.hl_change_page(page)
    
    def normalize_date_page_name(self, page):
        match = re.search("([0-9]{1,2})/([0-9]{1,2})/([0-9]{1,4})", page)
        if match != None:
            d = int(match.group(1))
            m = int(match.group(2))
            y = int(match.group(3))
            return u"%04d-%02d-%02d" % (y, m, d)
        match = re.search("([0-9]{1,4})-([0-9]{1,2})-([0-9]{1,2})", page)
        if match != None:
            y = int(match.group(1))
            m = int(match.group(2))
            d = int(match.group(3))
            return u"%04d-%02d-%02d" % (y, m, d)
        return page

    def has_page(self, page):
        return self.db.has_key(self.page_name(page))
        
    def page_name(self, page):
        # Gets an utf-8 encoded string-or-unicode-string and return a the page
        # name as an utf-8 encoded prefixed string. Sounds confuse for you? :)
        if not isinstance(page, unicode):
            page = page.decode("utf-8")
        return "pag_" + self.normalize_date_page_name(page)
        
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
                    # Throws an ValueError for bad dates.
                    datetime.datetime(y, m, d)
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


def main():
    # Connect to the database.
    db = database.EncryptedDatabase()
    if not db.get_lock():
        interface.error_dialog(None, "Sked failed to get exclusive "
            + "access to its database. It usually happens when there "
            + "is another instance running or it could not create "
            + "files in your HOME directory. If the previous instance "
            + "was closed in some unusual way (eg. by a power failure), "
            + "you must delete the file " + db.lock_path
            + " before proceeding.")
        return

    jump_to_page = None
    if db.is_new():
        dlg = interface.NewPasswordDialog()
        dlg.set_title("Sked - New database")
        dlg.set_text("You are using this program for the first time. "
            "Please enter a password to lock the database or leave it "
            "blank if you do not want to password protect your database. "
            "It is possible to change this later")
        pwd = dlg.run()
        if pwd != None:
            db.create(pwd)
            try:
                xmlio.import_xml_file(db, utils.data_path("help.xml"))
                jump_to_page = "index"
            except:
                pass
        else:
            db.release_lock()
            return
    else:
        pwd = u""
        firstime = True
        while not db.try_open(pwd):
            if not firstime:
                interface.error_dialog(None, \
                    "Wrong password. Please try again.")
            dlg = interface.PasswordDialog()
            firstime = False
            dlg.set_title("Sked - Password required")
            dlg.set_text("The database is locked. Please enter the password.")
            pwd = dlg.run()
            if pwd == None:
                db.release_lock()
                return

    if db.is_ready():
        try:
            app = SkedApp(db)
            app.start(jump_to_page)
            gtk.main()
        except Exception, e:
            print(e)
        finally:
            db.close()
    else:
        interface.error_dialog(None, u"Can't open the database. Namárië.")
        db.release_lock()
        return

