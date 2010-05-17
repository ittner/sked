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

    def __init__(self, page_manager, callback = None):
        self._pm = page_manager
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
            self._pm.save(Page(self._pagename, self._pagedata), False)
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



class SkedEntityResolver(EntityResolver):
    def resolveEntity(self, publicId, systemId):
        if systemId == "sked.dtd":
            return utils.data_path(systemId)
        return None


def import_xml_data(page_manager, fp, callback = None):
    """ Import XML data from a stream 'fp' into the page manager. 'callback'
    will be called for each entry imported. """

    parser = sax.make_parser()
    parser.setContentHandler(SkedContentHandler(page_manager, callback))
    parser.setEntityResolver(SkedEntityResolver())
    parser.parse(fp)


def import_xml_file(page_manager, fname, callback = None):
    """ Import XML data from a file 'fname' into the given page manager. 
    'callback' will be called for each entry imported. """
    
    fp = open(fname, "rb")
    import_xml_data(page_manager, fp, callback)
    fp.close()


def export_xml_file(page_manager, fname, callback = None):
    """ Exports the pages from the page manager to the file named 'fname'
    with no compression or encryption. For each entry exported, 'callback'
    will be called with no arguments.
    """

    fp = open(fname, "w")
    fp.write('<?xml version="1.0" encoding="utf-8"?>\n'
        '<!DOCTYPE skeddata SYSTEM "sked.dtd">\n'
        '<skeddata version="1.0">\n')
    for page in page_manager.iterate():
        fp.write(" <entry name=%s>%s</entry>\n" % (
            saxutils.quoteattr(page.name).encode("utf-8"),
            saxutils.escape(page.text).encode("utf-8")))
        if callback != None: callback()
    fp.write("</skeddata>\n")
    fp.close()
