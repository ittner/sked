# -*- coding: utf-8 -*-
#
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
#

"""
XML data importer/exporter for Sked.
"""

from xml import sax
from xml.sax import saxutils
from xml.sax.handler import ContentHandler, EntityResolver

from pages import *
from history import HistoryManager
import utils

class VersionError(Exception):
    pass

class DataFormatError(Exception):
    pass
    
class PrematureDocumentEndError(Exception):
    pass

class SkedContentHandler(ContentHandler):
    """ The main workhorse for data parsing and manipulation.
    'db' is a Sked database. 'page_manager' is an instance of PageManager
    using 'db' as its backend or None (implies in import_pages=False).
    'option_manager' is an instance of OptionManager using 'db' as its
    backend or None (implies in import_config=False). The properties
    'import_pages', 'import_config', and 'import_history' controls whether
    each kind of data will be imported and saved to the database.
    """

    READY = 0
    WAITING_SKEDDATA = 1
    IN_SKEDDATA = 2
    IN_CONFIG = 3
    IN_CONFIG_OPTION = 4
    IN_HISTORY = 5
    IN_HISTORY_ITEM = 6
    IN_ENTRY = 7
    DONE = 9

    import_pages = True
    import_config = True
    import_history = True

    def __init__(self, db, page_manager = None, option_manager = None):
        self._db = db
        self._pm = page_manager
        self._opt = option_manager
        if self._pm == None: self.import_pages = False
        if self._opt == None: self.import_config = False
        self._state = SkedContentHandler.READY

    def startDocument(self):
        self._state = SkedContentHandler.WAITING_SKEDDATA

    def endDocument(self):
        if self._state != SkedContentHandler.DONE:
            raise PrematureDocumentEndError

    def startElement(self, name, attrs):
        if self._state == SkedContentHandler.WAITING_SKEDDATA \
        and name == "skeddata":
            ver = attrs.get("version")
            if ver != "1.0" and ver != "1.1":
                raise VersionError
            self._state = SkedContentHandler.IN_SKEDDATA

        elif self._state == SkedContentHandler.IN_SKEDDATA \
        and name == "configuration":
            self._state = SkedContentHandler.IN_CONFIG
        elif self._state == SkedContentHandler.IN_SKEDDATA \
        and name == "history":
            self._tmp_name = attrs.get("name")
            if len(self._tmp_name) < 1:
                raise DataFormatError("Empty history name")
            self._tmp_hist_items = []
            self._state = SkedContentHandler.IN_HISTORY
        elif self._state == SkedContentHandler.IN_SKEDDATA \
        and name == "entry":
            self._tmp_name = attrs.get("name")
            if len(self._tmp_name) < 1:
                raise DataFormatError("Empty page name")
            self._tmp_data = ""
            self._state = SkedContentHandler.IN_ENTRY

        elif self._state == SkedContentHandler.IN_CONFIG \
        and name == "option":
            self._tmp_name = attrs.get("name")
            if len(self._tmp_name) < 1:
                raise DataFormatError("Empty option name")
            self._tmp_data = ""
            self._state = SkedContentHandler.IN_CONFIG_OPTION

        elif self._state == SkedContentHandler.IN_HISTORY and name == "item":
            self._tmp_data = ""
            self._state = SkedContentHandler.IN_HISTORY_ITEM

        else:
            raise DataFormatError("Unknow tag: " + name)

    def endElement(self, name):
        if self._state == SkedContentHandler.IN_CONFIG_OPTION \
        and name == "option":
            if self.import_config:
                self._opt.set_str(self._tmp_name, self._tmp_data)
            self._tmp_name = None
            self._tmp_data = None
            self._state = SkedContentHandler.IN_CONFIG
        elif self._state == SkedContentHandler.IN_CONFIG \
        and name == "configuration":
            if self.import_config:
                self._opt.save()
            self._state = SkedContentHandler.IN_SKEDDATA

        elif self._state == SkedContentHandler.IN_HISTORY_ITEM \
        and name == "item":
            self._tmp_hist_items.append(self._tmp_data)
            self._tmp_data = None
            self._state = SkedContentHandler.IN_HISTORY
        elif self._state == SkedContentHandler.IN_HISTORY \
        and name == "history":
            if self.import_history:
                hist = HistoryManager(self._db, self._tmp_name.encode("utf-8"))
                hist.set_items(self._tmp_hist_items)
                hist.save()
            self._tmp_name = None
            self._tmp_hist_items = None
            self._state = SkedContentHandler.IN_SKEDDATA
        elif self._state == SkedContentHandler.IN_ENTRY \
        and name == "entry":
            if self.import_pages:
                self._pm.save(Page(self._tmp_name, self._tmp_data), False)
            self._tmp_name = None
            self._tmp_data = None
            self._state = SkedContentHandler.IN_SKEDDATA
        elif self._state == SkedContentHandler.IN_SKEDDATA \
        and name == "skeddata":
            self._state = SkedContentHandler.DONE
        else:
            raise DataFormatError

    def characters(self, data):
        if self._state == SkedContentHandler.IN_CONFIG_OPTION \
        or self._state == SkedContentHandler.IN_HISTORY_ITEM \
        or self._state == SkedContentHandler.IN_ENTRY:
            self._tmp_data = self._tmp_data + data



