# -*- coding: utf-8 -*-

# Sked - a wikish scheduler with Python, PyGTK and Berkeley DB
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
User interface module.
"""

__CVSID__ = "$Id$"

import pygtk            # GTK+ stuff
pygtk.require('2.0')
import gtk
from gtk import glade
from gtk import gdk
import gobject
import pango


import utils


class BaseDialog(object):
    GLADE_FILE_NAME = 'sked.glade'
    
    def glade_init(self, root = None):
        fname = utils.search_share_path(BaseDialog.GLADE_FILE_NAME)
        self.glade = gtk.glade.XML(fname, root)
        return self.glade


class AboutDialog(BaseDialog):
    _dlg = None

    def __init__(self, parent):
        self.parent = parent
        self._load_interface()
        
    def show(self):
        if AboutDialog._dlg != None:
            AboutDialog._dlg.present()
        else:
            AboutDialog._dlg = self.dlg
            self.dlg.set_modal(True)
            self.dlg.show()

    def _load_interface(self):
        self.glade_init("dlgAbout")
        self.dlg = self.glade.get_widget("dlgAbout")



class PreferencesDialog(BaseDialog):
    _dlg = None

    def __init__(self, parent):
        self.parent = parent
        self.opt = parent.opt
        self._load_interface()
        self._set_widget_values()
        
    def show(self):
        if PreferencesDialog._dlg != None:
            PreferencesDialog._dlg.present()
        else:
            PreferencesDialog._dlg = self.dlg
            self.dlg.show()

    def _load_interface(self):
        self.glade_init("dlgPreferences")

        self.dlg = self.glade.get_widget("dlgPreferences")
        self.spFormatTime = self.glade.get_widget("spFormatTime")
        self.spSaveTime = self.glade.get_widget("spSaveTime")
        self.spUndoLevels = self.glade.get_widget("spUndoLevels")
        self.spHistorySize = self.glade.get_widget("spHistorySize")
        self.cbShowEdit = self.glade.get_widget("cbShowEdit")
        self.cbShowCalendar = self.glade.get_widget("cbShowCalendar")
        self.cbShowHistory = self.glade.get_widget("cbShowHistory")
        self.cbShowGlobalSearch = self.glade.get_widget("cbShowGlobalSearch")
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
        self.dlg.destroy()
        PreferencesDialog._dlg = None
        self.parent.update_options()
        
    def _on_cmd_cancel(self, widget = None, data = None):
        self.dlg.destroy()
        PreferencesDialog._dlg = None
        return False

    def _set_widget_values(self):
        self.spFormatTime.set_value(self.opt.get_int("format_time"))
        self.spSaveTime.set_value(self.opt.get_int("save_time"))
        self.spUndoLevels.set_value(self.opt.get_int("undo_levels"))
        self.spHistorySize.set_value(self.opt.get_int("max_history"))
        self.cbShowEdit.set_active(self.opt.get_bool("show_edit_buttons"))
        self.cbShowCalendar.set_active(self.opt.get_bool("show_calendar"))
        self.cbShowHistory.set_active(self.opt.get_bool("show_history"))
        self.cbShowGlobalSearch.set_active(self.opt.get_bool("show_gsearch"))

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
        self.opt.set_int("max_history", self.spHistorySize.get_value_as_int())
        self.opt.set_bool("show_edit_buttons", self.cbShowEdit.get_active())
        self.opt.set_bool("show_calendar", self.cbShowCalendar.get_active())
        self.opt.set_bool("show_history", self.cbShowHistory.get_active())
        self.opt.set_bool("show_gsearch", self.cbShowGlobalSearch.get_active())

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


