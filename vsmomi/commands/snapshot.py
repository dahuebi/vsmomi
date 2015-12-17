# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
        print_function, unicode_literals)

from builtins import *
from future.builtins.disabled import *

import re

from ._common import *

class Snapshot(SubCommand):
    def __init__(self, *args, **kwargs):
        super(Snapshot, self).__init__(*args, **kwargs)

    @classmethod
    def addParser(cls, cmdLineParser, subparsers):
        parser = cmdLineParser.getSubParser(
                "snapshot", subparsers,
                help="Create snapshots")
        parser.add_argument(
                "name",
                metavar="name",
                help="VM to create snapshot")
        parser.add_argument(
                "snap",
                metavar="<snashot name>",
                help="Snapshot to create.")
        parser.set_defaults(snapshotArgs=["name", "snap"])

    @export
    def snapshot(self, name=None, snap=None):
        self._checkType(name, (str, vim.VirtualMachine))
        self._checkType(snap, str)

        regexps = [re.compile("^{}$".format(re.escape(name)))]
        #snap = snap.decode("UTF-8")
        vm = self.getRegisteredVms(regexps=regexps)[0]
        task = vm.CreateSnapshot(name=snap, memory=False, quiesce=False)
        vcTask = VcTask(task)
        vcTask.waitTaskDone()
        if vcTask.isSuccess():
            self.logger.info("Success")
        else:
            msg = vcTask.error()
            self.logger.error("Failed {}".format(repr(msg)))
            raise RuntimeError("Snapshot failed")

        return 0


