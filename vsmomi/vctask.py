# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
        print_function, unicode_literals)

from builtins import *
from future.builtins.disabled import *

import time
from pyVmomi import vim

class VcTask(object):
    def __init__(self, task):
        self.task = task

    def isSuccess(self):
        return self.state() == vim.TaskInfo.State.success

    def state(self):
        return self.task.info.state

    def error(self):
        return self.task.info.error

    def isTaskDone(self):
        return self.state() in [vim.TaskInfo.State.success, vim.TaskInfo.State.error]

    def waitTaskDone(self):
        while not self.isTaskDone():
            time.sleep(1.0)
        return self.state()

    def __getattr__(self, name):
        return getattr(self.task, name)

