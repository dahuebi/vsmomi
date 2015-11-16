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

class GuestExecute(GuestCommand):
    def __init__(self, *args, **kwargs):
        super(GuestExecute, self).__init__(*args, **kwargs)

    @classmethod
    def addParser(cls, cmdLineParser, subparsers):
        parser = cmdLineParser.getSubParser(
                "guest-execute", subparsers,
                help="Execute on VMs")
        commonArgs = cls._addCommonArgs(cmdLineParser, parser)
        parser.add_argument(
                "--cmd", nargs=argparse.REMAINDER,
                metavar="<cmd>",
                help="Command to execute, will be joined.")
        parser.set_defaults(guestExecuteArgs=commonArgs +
                ["cmd"])

    def guestExecute(self, cmd=[], **kwargs):
        if not cmd:
            raise RuntimeError("No command provided")
        tmpl = CT.compile(
""" \
#for name, v in $ns.items()
<%="{}: {} [exitCode:{}]".format(name, v["prog"], v["exitCode"])%> \
#end for \
""")
        rc = 0
        cmd = " ".join(cmd)
        prog = cmd
        args = ""
        try:
            (prog, args) = cmd.split(" ", 1)
        except ValueError:
            pass
        wd = re.sub(r"[^\\/]*$", "", prog)
        cmdspec = vim.vm.guest.ProcessManager.ProgramSpec(
                arguments=args, programPath=prog,
                workingDirectory=wd)
        auth, vms = self._guestCommon(**kwargs)
        content = self.content()
        pm = content.guestOperationsManager.processManager
        tasks = {}
        for vm in vms:
            if vm.guest.toolsStatus != "toolsOk":
                data = {vm.name: {"success": False, "ERROR": "VMTools not OK"}}
                self.output(data, level=logging.ERROR)
                rc = 1
                continue

            pid = pm.StartProgramInGuest(vm=vm, auth=auth,
                    spec=cmdspec)
            tasks[vm] = pid

        # wait for completion
        sync = True
        while sync and tasks:
            time.sleep(1)
            for vm in tasks.keys():
                pid = tasks[vm]
                procInfo = pm.ListProcessesInGuest(vm=vm, auth=auth,
                        pids=[pid])
                if procInfo:
                    procInfo = procInfo[0]
                    if procInfo.endTime is None:
                        continue
                    exitCode = procInfo.exitCode
                    data = {vm.name: {"success": False, "prog": prog, "exitCode": exitCode}}
                    if exitCode:
                        self.output(data, tmpl=tmpl, level=logging.ERROR)
                        rc = 2
                    else:
                        data[vm.name]["success"] = True
                        self.output(data, tmpl=tmpl)
                del tasks[vm]

        return rc

