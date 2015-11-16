# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
        print_function, unicode_literals)

from builtins import *
from future.builtins.disabled import *

import re

from ._common import *

class Customize(SubCommand):
    def __init__(self, *args, **kwargs):
        super(Customize, self).__init__(*args, **kwargs)

    @classmethod
    def addParser(self, cmdLineParser, subParsers):
        # TODO: implement
        pass

    def customize(self, name=None, cms=None):
        regexps = [re.compile("^{}$".format(re.escape(name)))]
        vm = self.getRegisteredVms(regexps=regexps)[0]
        csm = self.getCSMByName(csm)
        task = vm.CustomizeVM(csm)
        vcTask = VcTask(task)
        vcTask.waitTaskDone()
        if vcTask.isSuccess():
            self.logger.info("Success")
        else:
            msg = vcTask.error()
            self.logger.error("Failed {}".format(repr(msg)))
            raise RuntimeError("CMS failed")

        return 0

