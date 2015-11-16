# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
        print_function, unicode_literals)

from builtins import *
from future.builtins.disabled import *

from .application import Application
from .command_line_parser import CommandLineParser
from .service_instance_api import DryrunError

import sys

def main(argv=sys.argv[1:]):
    return Application.main(argv=argv)
