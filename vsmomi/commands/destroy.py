# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
        print_function, unicode_literals)

from builtins import *
from future.builtins.disabled import *

import re

from ._common import *

class Destroy(SubCommand):
    def __init__(self, *args, **kwargs):
        super(Destroy, self).__init__(*args, **kwargs)

    @classmethod
    def addParser(cls, cmdLineParser, subparsers):
        parser = cmdLineParser.getSubParser(
                "destroy", subparsers,
                help="Destroy VMs")
        parser.add_argument(
                "names", nargs="+",
                metavar="name",
                help="VMs to destroy, name MUST match, no wildcard/regexps.")
        parser.set_defaults(destroyArgs=["names"])

    @export
    def destroy(self, names=[]):
        self._checkType(names, list)
        [self._checkType(x, (str, vim.VirtualMachine)) for x in names]

        # no wildcard or regexp patterns allowed
        if not names:
            raise RuntimeError("Must give vm")
        regexps = [re.compile("^{}$".format(name)) for name in names]
        tmpl = CT.compile(
""" \
#for $name, $v in $ns.items()
<%="{:30}: {}".format(name, v)%> \
#end for \
""")
        vms = self.getRegisteredVms(regexps=regexps)
        for vm in vms:
            vmName = vm.name
            vm.PowerOff()
            task = vm.Destroy()
            self.output({vmName: "Destroy"}, tmpl=tmpl)
            vcTask = VcTask(task)
            vcTask.waitTaskDone()

        return 0


