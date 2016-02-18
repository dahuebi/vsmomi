# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
        print_function, unicode_literals)

from builtins import *
from future.builtins.disabled import *

import time
import re
import os

from ._guest_common import *

import argparse

class GuestReadEnv(GuestCommand):
    def __init__(self, *args, **kwargs):
        super(GuestReadEnv, self).__init__(*args, **kwargs)

    @classmethod
    def addParser(cls, cmdLineParser, subparsers):
        parser = cmdLineParser.getSubParser(
                "guest-read-env", subparsers,
                help="Read env on VMs")
        commonArgs = cls._addCommonArgs(cmdLineParser, parser)
        parser.set_defaults(guestReadEnvArgs=commonArgs)

    @export
    def guestReadEnv(self, **kwargs):
        auth, vms = self._guestCommon(**kwargs)
        content = self.content()
        pm = content.guestOperationsManager.processManager
        for vm in vms:
            if not self._guestCheckTools(vm, auth):
                data = {vm.name: {"success": False, "ERROR": "VMTools not OK"}}
                self.output(data, level=logging.ERROR)
                continue

            env = pm.ReadEnvironmentVariableInGuest(vm=vm, auth=auth,
                    names=[])
            print (env)
            for keyValue in env:
                key, value = keyValue.split("=", 1)
                print (key, value)

