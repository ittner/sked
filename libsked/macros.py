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
#

import json
import datetime

class MacroManager(object):
    """ Handles keyboard macros.
    """

    def __init__(self):
        self._macros = dict()

    @staticmethod
    def new_from_string(json_data):
        m = MacroManager()
        m.load_string(json_data)
        return m

    def load_string(self, json_data):
        try:
            d = json.loads(json_data)
            if type(d) != dict: return  # Bad data
            for k in d: self.add(str(k), str(d[k]))
        except ValueError:
            pass

    def dump_string(self):
        return json.dumps(self._macros)

    def add(self, name, value):
        # TODO: Validate the %tokens in value
        name = name.strip().lower()
        if name != "":
            self._macros[name] = value

    def remove(self, name):
        if self._macros.has_key(name):
            del self._macros[name]

    def clear(self):
        self._macros = dict()

    def iterate(self):
        # Ensures alphabetical order
        skeys = sorted(self._macros.keys())
        for k in skeys:
            yield k, self._macros[k]

    @staticmethod
    def _evaluate(format_string):
        # TODO: Add tokens for non-date operations (page name, word
        # replacements, number conversions, arithmetic operations, etc...)
        return datetime.datetime.now().strftime(format_string)

    def find_and_evaluate(self, text_line):
        lline = text_line.lower()
        slline = lline.rstrip()
        skeys = sorted(self._macros.keys())
        for k in skeys:
            if slline.endswith(k):
                ndx = lline.rfind(k)
                if ndx > -1:
                    macro = self._macros[k]
                    return text_line[0:ndx] + MacroManager._evaluate(macro)
        return None

