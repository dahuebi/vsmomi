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
        # TODO
        pass

    def snapshot(self, name=None, snap=None):
        regexps = [re.compile("^{}$".format(re.escape(name)))]
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


