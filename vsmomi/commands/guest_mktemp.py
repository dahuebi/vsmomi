# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
        print_function, unicode_literals)

from builtins import *
from future.builtins.disabled import *

import re
import os

from ._guest_common import *

class GuestMkTemp(GuestCommand):
    def __init__(self, *args, **kwargs):
        super(GuestMkTemp, self).__init__(*args, **kwargs)

    @classmethod
    def addParser(cls, cmdLineParser, subparsers):
        parser = cmdLineParser.getSubParser(
                "guest-mktemp", subparsers,
                help="Delete from VMs")
        commonArgs = cls._addCommonArgs(cmdLineParser, parser)
        parser.add_argument(
                "--prefix",
                metavar="prefix",
                default="",
                help="Prefix")
        parser.add_argument(
                "--suffix",
                metavar="suffix",
                default="",
                help="Suffix")
        parser.set_defaults(guestMktempArgs=commonArgs +
                ["prefix", "suffix"])

    @export
    def guestMktemp(self, prefix="", suffix="", **kwargs):
        self._checkType(prefix, str)
        self._checkType(suffix, str)
        rc = 0
        tmpl = CT.compile(
""" \
#for name, guestFilePath in $ns.items()
<%="{} {}".format(name, guestFilePath)%> \
#end for \
""")
        auth, vms = self._guestCommon(**kwargs)
        content = self.content()
        fm = content.guestOperationsManager.fileManager
        tempDirs = {}
        for vm in vms:
            vmName = vm.name
            if vm.guest.toolsStatus != "toolsOk":
                self.logger.error("VMTools not OK: {}".format(vmName))
                rc = 1
                continue

            tempDir = fm.CreateTemporaryDirectoryInGuest(vm=vm, auth=auth,
                    prefix=prefix, suffix=suffix)
            tempDirs[vmName] = tempDir

        data = {}
        data.update(tempDirs)
        self.output(data, tmpl=tmpl)

        if rc:
            raise RuntimeError("Create Temp Directory failed")

        return rc, tempDirs
