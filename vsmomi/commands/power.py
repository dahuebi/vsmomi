# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
        print_function, unicode_literals)

from builtins import *
from future.builtins.disabled import *

from ._common import *

class Power(SubCommand):
    def __init__(self, *args, **kwargs):
        super(Power, self).__init__(*args, **kwargs)

    @classmethod
    def addParser(cls, cmdLineParser, subparsers):
        parser = cmdLineParser.getSubParser(
                "power", subparsers,
                help="Power VMs")
        parser.add_argument(
                "patterns", nargs="+", type=cmdLineParser.patternToRegexp,
                metavar="pattern",
                help="VMs to select")
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--on", action="store_true")
        group.add_argument("--off", action="store_true")
        group.add_argument("--reset", action="store_true")
        group.add_argument("--shutdown", action="store_true")
        group.add_argument("--halt", action="store_true")
        group.add_argument("--reboot", action="store_true")
        parser.set_defaults(powerArgs=["patterns",
            "on", "off", "reset", "halt", "reboot", "shutdown"])

    @export
    def power(self, patterns=[], on=False, off=False, reset=False,
            shutdown=False, halt=False, reboot=False):
        tmpl = CT.compile(
""" \
#for $name, $v in $ns.items()
<%="{:30}: {}".format(name, v)%> \
#end for \
""")
        if not patterns:
            raise RuntimeError("Must give a vm")
        action = ""
        if on: action = "PowerOn"
        elif off: action = "PowerOff"
        elif reset: action = "Reset"
        elif shutdown or halt: action = "ShutdownGuest"
        elif reboot: action = "RebootGuest"
        else:
            raise NotImplementedError("Power action not supported")
        vms = self.getRegisteredVms(regexps=patterns)
        for vm in vms:
            getattr(vm, action)()
            self.output({vm.name: action}, tmpl=tmpl)
        return 0

