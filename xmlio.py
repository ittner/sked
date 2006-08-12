# -*- coding: utf-8 -*-
#
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
#

"""
XML data importer/exporter for Sked.
$Id$
"""

from xml.sax.handler import ContentHandler
from xml.sax import saxutils


class VersionError(Exception):
    pass

class DataFormatError(Exception):
    pass
    
class PrematureDocumentEndError(Exception):
    pass

class SkedDocumentHandler(ContentHandler):
    READY = 0
    WAITING_SKEDDATA = 1
    WAITING_ENTRY = 2
    WAITING_TEXT = 3
    DONE = 4

    def __init__(self, fd, db):
        self._fd = fd
        self._db = db
        self._state = SkedDocumentHandler.READY
        
    def startDocument(self):
        self._state = SkedDocumentHandler.WAITING_SKEDDATA
        
    def endDocument(self):
        if self._state == SkedDocumentHandler.DONE:
            self._db.sync()
        else:
            raise PrematureDocumentEndError

    def startElement(self, name, attrs):
        if self._state == SkedDocumentHandler.WAITING_SKEDDATA \
        and name == "skeddata":
            ver = attrs.get("version")
            if ver != "1.0":
                raise VersionError
            self._state = SkedDocumentHandler.WAITING_ENTRY
        elif self._state == SkedDocumentHandler.WAITING_ENTRY \
        and name == "entry":
            self._pagename = attrs.get("name")
            self._pagedata = ""
            self._state = SkedDocumentHandler.WAITING_DATA
        else:
            raise DataFormatError

    def endElement(self, name):
        if self._state == SkedDocumentHandler.WAITING_DATA \
        and name == "entry":
            self._db.set_key("pag_" + self._pagename, self._pagedata)
            self._state = SkedDocumentHandler.WAITING_ENTRY
        elif self._state == SkedDocumentHandler.WAITING_ENTRY \
        and name == "skeddata":
            self._state = SkedDocumentHandler.DONE
        else:
            raise FormatError

    def characters(self, chrs, offset, length):
        if self._state == SkedDocumentHandler.WAITING_DATA:
            self._pagedata = self._pagedata + chrs[offset:offset+length]
        else:
            raise FormatError

    def get_state(self):
        return self._state



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



class XMLFileExporter(XMLExporter):
    """Exports Sked databases as XML files without compression or encryption.
    """
    
    def __init__(self, db, fname):
        """Creates a new data exporter. 'db' is a Sked database and 'fname' is 
        the file wich will receive the data."""
        
        self._fname = fname
        fp = open(fname, "w")
        XMLExporter.__init__(self, db, fp)

    def close(self):
        self._fp.close()
