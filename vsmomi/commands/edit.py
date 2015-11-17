# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
        print_function, unicode_literals)

from builtins import *
from future.builtins.disabled import *

import re

from ._common import *

class Edit(SubCommand):
    def __init__(self, *args, **kwargs):
        super(Edit, self).__init__(*args, **kwargs)

    @classmethod
    def addParser(cls, cmdLineParser, subparsers):
        parser = cmdLineParser.getSubParser(
                "edit", subparsers,
                help="Edit VM")
        parser.add_argument(
                "name",
                metavar="name",
                help="VM to edit")
        parser.add_argument(
                "--cpus", type=int,
                metavar="cpus",
                help="CPUs")
        parser.add_argument(
                "--memory", type=int,
                metavar="memory",
                help="Memory in MB")
        parser.add_argument(
                "--extra-config", nargs="+", type=cmdLineParser.extraConfigType,
                default=[],
                metavar="key=value", dest="extraConfig",
                help="Extra config, use key=value")
        parser.add_argument(
                "--network", type=str,
                metavar="network",
                help="Set network for _ALL_ interfaces")
        parser.add_argument(
                "--iso", type=cmdLineParser.isoType,
                metavar="<[Datastore] path to iso>",
                help="Load iso into cdrom, format:\n" \
                "[Datastore] <path to iso>")
        parser.add_argument(
                "--disk-new", nargs="+",
                default=[], type=cmdLineParser.diskNewType,
                metavar = "<disk-new>",
                dest="diskNew",
                help="Add a disk\n" \
                "[ctrlNr-slotNr,]size=capacity[mb|gb|tg]" \
                )
        parser.add_argument(
                "--disk-linked", nargs="+",
                default=[], type=cmdLineParser.diskLinkedType,
                metavar="<disk-linked>",
                dest="diskLinked",
                help="Add a disk with delta backing\n" \
                "[<ctrlNr>-<slotNr>,]vm[:snapshot],<ctrlNr>-<slotNr>"
                )

        parser.add_argument(
                "--disk-destroy", nargs="+",
                default=[], type=cmdLineParser.diskDestroyType,
                metavar="<ctrlNr-slotNr>",
                dest="diskDestroy",
                help="List of [controllerNumber-slotNumber] to delete, ex: 0-1 2-3")

        # nic
        parser.set_defaults(editArgs=["name",
            "cpus", "memory", "diskDestroy", "network", "iso",
            "extraConfig", "diskNew", "diskLinked"])

    @export
    def edit(self, name=None, cpus=None, memory=None, extraConfig=[], network=None, iso=None,
            diskDestroy=[], diskNew=[], diskLinked=[]):
        self._checkType(name, str)
        self._checkType(memory, (type(None), int))
        self._checkType(cpus, (type(None), int))
        self._checkType(extraConfig, list)
        for ec in extraConfig:
            self._checkType(ec, tuple)
            [self._checkType(x, str) for x in ec]
            assert len(ec) == 2
        self._checkType(network, (type(None), str))
        self._checkType(iso, (type(None), str))
        self._checkType(diskDestroy, list)
        for dd in diskDestroy:
            self._checkType(dd, tuple)
            [self._checkType(x, int) for x in dd]
            assert len(dd) == 2
        self._checkType(diskLinked, list)
        for dl in diskLinked:
            self._checkType(dl, dict)
            assert "slot" in dl
            assert "vm" in dl
            assert "vmSlot" in dl
            self._checkType(dl["slot"], tuple)
            [self._checkType(x, (type(None), int)) for x in dl["slot"]]
            assert len(dl["slot"]) == 2
            self._checkType(dl["vmSlot"], tuple)
            [self._checkType(x, int) for x in dl["vmSlot"]]
            assert len(dl["vmSlot"]) == 2
            self._checkType(dl["vm"], tuple)
            assert len(dl["vm"]) == 2
            self._checkType(dl["vm"][0], str)
            self._checkType(dl["vm"][1], (type(None), str))
        self._checkType(diskNew, list)
        for dn in diskNew:
            self._checkType(dn, dict)
            assert "slot" in dn
            assert "capacity" in dn
            self._checkType(dn["slot"], tuple)
            [self._checkType(x, (type(None), int)) for x in dn["slot"]]
            assert len(dn["slot"]) == 2
            self._checkType(dn["capacity"], int)


        regexps = [re.compile("^{}$".format(re.escape(name)))]
        vm = self.getRegisteredVms(regexps=regexps)[0]

        configSpec = vim.vm.ConfigSpec()
        VDS = vim.vm.device.VirtualDeviceSpec
        devices = []

        # fix newint class
        configSpec.numCPUs = self._toNativeInt(cpus)
        configSpec.memoryMB = self._toNativeInt(memory)
        self._configSpecAddExtraConfig(configSpec, extraConfig)

        # find first cdrom
        CDROM = vim.vm.device.VirtualCdrom
        layout = VirtualMachineDiskLayout(vm)
        for (ctrlNr, slotNr, disk) in layout:
            if isinstance(disk, CDROM):
                cdrom = disk
                break
        # iso == "" -> unassign
        if iso is not None and not cdrom:
            raise RuntimeError("Try to assign ISO, but no CDROM found")
        if iso is not None and cdrom.connectable.connected:
            raise RuntimeError("CDROM is locked, please power off VM or eject CDROM in guest")
        if iso:
            backing = vim.vm.device.VirtualCdrom.IsoBackingInfo()
            backing.fileName = iso
            cdrom.backing = backing
            ci = vim.vm.device.VirtualDevice.ConnectInfo()
            ci.allowGuestControl = False
            connected = False
            if iso:
                connected = True
            ci.connected = connected
            ci.startConnected = connected
            cdrom.connectable = ci
            change = VDS(
                    operation=VDS.Operation.edit,
                    device=cdrom)
            devices.append(change)

        for ctrlNr, slotNr in diskDestroy:
            disk = layout.getDisk(ctrlNr, slotNr)
            if not disk:
                raise LookupError("Disk {}-{} not found".format(ctrlNr, slotNr))
            layout.delSlot(ctrlNr, slotNr)
            if not disk:
                continue

            change = VDS(
                operation=VDS.Operation.remove,
                fileOperation=VDS.FileOperation.destroy,
                device=disk
            )
            devices.append(change)

        # disk-new: {"slot": (m, n), "capacity":size}
        #           m, n may be None
        for entry in diskNew:
            (ctrlNr, slotNr) = entry["slot"]
            capacity = entry["capacity"]
            if ctrlNr is None:
                # get free slot
                ctrlNr, slotNr = layout.getFreeSlot()
            capacityInKB = capacity // 1024

            ctrl = layout.getController(ctrlNr)
            ctrlKey = ctrl.key

            backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo(
                diskMode="persistent", # persistent: dependent
                thinProvisioned=True,
                parent = None
                )
            disk = vim.vm.device.VirtualDisk(
                key=-1,
                backing=backing,
                capacityInKB=capacityInKB,
                controllerKey=ctrlKey,
                unitNumber=slotNr
                )
            layout.addDisk(ctrlNr, slotNr, disk)

            change = VDS(
                operation=VDS.Operation.add,
                fileOperation=VDS.FileOperation.create,
                device=disk
                )

            devices.append(change)

        # disk-linked: {"slot": (n, m)?, "vm": (vm, snashot?), "vmSlot": (x, y)}
        #              m, n may be None
        for entry in diskLinked:
            (ctrlNr, slotNr) = entry["slot"]
            if ctrlNr is None:
                # get free slot
                ctrlNr, slotNr = layout.getFreeSlot()
            (fromVmName, fromSnapshotName) = entry["vm"]
            fromVm = self.getVmByName(fromVmName)
            if not fromVm:
                raise LookupError("From VM '{}' not found".format(fromVmName))
            fromSnapshot = None
            for root, tree in self._walkVmSnapshots(fromVm):
                if not fromSnapshotName:
                    # find latest snapshot
                    fromSnapshot = tree.snapshot
                elif fromSnapshot == tree.name:
                    fromSnapshot = tree.snapshot
                    break

            if not fromSnapshot:
                raise LookupError("No snapshot or snapshot '{}' not found in VM '{}'".format(
                    fromSnapshotName, fromVmName))
            fromLayout = VirtualMachineDiskLayout(fromSnapshot)
            (fromCtrlNr, fromSlotNr) = entry["vmSlot"]
            fromDisk = fromLayout.getDisk(fromCtrlNr, fromSlotNr)
            if not fromDisk:
                raise LookupError("From Disk '{}' not found in snapshot '{}'".format(
                    (fromCtrlNr, fromSlotNr), fromSnapshotName))
            deltaBacking= fromDisk.backing.parent

            ctrl = layout.getController(ctrlNr)
            ctrlKey = ctrl.key

            backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo(
                diskMode="persistent", # persistent: dependent
                thinProvisioned=True,
                parent = deltaBacking
                )
            disk = vim.vm.device.VirtualDisk(
                key=-1,
                backing=backing,
                capacityInKB=0,
                controllerKey=ctrlKey,
                unitNumber=slotNr
                )
            layout.addDisk(ctrlNr, slotNr, disk)

            change = VDS(
                operation=VDS.Operation.add,
                fileOperation=VDS.FileOperation.create,
                device=disk
                )

            devices.append(change)

        if network:
            # find network
            for nic in self._getVmNics(vm):
                nic.backing.deviceName = network
                change = VDS(
                    operation=VDS.Operation.edit,
                    device=nic
                )
                devices.append(change)

        configSpec.deviceChange = devices

        task = vm.ReconfigVM_Task(spec=configSpec)
        vcTask = VcTask(task)
        vcTask.waitTaskDone()
        if vcTask.isSuccess():
            self.logger.info("Success")
        else:
            msg = vcTask.error()
            self.logger.error("Failed {}".format(repr(msg)))
            raise RuntimeError("Edit failed")

        return 0

