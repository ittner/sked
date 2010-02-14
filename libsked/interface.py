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
User interface module.
"""


import pygtk            # GTK+ stuff
pygtk.require('2.0')
import gtk
from gtk import glade
from gtk import gdk
import gobject
import pango
import re

from history import HistoryManager
import utils
import os.path


class BaseDialog(object):
    GLADE_FILE_NAME = 'sked.glade'
    
    def glade_init(self, root = None):
        fname = utils.data_path(BaseDialog.GLADE_FILE_NAME)
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


class BasePasswordDialog(BaseDialog):
    """ Commom base for password-related dialog boxes. """

    def _load_interface(self):
        self.glade_init("dlgPassword")
        self.dlg = self.glade.get_widget("dlgPassword")
        self.lbGeneral = self.glade.get_widget("lbGeneral")
        self.lbPassword = self.glade.get_widget("lbPassword")
        self.lbNewPassword = self.glade.get_widget("lbNewPassword")
        self.lbConfirmPassword = self.glade.get_widget("lbConfirmPassword")
        self.lbPasswordQuality = self.glade.get_widget("lbPasswordQuality")
        self.txPassword = self.glade.get_widget("txPassword")
        self.txNewPassword = self.glade.get_widget("txNewPassword")
        self.txConfirmPassword = self.glade.get_widget("txConfirmPassword")
        self.pgPasswordQuality = self.glade.get_widget("pgPasswordQuality")
        self.txPassword.set_visibility(False)
        self.txNewPassword.set_visibility(False)
        self.txConfirmPassword.set_visibility(False)
        try:
            self.dlg.set_icon_from_file(utils.data_path("sked.png"))
        except: pass

    def set_text(self, text):
        self.lbGeneral.set_text(text)
    
    def set_title(self, title):
        self.dlg.set_title(title)



class PasswordDialog(BasePasswordDialog):
    """ Dialog to ask a password to the user. """
    
    def __init__(self, parent = None):
        self.parent = parent
        self._load_interface()
        self.password = None

    def get_password(self):
        return self.password
    
    def _load_interface(self):
        BasePasswordDialog._load_interface(self)
        self.set_text("Enter the password")
        self.lbPassword.set_property("visible", True)
        self.lbNewPassword.set_property("visible", False)
        self.lbConfirmPassword.set_property("visible", False)
        self.lbPasswordQuality.set_property("visible", False)
        self.txPassword.set_property("visible", True)
        self.txNewPassword.set_property("visible", False)
        self.txConfirmPassword.set_property("visible", False)
        self.pgPasswordQuality.set_property("visible", False)
        
    def run(self):
        val = self.dlg.run()
        if val == gtk.RESPONSE_OK:
            self.password = self.txPassword.get_text().decode("utf-8")
            self.dlg.destroy()
            return self.password
        elif val == gtk.RESPONSE_CANCEL:
            self.password = None
            self.dlg.destroy()
            return None


class BasePasswordChangeDialog(BasePasswordDialog):
    """ Common base for NewPasswordDialog and ChangePasswordDialog. """
    
    def __init__(self, parent = None):
        self.parent = parent
        self._load_interface()
        self.newpassword = None

    def get_new_password(self):
        return self.newpassword
    
    def _load_interface(self):
        BasePasswordDialog._load_interface(self)
        self.set_text("Enter a password")
        self.lbNewPassword.set_property("visible", True)
        self.lbConfirmPassword.set_property("visible", True)
        self.lbPasswordQuality.set_property("visible", True)
        self.txNewPassword.set_property("visible", True)
        self.txConfirmPassword.set_property("visible", True)
        self.pgPasswordQuality.set_property("visible", True)
        self.glade.signal_autoconnect({
            'on_pwd_change' : self._update_meter
        })

    def _check_match(self):
        new = self.txNewPassword.get_text().decode("utf-8")
        conf = self.txConfirmPassword.get_text().decode("utf-8")
        if new == None or conf == None:
            return None
        elif new != conf:
            error_dialog(self.dlg, u"The passwords does not match.")
            return None
        else:
            return new

    def _update_meter(self, widget = None, data = None):
        # The quality meter reaches the maximum for passwords mixing letters,
        # numbers and special symbols with, at least, 10 chars.
        qfact = 0.0
        qtext = "Bad"
        pwd = self.txNewPassword.get_text().decode("utf-8")
        plen = len(pwd)
        if plen > 0:
            singlecase = pwd.upper() == pwd or pwd.lower() == pwd
            if re.search("^[0-9]+$", pwd):
                # Only numbers. The worst.
                qfact = 15.0
            elif re.search("^[a-z]+$", pwd, re.IGNORECASE):
                # Only letters.
                if singlecase:
                    qfact = 30.0
                else:
                    qfact = 50.0
            elif re.search("^[a-z0-9]+$", pwd, re.IGNORECASE):
                # Numbers and letters. Just bad.
                if singlecase:
                    qfact = 45.0
                else:
                    qfact = 70.0
            else:
                # Numbers, letters and others. Good.
                if singlecase:
                    qfact = 80.0
                else:
                    qfact = 100.0
            qfact = qfact * min(10.0, plen) / 10.0
        if qfact < 50:
            qtext = "Bad"
        elif qfact < 75:
            qtext = "Medium"
        else:
            qtext = "Good"
        self.pgPasswordQuality.set_text(qtext)
        self.pgPasswordQuality.set_fraction(qfact/100.0)


class NewPasswordDialog(BasePasswordChangeDialog):
    
    def _load_interface(self):
        BasePasswordChangeDialog._load_interface(self)
        self.lbPassword.set_property("visible", False)
        self.txPassword.set_property("visible", False)
        
    def run(self):
        while True:
            val = self.dlg.run()
            if val == gtk.RESPONSE_OK:
                pwd = self._check_match()
                if pwd != None:
                    self.newpassword = pwd
                    self.dlg.destroy()
                    return pwd
            elif val == gtk.RESPONSE_CANCEL:
                self.newpassword = None
                self.dlg.destroy()
                return None


class PasswordChangeDialog(BasePasswordChangeDialog):
    
    def __init__(self, parent, check_callback):
        BasePasswordChangeDialog.__init__(self, parent)
        self.password = None
        self.check_callback = check_callback

    def get_password(self):
        return self.password

    def _load_interface(self):
        BasePasswordChangeDialog._load_interface(self)
        self.lbPassword.set_property("visible", True)
        self.txPassword.set_property("visible", True)

    def run(self):
        while True:
            val = self.dlg.run()
            if val == gtk.RESPONSE_OK:
                newpwd = self._check_match()
                if newpwd != None:
                    pwd = self.txPassword.get_text().decode("utf-8")
                    if self.check_callback(pwd):
                        self.password = pwd
                        self.newpassword = newpwd
                        self.dlg.destroy()
                        return newpwd
                    else:
                        error_dialog(self.dlg, \
                            u"Wrong password. Please try again.")
            elif val == gtk.RESPONSE_CANCEL:
                self.password = None
                self.newpassword = None
                self.dlg.destroy()
                return False


class InsertPageTextDialog(BaseDialog):
    
    def __init__(self, skapp):
        self.app = skapp
        self.parent = skapp.window
        self.history = HistoryManager(self.app, u"insert_history", True)
        self.hmodel = gtk.ListStore(gobject.TYPE_STRING)
        self._load_interface()

    def _load_interface(self):
        self.glade_init("dlgInsertPageText")
        self.dlg = self.glade.get_widget("dlgInsertPageText")
        self.cbePageName = self.glade.get_widget("cbePageName")
        self.txPageName = self.cbePageName.child
        self.cbePageName.set_model(self.hmodel)
        self.cbePageName.set_text_column(0)

    def run(self):
        self.hmodel.clear()
        for item in self.history.get_items():
            self.hmodel.append([item])
        while True:
            val = self.dlg.run()
            if val == gtk.RESPONSE_OK:
                page = self.txPageName.get_text().decode("utf-8")
                if self.app.has_page(page):
                    self.dlg.destroy()
                    self.history.add(page)
                    self.history.save()
                    return page
                else:
                    error_dialog(self.dlg, u"Page not found.")
            elif val == gtk.RESPONSE_CANCEL:
                self.dlg.destroy()
                self.history.save()
                return None
        return None


class RenamePageDialog(BaseDialog):
    
    def __init__(self, skapp):
        self.app = skapp
        self.parent = skapp.window
        self.curpage = self.app.curpage
        self.history = HistoryManager(self.app, u"rename_history", True)
        self.hmodel = gtk.ListStore(gobject.TYPE_STRING)
        self._load_interface()
        self.page_name = None
        self.create_redirect = False

    def _load_interface(self):
        self.glade_init("dlgRenamePage")
        self.dlg = self.glade.get_widget("dlgRenamePage")
        self.lbCurrentName = self.glade.get_widget("lbCurrentName")
        self.cbCreateRedirect = self.glade.get_widget("cbCreateRedirect")
        self.cbeNewName = self.glade.get_widget("cbeNewName")
        self.txNewName = self.cbeNewName.child
        self.cbeNewName.set_model(self.hmodel)
        self.cbeNewName.set_text_column(0)

    def run(self):
        self.hmodel.clear()
        for item in self.history.get_items():
            self.hmodel.append([item])
        self.lbCurrentName.set_text(self.curpage)
        self.txNewName.set_text(self.curpage)
        while True:
            val = self.dlg.run()
            if val == gtk.RESPONSE_OK:
                page = self.txNewName.get_text().decode("utf-8")
                pname = self.app.page_name(page).upper()
                cname = self.app.page_name(self.curpage).upper()
                if (not self.app.has_page(page)) or cname == pname:
                    self.dlg.destroy()
                    self.history.add(page)
                    self.history.save()
                    self.page_name = page
                    self.create_redirect = self.cbCreateRedirect.get_active()
                    return page
                else:
                    error_dialog(self.dlg, u"Page already exists.")
            elif val == gtk.RESPONSE_CANCEL:
                self.dlg.destroy()
                self.history.save()
                return None
        return None
        
    def get_page_name(self):
        return self.page_name
        
    def get_create_redirect(self):
        return create_redirect


def confirm_yes_no(parent_window, msg):
    """A simple Yes/No message box.
    """
    dlg = gtk.MessageDialog(parent_window,
        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
        gtk.MESSAGE_QUESTION, gtk.BUTTONS_YES_NO, msg)
    ret = dlg.run()
    dlg.destroy()
    return ret == gtk.RESPONSE_YES


def confirm_file_overwrite(parent_window, fpath):
    """A simple "Do you want to overwrite" message box.
    """
    fdir, fname = os.path.split(fpath)
    return confirm_yes_no(parent_window, u"The file " + fname + \
        u" already exists. Do you want to replace it?")


def error_dialog(parent_window, msg):
    """A simple error dialog box.
    """
    dlg = gtk.MessageDialog(parent_window,
        gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT,
        gtk.MESSAGE_ERROR, gtk.BUTTONS_OK, msg)
    dlg.run()
    dlg.destroy()
