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
A Conduit module for Sked databases. EXPERIMENTAL.
"""

import conduit
import conduit.dataproviders.DataProvider as DataProvider
import conduit.Exceptions as Exceptions
from conduit.datatypes.Note import Note

from gettext import gettext as _

try:
    import libsked as sked
    import libsked.database as skdb
    import libsked.pages as skpages
    MODULES = { "SkedTwoWay" : { "type": "dataprovider" } }
except:
    # Sked is not installed.
    MODULES = { }


class SkedTwoWay(DataProvider.TwoWay):
    """ Synchronization for Sked databases.
    """
    _name_ = _("Sked Entries")
    _description_ = _("Synchronize your Sked database")
    _category_ = conduit.dataproviders.CATEGORY_NOTES
    _module_type_ = "twoway"
    _in_type_ = "note"
    _out_type_ = "note"
    _icon_ = "sked"
    _configurable_ = True

    def __init__(self, *args):
        DataProvider.TwoWay.__init__(self)
        self._status = _("Leave the path empty to use your default database")
        self._db = None
        self._pm = None
        self.update_configuration(database = "", password = "")

    def __del__(self):
        # Who forgot closing the DB?
        self._close_db()

    def config_setup(self, config):
        config.add_section("Sked database")
        database_config = config.add_item("Path", "text",
            config_name = "database")
        password_config = config.add_item("Password", "text",
            config_name = "password", password = True)

        def _test_password(button):
            config.apply_config(items = [ database_config, password_config ])
            self._open_db()
            self._close_db()

        self.status_config = config.add_item(None, "label",
            xalignment = 0.5, initial_value = self._status)
        config.add_item("Test password", "button", image="dialog-password",
            action = _test_password)
        return database_config, password_config

    def _set_status(self, status):
        self._status = status
        if self.status_config:
            self.status_config.value = status

    def _open_db(self):
        if self._db: return

        path = self.database
        if path == None or path == "":
            path = skdb.get_default_database_path()
        password = self.password or ""

        self._db = skdb.EncryptedDatabase(path)
        if self._db.is_new:
            e = "No database found"
            self._set_status(e)
            raise Exceptions.SyncronizeError(e)
        if not self._db.get_lock():
            e = "Database is locked. Is Sked open?"
            self._set_status(e)
            raise Exceptions.SyncronizeError(e)
        if not self._db.try_open(password):
            e = "Wrong password"
            self._set_status(e)
            raise Exceptions.SyncronizeError(e)
        if not self._db.is_ready:
            e = "Failed to connect to the Sked database"
            self._set_status(e)
            raise Exceptions.SyncronizeError(e)
        self._pm = skpages.PageManager(self._db)
        self._set_status("Connected to the database")

    def _close_db(self):
        self._pm = None
        if self._db != None:
            self._db.close()
            self._db.release_lock()
            self._db = None

    def _update_luids(self):
        try:
            self._open_db()
            self.data = [ n for n in self._pm.iterate_names() ]
        except:
            raise
        finally:
            self._close_db()

    def refresh(self):
        DataProvider.TwoWay.refresh(self)
        self._update_luids()
        return self.data

    def get_all(self):
        DataProvider.TwoWay.get_all(self)
        self._update_luids()
        return self.data

    def get(self, luid):
        DataProvider.TwoWay.get(self, luid)
        self._open_db()
        page = self._pm.load(luid)
        self._close_db()
        return self._note_from_page(page)

    def put(self, data, overwrite, luid=None):
        self._open_db()
        newpage = self._page_from_note(data)
        if luid and newpage.normalized_name != luid:
            luid = None     # LUID was some nonsense trash.
        # TODO: Deleted entries are recreated
        if not overwrite:
            oldpage = self._pm.load(newpage.name)
            if oldpage:
                newpage.cursor_pos = oldpage.cursor_pos
                # Sked notes have no dates, but we can use another strategy:
                # if the contents of an entry _are contained_ in another,
                # this entry is newer (and no text is lost).
                if (oldpage.name != newpage.name) or (oldpage.text != \
                    newpage.text and oldpage.text not in newpage.text):
                    raise Exceptions.SynchronizeConflictError(
                        conduit.datatypes.COMPARISON_UNKNOWN,
                        newpage, oldpage)
        self._pm.save(newpage)
        self._close_db()
        return conduit.datatypes.Rid(newpage.normalized_name)

    def delete(self, luid):
        DataProvider.TwoWay.delete(self, luid)
        self._open_db()
        self._pm.delete(luid)
        self._close_db()
            
    def is_configured(self, isSource, isTwoWay):
        return True     # Buggy

    def get_UID(self):
        return "sked " + (self.database or "default")

    def _note_from_page(self, page):
        note = Note(unicode(page.name), unicode(page.text))
        note.set_UID(unicode(page.normalized_name))
        return note

    def _page_from_note(self, note):
        return skpages.Page(unicode(note.title), unicode(note.contents))
