# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
        print_function, unicode_literals)

from builtins import *
from future.builtins.disabled import *

import re

from ._common import *

class Clone(SubCommand):
    def __init__(self, *args, **kwargs):
        super(Clone, self).__init__(*args, **kwargs)

    @classmethod
    def addParser(cls, cmdLineParser, subparsers):
        parser = cmdLineParser.getSubParser(
                "clone", subparsers,
                help="Clone VMs")
        parser.add_argument(
                "name",
                metavar="name",
                help="VM to clone from")
        parser.add_argument(
                "--src-snap", type=str,
                metavar="<source snapshot>",
                dest="srcSnap",
                help="Snapshot to clone from, default to latest")
        parser.add_argument(
                "--target", nargs="+", required=True,
                metavar="target",
                help="List of target VMs to create")
        parser.add_argument(
                "--snap", type=str,
                metavar="<target snapshot>",
                help="If given, snapshot to create after cloning")
        parser.add_argument(
                "--disk-mode", nargs="*", type=cmdLineParser.diskModeType,
                default=["all"],
                metavar="disk-mode", dest="diskMode",
                help="Delta backing for disks, only store deltas, default to *all*" +
                "\n  all: link all disks\n  none: copy all disks\n  ctrlNr-slotNr: link specific disk")
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
                "--datastore", type=str,
                metavar="datastore",
                help="Datastore name")
        parser.add_argument(
                "--host", type=str,
                metavar="host",
                help="Host name (which host to place the new VMs on)")
        parser.add_argument(
                "--poweron", action="store_true",
                help="Power the cloned VMs on")
        parser.add_argument(
                "--cms", type=str,
                metavar="customization",
                help="Path to customication file")

        # nic
        parser.set_defaults(cloneArgs=["name",
            "srcSnap", "target", "snap", "diskMode",
            "cpus", "memory", "host", "datastore", "poweron", "cms",
            "extraConfig"])

    def clone(self, name=None, srcSnap=None, target=None, snap=None, diskMode=[], poweron=False,
            host=None, datastore=None, memory=None, cpus=None, cms=None, extraConfig=[]):
        # TODO: nic, extraConfig
        assert name

        regexps = [re.compile("^{}$".format(re.escape(name)))]
        fromVm = self.getRegisteredVms(regexps=regexps)[0]

        pool = None
        if host:
            (pool, host) = self.getPoolHostByHostname(host)
            assert pool is not None
            assert host is not None

        # fix newint class
        cpus = self._toNativeInt(cpus)
        memory = self._toNativeInt(memory)

        if datastore:
            datastore = self.getDatastoreByName(datastore)
            assert datastore is not None

        # find snapshot to clone from
        fromSnapshot = None
        for root, tree in self._walkVmSnapshots(fromVm):
            if not srcSnap:
                # find latest snapshot
                fromSnapshot = tree.snapshot
            elif srcSnap == tree.name:
                fromSnapshot = tree.snapshot
                break
        if snap and not fromSnapshot:
            raise LookupError("Snapshot '{}' not found".format(snap))

        assert not fromSnapshot or isinstance(fromSnapshot, vim.vm.Snapshot)
        # evaluate disko mode
        linkAll = False
        linkedDisks = []
        assertDiskModeLen0 = True
        if None in diskMode:
            linkAll = False
            diskMode.remove(None)
        elif "all" in diskMode:
            linkAll = True
            diskMode.remove("all")
        else:
            assertDiskModeLen0 = False

        if assertDiskModeLen0 and len(diskMode) != 0:
            raise RuntimeError("Disk mode must have all | none | [disk1, disk2, ...]")

        # walk disk mode
        for x in diskMode:
            linkedDisks.append(x)

        if fromVm.config.template and diskMode:
            raise RuntimeError("Template can not be linked")

        diskLocator = []
        DISK = vim.vm.device.VirtualDisk
        for (ctrlNr, slotNr, disk) in VirtualMachineDiskLayout(fromVm):
            if not isinstance(disk, DISK):
                # skip cdroms
                continue
            diskMoveType = "moveAllDiskBackingsAndDisallowSharing"
            key = (ctrlNr, slotNr)
            if linkAll or key in linkedDisks:
                try:
                    linkedDisks.remove(key)
                except ValueError:
                    pass
                diskMoveType = "createNewChildDiskBacking"
            locator = {"datastore": disk.backing.datastore,
                    "diskId": disk.key,
                    "diskMoveType": diskMoveType}
            diskLocator.append(locator)

        if linkedDisks:
            raise LookupError("Not all disk to be linked where found, missing: '{}'".format(
                repr(linkedDisks)))

        relocationSpec = vim.vm.RelocateSpec()
        relocationSpec.disk = list(map(lambda kwargs: vim.vm.RelocateSpec.DiskLocator(**kwargs),
                diskLocator))
        if pool:
            relocationSpec.pool = pool
        if host:
            relocationSpec.host = host
        if datastore:
            relocationSpec.datastore = datastore

        configSpec = vim.vm.ConfigSpec()
        if memory:
            configSpec.memoryMB = memory
        if cpus:
            configSpec.numCPUs = cpus
            # cores per socket (number of cpus per socket!!!)
            configSpec.numCoresPerSocket = cpus
        self._configSpecAddExtraConfig(configSpec, extraConfig)

        folder = fromVm.parent
        if not folder:
            datacenter = self.getDatacenters().keys()[0]
            folder = dc.vmFoler.childEntity[0]

        cloneSpec = vim.vm.CloneSpec()
        cloneSpec.powerOn = poweron
        cloneSpec.template = False
        cloneSpec.location = relocationSpec
        cloneSpec.config = configSpec
        if fromSnapshot:
            cloneSpec.snapshot = fromSnapshot
        if cms:
            cloneSpec.customization = self.getCSMByName(csm)

        rc = 0
        for toName in target:
            self.logger.info("Cloning {} -> {}".format(fromVm.name, target))
            task = fromVm.Clone(name=toName, folder=folder, spec=cloneSpec)
            vcTask = VcTask(task)
            vcTask.waitTaskDone()
            if vcTask.isSuccess():
                self.logger.info("Success")
            else:
                msg = vcTask.error()
                self.logger.error("Failed {}".format(repr(msg)))
                rc = 2
                continue
            if snap:
                try:
                    self.snapshot(toName, snap)
                except RuntimeError:
                    rc = 3
            if poweron:
                self.power([toName], on=True)

        if rc:
            raise RuntimeError("Clone failed")
        return rc

