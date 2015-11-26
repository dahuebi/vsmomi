# -*- coding: utf-8 -*-

from __future__ import (absolute_import, division,
        print_function, unicode_literals)

from builtins import *
from future.builtins.disabled import *

import base64
import atexit

import requests
# disable warnings
try:
    requests.packages.urllib3.disable_warnings()
except AttributeError:
    pass

from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect

class ServiceInstance(object):
    def __init__(self, vcenter, username, password):
        self.si = None
        self.vcenter = vcenter
        self.username = username
        self.password = password
        self.__connect()

    def __connect(self):
        connect = True
        if self.si:
            # check connection
            try:
                self.si.CurrentTime()
                connect = False
            except vim.fault.NotAuthenticated:
                # timeout
                pass

        if connect:
            si = None
            try:
                pwd = base64.b64decode(self.password).decode("utf-8")
                si = SmartConnect(
                    host=self.vcenter,
                    user=self.username,
                    pwd=pwd,
                    port=443)
            except IOError:
                raise
            if self.si is None:
                atexit.register(Disconnect, self.si) 
            else:
                Disconnect(self.si)
            self.si = si

    def __getattr__(self, name):
        self.__connect()
        return getattr(self.si, name)

