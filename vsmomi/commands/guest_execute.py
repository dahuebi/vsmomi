# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
        print_function, unicode_literals)

from builtins import *
from future.builtins.disabled import *

import time
import re
import os
import subprocess

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
        parser.add_argument(
                "--timeout", type=float,
                metavar="<timeout>",
                default=None,
                help="Command to execute, will be joined.")
        parser.set_defaults(guestExecuteArgs=commonArgs +
                ["cmd"])

    @export
    def guestExecute(self, cmd=[], timeout=None, **kwargs):
        self._checkType(cmd, list)
        [self._checkType(x, str) for x in cmd]
        self._checkType(timeout, (type(None), int, float))

        tmpl = CT.compile(
""" \
#for name, v in $ns.items()
<%="{}: {} [exitCode:{}]".format(name, v["prog"], v["exitCode"])%> \
#end for \
""")
        rc = 0
        prog = cmd[0]
        # TODO: guest os dependent escape for "
        args = []
        args = subprocess.list2cmdline(cmd[1:])
        wd = re.sub(r"[^\\/]*$", "", prog)
        cmdspec = vim.vm.guest.ProcessManager.ProgramSpec(
                arguments=args, programPath=prog,
                workingDirectory=wd)
        auth, vms = self._guestCommon(**kwargs)
        content = self.content()
        pm = content.guestOperationsManager.processManager
        tasks = {}
        for vm in vms:
            if not self._guestCheckUpgradeTools(vm, auth):
                data = {vm.name: {"success": False, "ERROR": "VMTools not OK"}}
                self.output(data, level=logging.ERROR)
                rc = 1
                continue

            pid = pm.StartProgramInGuest(vm=vm, auth=auth,
                    spec=cmdspec)
            tasks[vm] = pid

        if timeout is None:
            timeout = 7*24*3600
        timeEnd = time.time() + timeout
        # wait for completion
        sync = True
        try:
            while sync and tasks and timeEnd > time.time():
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
        except KeyboardInterrupt:
            rc = 3
            pass
        finally:
            if tasks:
                rc = 3
            for vm in tasks.keys():
                pid = tasks[vm]
                try:
                    pm.TerminateProcessInGuest(vm=vm, auth=auth, pid=pid)
                except vim.fault.GuestProcessNotFound:
                    pass

        return rc

