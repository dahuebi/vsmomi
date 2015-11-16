# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
        print_function, unicode_literals)

from builtins import *
from future.builtins.disabled import *

import re

from ._common import *

class Help(SubCommand):
    PARSER = None
    def __init__(self, *args, **kwargs):
        super(Help, self).__init__(*args, **kwargs)

    @classmethod
    def addParser(cls, cmdLineParser, subparsers):
        cls.PARSER = cmdLineParser
        parser = cmdLineParser.getSubParser(
                "help", subparsers,
                help="Show help of all command")
        parser.set_defaults(helpArgs=[])

    def help(self):
        self.PARSER.showFullHelp()
        sys.exit(0)

