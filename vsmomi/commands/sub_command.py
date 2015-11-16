# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
        print_function, unicode_literals)

from builtins import *
from future.builtins.disabled import *

class SubCommand(object):
    def __init__(self, main, *args, **kwargs):
        super(SubCommand, self).__init__(*args, **kwargs)
        self._main = main

    @classmethod
    def addParser(cls, subParsers):
        raise NotImplementedError()

    def __getattr__(self, name):
        return getattr(self._main, name)
