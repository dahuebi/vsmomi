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

    def destroy(self, names=[]):
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
            vm.Destroy()
            self.output({vmName: "Destroy"}, tmpl=tmpl)

        return 0


