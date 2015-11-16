# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
        print_function, unicode_literals)

from builtins import *
from future.builtins.disabled import *

from pyVmomi import vim

class VirtualMachineDiskLayout(object):
    def __init__(self, vm):
        self.layout = {}
        self.__layout(vm)

    def delSlot(self, ctrlNr, slotNr):
        layout = self.layout
        try:
            del layout[ctrlNr]["slots"][slotNr]
        except KeyError:
            pass

    def getController(self, ctrlNr):
        layout = self.layout
        ctrl = None
        try:
            ctrl = layout[ctrlNr]["ctrl"]
        except KeyError:
            pass
        return ctrl

    def addController(self, ctrlNr, ctrl):
        layout = self.layout
        assert ctrlNr not in layout, "%d" % (ctrlNr)
        layout[ctrlNr] = {"ctrl": ctrl, "slots": {}}

    def addDisk(self, ctrlNr, slotNr, disk):
        layout = self.layout
        assert ctrlNr in layout, \
                "controller '{}' must exist".format(ctrlNr)
        assert slotNr not in layout[ctrlNr]["slots"], \
                "slot '{}' must not exist".format((ctrlNr, slotNr))
        layout[ctrlNr]["slots"][slotNr] = disk

    def getDisk(self, ctrlNr, slotNr):
        layout = self.layout
        disk = None
        try:
            disk = layout[ctrlNr]["slots"][slotNr]
        except KeyError:
            pass
        return disk

    def getFreeSlot(self):
        layout = self.layout
        for ctrlNr in sorted(layout.keys()):
            slotList = layout[ctrlNr]["slots"]
            for slotNr in range(0, 16): # slots per controller 16
                if slotNr not in slotList.keys():
                    return ctrlNr, slotNr
        assert False, "%d-%d" % (ctrlNr, slotNr)

    def __iter__(self):
        layout = self.layout
        for ctrlNr in sorted(layout.keys()):
            slotList = layout[ctrlNr]["slots"]
            for slotNr in sorted(slotList.keys()):
                disk = layout[ctrlNr]["slots"][slotNr]
                yield (ctrlNr, slotNr, disk)

    def __layout(self, vm):
        # layout:
        # {controllerNumber (0...)}{'slots'}{slotNumber (0..16)} = disk
        res = {}
        ctrls = []
        disks = []
        for dev in vm.config.hardware.device:
            # vim.vm.device.VirtualController
            # vim.vm.device.VirtualIDEController
            # vim.vm.device.VirtualSCSIController
            if isinstance(dev, (vim.vm.device.VirtualSCSIController, vim.vm.device.VirtualIDEController)):
                ctrls.append(dev)
            if isinstance(dev, (vim.vm.device.VirtualDisk, vim.vm.device.VirtualCdrom)):
                disks.append(dev)
        for ctrlNr in range(0, len(ctrls)):
            ctrl = ctrls[ctrlNr]
            ctrlDisks = [x for x in disks if x.key in ctrl.device]
            self.addController(ctrlNr, ctrl)
            for disk in ctrlDisks:
                self.addDisk(ctrlNr, disk.unitNumber, disk)

