# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
        print_function, unicode_literals)

from builtins import *
from future.builtins.disabled import *

import re
import os

from ._guest_common import *

class GuestLs(GuestCommand):
    def __init__(self, *args, **kwargs):
        super(GuestLs, self).__init__(*args, **kwargs)

    @classmethod
    def addParser(cls, cmdLineParser, subparsers):
        parser = cmdLineParser.getSubParser(
                "guest-ls", subparsers,
                help="List files in guest")
        commonArgs = cls._addCommonArgs(cmdLineParser, parser)
        parser.add_argument(
                "--path", type=str, required=True,
                metavar="path",
                help="Path to list")
        parser.add_argument(
                "--pattern", type=str,
                default=".*",
                metavar="pattern",
                dest="pattern",
                help="Match pattern.")
        parser.set_defaults(guestLsArgs=commonArgs +
                ["path", "pattern"])

    @export
    def guestLs(self, path=None, pattern=None, **kwargs):
        self._checkType(pattern, (str, None))
        self._checkType(path, str)

        path = "{}".format(path)
        pattern = "{}".format(pattern)
        auth, vms = self._guestCommon(**kwargs)
        content = self.content()
        fm = content.guestOperationsManager.fileManager
        for vm in vms:
            vmName = vm.name
            if not self._guestCheckTools(vm, auth):
                self.logger.error("VMTools not OK: {}".format(vmName))
                rc = 1
                continue
            (sep, pathsep) = self.getGuestSeparators(vm)

            lf = fm.ListFilesInGuest(vm=vm, auth=auth, filePath=path,
                    index=0, maxResults=99999, matchPattern=pattern)
            print (lf)

