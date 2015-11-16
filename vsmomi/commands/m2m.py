# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
        print_function, unicode_literals)

from builtins import *
from future.builtins.disabled import *

import sys
import json
import traceback

from ._common import *

class M2M(SubCommand):
    def __init__(self, *args, **kwargs):
        super(M2M, self).__init__(*args, **kwargs)

    @classmethod
    def addParser(cls, cmdLineParser, subparsers):
        parser = cmdLineParser.getSubParser(
                "m2m", subparsers,
                help="Machine to machine interface")
        parser.set_defaults(m2mArgs=[])

    def m2m(self, which=None, **kwargs):
        assert which
        assert which != "m2m"
        func = getattr(self, which)
        self.isM2M = True
        self.jsonObj = {}
        sys.stdout = sys.stderr
        try:
            rc = func(**kwargs)
        except:
            s = traceback.format_exc()
            self.jsonObj["ERROR"] = s
            raise
        finally:
            sys.stdout = sys.__stdout__
            print(json.dumps(self.jsonObj, indent=4, separators=(',', ': ')))
        return rc

