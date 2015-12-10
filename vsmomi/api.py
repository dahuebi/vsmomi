# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
        print_function, unicode_literals)

from builtins import *
from future.builtins.disabled import *

import re

def export(func):
    func.export = True
    return func

def isExported(func):
    if not callable(func):
        return False
    if not hasattr(func, "export"):
        return False
    return func.export

class API(object):
    def __init__(self, *args, **kwargs):
        from .application import Application
        app = Application(*args, **kwargs)
        self.__app = app
        for obj in [app] + app.subCommands:
            for attr in dir(type(obj)):
                if attr.startswith("_"):
                    continue
                typeFunc = getattr(type(obj), attr)
                if isExported(typeFunc):
                    if hasattr(self, attr):
                        raise RuntimeError("'{}' already exported".format(attr))
                    func = getattr(obj, attr)
                    setattr(self, attr, func)

    @export
    def getVms(self, pattern, sort=True, asDict=False):
        return self.__app.getRegisteredVms(pattern, sort, asDict)
