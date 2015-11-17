# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
        print_function, unicode_literals)

from builtins import *
from future.builtins.disabled import *

import re
import os

from ._guest_common import *

class GuestDelete(GuestCommand):
    def __init__(self, *args, **kwargs):
        super(GuestDelete, self).__init__(*args, **kwargs)

    @classmethod
    def addParser(cls, cmdLineParser, subparsers):
        parser = cmdLineParser.getSubParser(
                "guest-delete", subparsers,
                help="Delete from VMs")
        commonArgs = cls._addCommonArgs(cmdLineParser, parser)
        parser.add_argument(
                "--files", nargs="+", required=True,
                metavar="file",
                help="Files to delete")
        parser.set_defaults(guestDeleteArgs=commonArgs +
                ["files"])

    @export
    def guestDelete(self, files=[], recursive=True, **kwargs):
        self._checkType(files, list)
        [self._checkType(x, str) for x in files]
        self._checkType(recursive, bool)

        rc = 0
        tmpl = CT.compile(
""" \
#for name, v in $ns.items()
<%="{} {}".format(name, v["guestFilePath"])%> \
#end for \
""")
        auth, vms = self._guestCommon(**kwargs)
        content = self.content()
        fm = content.guestOperationsManager.fileManager
        for vm in vms:
            vmName = vm.name
            if vm.guest.toolsStatus != "toolsOk":
                self.logger.error("VMTools not OK: {}".format(vmName))
                rc = 1
                continue
            guestId = vm.summary.config.guestId
            sep = "/"
            if guestId.lower().startswith("win"):
                sep = r"\\"
            for file_ in files:
                guestFilePath = re.sub(r"[\\/]", sep, file_)
                data = {vmName: {"guestFilePath": guestFilePath, "success": False}}
                try:
                    try:
                        fm.DeleteDirectoryInGuest(vm=vm, auth=auth,
                                directoryPath=guestFilePath, recursive=True)
                    except vim.fault.NotADirectory:
                        fm.DeleteFileInGuest(vm=vm, auth=auth,
                                filePath=guestFilePath)
                except vim.fault.FileNotFound:
                    pass
                except:
                    self.output(data, tmpl=tmpl, level=logging.ERROR)
                else:
                    data[vmName]["success"] = True
                    self.output(data, tmpl=tmpl)
        if rc:
            raise RuntimeError("Delete failed")
