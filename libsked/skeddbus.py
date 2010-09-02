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

import dbus
import dbus.service
import dbus.glib
import gobject

APP_DOMAIN = "br.com.ittner.Sked"
APP_OBJECT = "/br/com/ittner/Sked"
APP_INTERFACE = "br.com.ittner.Sked"


class SkedController(dbus.service.Object):
    """ Sked controller class (currently only shows the main window). """

    def __init__(self, app, instance_name):
        self.bus_name = make_bus_name(instance_name)
        self.app = app
        bus = dbus.SessionBus()
        sked_bus = dbus.service.BusName(self.bus_name, bus=bus)
        dbus.service.Object.__init__(self, sked_bus, APP_OBJECT)

    @dbus.service.method(APP_INTERFACE)
    def show_window(self):
        if self.app:
            self.app.window.present()
            return True


def make_bus_name(instance_name):
    """ Generates a Sked bus name for the given instance name. """
    return APP_DOMAIN + ".i" + instance_name


def ask_show_window(instance_name):
    """ Detects if the Sked instance given by 'instance_name' is running
    and sends a signal to it shows the main window. If this function
    returns True, the instance is running and the signal was received,
    so, the caller may exit before trying to get the database lock.
    If it returns False, there is no instance running or was not possible
    to send the signal -- for example, no DBus subsystem running.

    NOTE: Since the DBus service is enable only when the main application
    starts (not on database creation, verification, etc.) it is safe to
    abort the initialization of a new instance after this function returns
    True, but you MUST NOT assume that there is no instance running if it
    returns False. The standard locking mechanism applies in this case.
    """
    try:
        sked_bus_name = make_bus_name(instance_name)
        session_bus = dbus.SessionBus()
        if not sked_bus_name in session_bus.list_names():
            return False
        sked_obj = session_bus.get_object(sked_bus_name, APP_OBJECT)
        sked_iface = dbus.Interface(sked_obj, APP_INTERFACE)
        sked_iface.show_window()
        return True
    except:
        return False
