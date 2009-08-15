# -*- coding: utf-8 -*-
#
# Sked - a wikish scheduler with Python and PyGTK
# (c) 2006-09 Alexandre Erwin Ittner <alexandre@ittner.com.br>
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
$Id$
"""

from xml import sax
from xml.sax import saxutils
from xml.sax.handler import ContentHandler, EntityResolver

import utils

class VersionError(Exception):
    pass

class DataFormatError(Exception):
    pass
    
class PrematureDocumentEndError(Exception):
    pass

class SkedContentHandler(ContentHandler):
    READY = 0
    WAITING_SKEDDATA = 1
    WAITING_ENTRY = 2
    WAITING_DATA = 3
    DONE = 4

    def __init__(self, db, callback = None):
        self._db = db
        self._state = SkedContentHandler.READY
        self._callback = callback
        
    def startDocument(self):
        self._state = SkedContentHandler.WAITING_SKEDDATA
        
    def endDocument(self):
        if self._state == SkedContentHandler.DONE:
            return
        else:
            raise PrematureDocumentEndError

    def startElement(self, name, attrs):
        if self._state == SkedContentHandler.WAITING_SKEDDATA \
        and name == "skeddata":
            ver = attrs.get("version")
            if ver != "1.0":
                raise VersionError
            self._state = SkedContentHandler.WAITING_ENTRY
        elif self._state == SkedContentHandler.WAITING_ENTRY \
        and name == "entry":
            self._pagename = attrs.get("name")
            self._pagedata = ""
            self._state = SkedContentHandler.WAITING_DATA
        else:
            raise DataFormatError

    def endElement(self, name):
        if self._state == SkedContentHandler.WAITING_DATA \
        and name == "entry":
            self._db.set_key("pag_" + self._pagename, self._pagedata, False)
            self._state = SkedContentHandler.WAITING_ENTRY
            if self._callback:
                SkedContentHandler._callback()
        elif self._state == SkedContentHandler.WAITING_ENTRY \
        and name == "skeddata":
            self._state = SkedContentHandler.DONE
        else:
            raise DataFormatError

    def characters(self, data):
        if self._state == SkedContentHandler.WAITING_DATA:
            self._pagedata = self._pagedata + data

    def get_state(self):
        return self._state


class SkedEntityResolver(EntityResolver):
    def resolveEntity(self, publicId, systemId):
        if systemId == "sked.dtd":
            return utils.data_path(systemId)
        return None


def import_xml_data(db, fp, callback = None):
    """ Import XML data from a stream 'fp' into the database 'db'. 'callback'
    will be called for each entry imported. """

    parser = sax.make_parser()
    parser.setContentHandler(SkedContentHandler(db, callback))
    parser.setEntityResolver(SkedEntityResolver())
    parser.parse(fp)


def import_xml_file(db, fname, callback = None):
    """ Import XML data from a file 'fname' into the database 'db'. 'callback'
    will be called for each entry imported. """
    
    fp = open(fname, "rb")
    import_xml_data(db, fp, callback)
    fp.close()


class XMLExporter(object):
    """Exports Sked databases as XML data to streams. By now, only text entries
    are supported."""
    
    def __init__(self, db, fp):
        """Creates a new data exporter. 'db' is a Sked database and 'fp' is 
        some file handler."""
        
        self._db = db
        self._fp = fp

    def write_all(self, prefix, callback = None):
        """Writes all entries begining with 'prefix' to the output. 'callback'
        is called for each written entry with no arguments. """
        
        self._fp.write('<?xml version="1.0" encoding="utf-8"?>\n' \
                       '<!DOCTYPE skeddata SYSTEM "sked.dtd">\n'  \
                       '<skeddata version="1.0">\n')
        
        plen = len(prefix)
        for tmp in self._db.pairs():
            if tmp[0].startswith(prefix):
                name = tmp[0][plen:]
                self._fp.write(" <entry name=%s>%s</entry>\n" % (\
                    saxutils.quoteattr(name).encode("utf-8"), \
                    saxutils.escape(tmp[1]).encode("utf-8")))
                if callback != None: callback()

        self._fp.write("</skeddata>\n")


def export_xml_file(db, fname, prefix, callback = None):
    """Exports the entries begining with 'prefix' from the database 'db' to
    the file named 'fname' with no compression or encryption. For each entry
    exported, 'callback' will be called with no arguments.
    """

    fp = open(fname, "w")
    exp = XMLExporter(db, fp)
    exp.write_all(prefix, callback)
    fp.close()
