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
                "--snap", type=str,
                metavar="<source snapshot>",
                dest="srcSnap",
                help="Snapshot to clone from, default is latest")
        parser.add_argument(
                "--target", nargs="+", required=True,
                metavar="target",
                help="List of target VMs to create")
        parser.add_argument(
                "--disk-mode", nargs="+", type=cmdLineParser.diskModeType,
                default=["all"],
                metavar="<disk-mode>", dest="diskMode",
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
                metavar="key=value",
                dest="extraConfig",
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
                "--csm", type=str,
                metavar="customization",
                help="Path to customication file")

        parser.set_defaults(cloneArgs=["name",
            "srcSnap", "target", "diskMode",
            "cpus", "memory", "host", "datastore", "poweron", "csm",
            "extraConfig"])

    @export
    def clone(self, name=None, srcSnap=None, target=None, diskMode=[], poweron=False,
            host=None, datastore=None, memory=None, cpus=None, csm=None, extraConfig=[]):
        self._checkType(name, (str, vim.VirtualMachine))
        self._checkType(srcSnap, (type(None), str))
        self._checkType(target, list)
        [self._checkType(x, str) for x in target]
        self._checkType(diskMode, list)
        for dm in diskMode:
            if isinstance(dm, tuple):
                [self._checkType(x, int) for x in dm]
                assert len(dm) == 2
            else:
                self._checkType(dm, (str, type(None)))
        self._checkType(poweron, bool)
        self._checkType(host, (type(None), str))
        self._checkType(datastore, (type(None), str))
        self._checkType(memory, (type(None), int))
        self._checkType(cpus, (type(None), int))
        self._checkType(csm, (type(None), str))
        self._checkType(extraConfig, list)
        for ec in extraConfig:
            self._checkType(ec, tuple)
            [self._checkType(x, str) for x in ec]
            assert len(ec) == 2

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
        if srcSnap and not fromSnapshot:
            raise LookupError("Snapshot '{}' not found".format(srcSnap))

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

        if (linkedDisks or linkAll) and not fromSnapshot:
            raise RuntimeError("Linking disk but no snapshot exist.")

        diskLocator = []
        DISK = vim.vm.device.VirtualDisk
        fromVmDisks = fromVm
        if fromSnapshot:
            fromVmDisks = fromSnapshot
        for (ctrlNr, slotNr, disk) in VirtualMachineDiskLayout(fromVmDisks):
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
        if csm:
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

        if rc:
            raise RuntimeError("Clone failed")
        return rc

