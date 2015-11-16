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
                metavar="extra-config", dest="extraConfig",
                help="Extra config, use key=value")
        parser.add_argument(
                "--network", type=str,
                metavar="network",
                help="Set network for _ALL_ interfaces")
        parser.add_argument(
                "--iso", type=cmdLineParser.isoType,
                metavar="iso",
                help="Load iso into cdrom, format:\n" \
                "[Datastore] <path to iso>")
        parser.add_argument(
                "--disk-new", nargs="+",
                default=[], type=cmdLineParser.diskNewType,
                metavar = "(<ctrlNr>-<slotNr>),size=<capacity>[mb|gb|tg]",
                dest="diskNew",
                help="Add a disk\n" \
                "[ctrlNr-slotNr,]size=capacity[GB]" \
                "capacity: supports KB, MB, GB, TB, defaults to GB"
                )
        parser.add_argument(
                "--disk-linked", nargs="+",
                default=[], type=cmdLineParser.diskLinkedType,
                metavar="[<ctrlNr>-<slotNr>,] vm[:snapshot],<ctrlNr>-<slotNr>",
                dest="diskLinked",
                help="Add a disk\n" \
                "sourceVm=<name>[:<snapshot>]:ctrlNr-slotNr"
                )

        parser.add_argument(
                "--disk-destroy", nargs="+",
                default=[], type=cmdLineParser.diskDestroyType,
                metavar="<ctrlNr>-<slotNr>",
                dest="diskDestroy",
                help="List of [controllerNumber-slotNumber] to delete, ex: 0-1 2-3")

        # nic
        parser.set_defaults(editArgs=["name",
            "cpus", "memory", "diskDestroy", "network", "iso",
            "extraConfig", "diskNew", "diskLinked"])

    def edit(self, name=None, cpus=None, memory=None, extraConfig=[], network=None, iso=None,
            diskDestroy=[], diskNew=[], diskLinked=[]):
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

        # TODO: disk_add
        # disk-new: {"slot": (n, m)?, "capacity":size}
        # disk-linked: {"slot": (n, m)?, "vm": (vm, snashot?), "vmSlot": (x, y)}
        for diskNew in disk_add_new:
            m = re.search("size=([\d]+)(GB|MG|TG|KB)?", diskNew, re.I)
            if not m:
                raise RuntimeError("Invalid format '{}'".format(diskNew))
            size, unit = m.groups()
            slotId = re.sub(",?size=.*", "", diskNew)
            (ctrlNr, slotNr) = (None, None)
            if slotId:
                m = re.search("^([\d]+)-([\d]+)", slotId)
                if not m:
                    raise RuntimeError("Wrong fromat in slotId '{}'".format(slotId))
                (ctrlNr, slotNr) = m.groups()
            else:
                # get free slot
                ctrlNr, slotNr = layout.getFreeSlot()
            print (size, unit, ctrlNr, slotNr)
            capacityInKB = size

            backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo(
                diskMode="persistent", # persistent: dependent
                thinProvisioned=True,
                parent = None
                )
            ctrl = layout.getController(ctrlNr)
            ctrlKey = ctrl.key
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

