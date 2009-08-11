#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
Sked uses a key "strengthing algorithm" for is DB4 encryption passwords
that make key testing deliberately slow in order to spoil dictionary
attacks. This application prints the generated keys for use with the 
db4-utils suite (db4.x_dump, db4.x_verify, etc.).
"""

import database
import getpass

print(__doc__)
print("Database key: " + database.make_key(getpass.getpass()))

