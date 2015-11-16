# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
        print_function, unicode_literals)

from builtins import *
from future.builtins.disabled import *

import logging

from Cheetah.Template import Template as CT
from pyVmomi import vim

from .sub_command import SubCommand
from ..virtual_machine_disk_layout import VirtualMachineDiskLayout
from ..vctask import VcTask
