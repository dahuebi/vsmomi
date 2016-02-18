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

class GuestToolsUpgrade(GuestCommand):
    def __init__(self, *args, **kwargs):
        super(GuestToolsUpgrade, self).__init__(*args, **kwargs)

    @classmethod
    def addParser(cls, cmdLineParser, subparsers):
        parser = cmdLineParser.getSubParser(
                "guest-tools-upgrade", subparsers,
                help="Upgrade guest tools on VMs")
        commonArgs = cls._addCommonArgs(cmdLineParser, parser)
        parser.set_defaults(guestToolsUpgradeArgs=commonArgs)

    @export
    def guestToolsUpgrade(self, **kwargs):
        auth, vms = self._guestCommon(**kwargs)
        content = self.content()
        for vm in vms:
            if not self._guestCheckUpgradeTools(vm, auth):
                data = {vm.name: {"success": False, "ERROR": "VMTools not OK"}}
                self.output(data, level=logging.ERROR)
                continue