class SkedEntityResolver(EntityResolver):
    def resolveEntity(self, publicId, systemId):
        if systemId == "sked.dtd":
            return utils.data_path(systemId)
        return None

def import_xml_file(fname, db, page_manager, option_manager, import_history):
    """ Import XML data from a file named 'fname' into the database. 'db' is
    a Sked database. 'page_manager' is an instance of PageManager using 'db'
    as its backend or None (implies in not importing pages from the file).
    'option_manager' is an instance of OptionManager using 'db' as its
    backend or None (implies in not importing the configuration from the file).
    'import_history' is a boolean which controls the importing of any history
    entries existing in the file.
    """
    ch = SkedContentHandler(db, page_manager, option_manager)
    ch.import_history = import_history
    parser = sax.make_parser()
    parser.setContentHandler(ch)
    parser.setEntityResolver(SkedEntityResolver())
    fp = open(fname, "rb")
    parser.parse(fp)
    fp.close()

def export_xml_file(fname, page_manager, option_manager, histories):
    """ Exports Sked data to the XML file 'fname'. 'option_manager' is an
    instance OptionManager or None (implies in not exporting options).
    'histories' is a list of instances of HistoryManager or None (implies in
    not exporting history). 'page_manager' is an instance of PageManager or
    None (implies in not exporting pages). If both 'options' and 'histories'
    are None, the file will be written with version="1.0", otherwise with
    version="1.1".
    """

    fp = open(fname, "w")
    fp.write('<?xml version="1.0" encoding="utf-8"?>\n'
        '<!DOCTYPE skeddata SYSTEM "sked.dtd">\n')
    if option_manager == None and histories == None:
        fp.write('<skeddata version="1.0">\n')
    else:
        fp.write('<skeddata version="1.1">\n')
    if option_manager != None:
        fp.write(' <configuration>\n')
        for name, value in option_manager.iterate():
            fp.write("  <option name=%s>%s</option>\n" % (
                saxutils.quoteattr(name).encode("utf-8"),
                saxutils.escape(value).encode("utf-8")))
        fp.write(' </configuration>\n')
    if histories != None:
        for hist in histories:
            fp.write(" <history name=%s>\n" % (
                saxutils.quoteattr(hist.name).encode("utf-8")))
            for item in hist.get_items():
                fp.write("  <item>%s</item>\n" % (
                    saxutils.escape(item).encode("utf-8")))
            fp.write(" </history>\n")
    if page_manager != None:
        for page in page_manager.iterate():
            fp.write(" <entry name=%s>%s</entry>\n" % (
                saxutils.quoteattr(page.name).encode("utf-8"),
                saxutils.escape(page.text).encode("utf-8")))
    fp.write("</skeddata>\n")
    fp.close()
