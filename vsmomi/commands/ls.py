# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
        print_function, unicode_literals)

from builtins import *
from future.builtins.disabled import *

import re

from ._common import *

class Ls(SubCommand):
    def __init__(self, *args, **kwargs):
        super(Ls, self).__init__(*args, **kwargs)

    @classmethod
    def addParser(cls, cmdLineParser, subparsers):
        parser = cmdLineParser.getSubParser(
                "ls", subparsers,
                help="List VMs")
        parser.add_argument(
                "patterns", nargs="*", type=cmdLineParser.patternToRegexp,
                metavar="pattern",
                help="VM Patterns to list, start with ~ for regexp")
        group = parser.add_mutually_exclusive_group()
        group.add_argument(
                "-l", action="store_true", dest="longList",
                help="List extended.")
        group.add_argument(
                "-s", action="store_true", dest="shortList",
                help="List only names.")
        parser.set_defaults(lsArgs=["patterns", "shortList", "longList"])

    @export
    def ls(self, patterns=None, longList=False, shortList=False):
        self._checkPatternType(patterns)
        self._checkType(longList, bool)
        self._checkType(shortList, bool)

        maxNameLength = 30
        printHdr = True
        hdrTmpl = CT.compile(
""" \
#for $name, $v in $ns.items()
<%="{:30} | {:>5} | {:>5} | {:>6} | {:15} | {:12}".format(
    name, v["power"], v["numCPUs"], v["memorySizeMB"], v["ipAddress"], v["toolsStatus"])%> \
#end for \
""")
        rowTmpl = CT.compile(
""" \
#for $name, $v in $ns.items()
<%="{:30} | {:5} | {:>5} | {:>6} | {:>15} | {:12}".format(
    name, v["power"], v["numCPUs"], v["memorySizeMB"], v["ipAddress"], v["toolsStatus"])%> \
#end for \
""")
        rowShortTmpl = CT.compile(
""" \
#for $name, $v in $ns.items()
<%="{:30}".format(
    name)%> \
#end for \
""")
        rowLongTmpl = CT.compile(
''' \
#for $name, $v in $ns.items()
<%= """{:30}
    Power:  {}
    CPUs:   {}
    Memory: {}
    IP:     {}
    Tools:  {}
    Host:   {}""".format(name+":",
    v["power"], v["numCPUs"], v["memorySizeMB"], v["ipAddress"], v["toolsStatus"], v["host"])%> \
#if $v["networks"]
    Networks:
#for $network in $v["networks"]
<%= """        {}""".format(network) %>
#end for
#end if \

#if $v["macAddresses"]
    Mac Addresses:
#for $mac in $v["macAddresses"]
<%= """        {}""".format(mac) %> \
#end for
#end if \

#if $v.disks
    Disks:
#for $disk in $v.disks
<%= """        {:02}-{:02}: {}""".format(
    disk["controllerNumber"], disk["slotNumber"], disk["label"]) %>
#for $fi in $disk.files
<%= "            Path: {}".format(fi["path"]) +
"\\n                UUID:    {}".format(fi["uuid"]) +
"\\n                DeltaTo: {}".format(fi["deltaTo"]) %>
#end for
#end for
#end if \

#if $v.cdroms
    CDROMs:
#for $cdrom in $v.cdroms
<%= """        {:02}-{:02}: {}""".format(
    cdrom["controllerNumber"], cdrom["slotNumber"], cdrom["label"]) %>
#for $fi in $cdrom.files
<%= "            Path: {}".format(fi["path"]) %>
#end for
#end for
#end if \

#if $v.snapshots
    Snapshots: $v.snapshots
#end if \

#end for \
''')
        if longList:
            rowTmpl = rowLongTmpl
            printHdr = False
        elif shortList:
            rowTmpl = rowShortTmpl
            printHdr = False

        vms = self.getRegisteredVms(regexps=patterns, sort=False, asDict=True)
        # name, power, cpus, memory, ip, tools
        if printHdr:
            hdrData= {"Name": {"power": "Power", "numCPUs": "CPUs", "memorySizeMB": "Memory",
                    "ipAddress": "IP", "toolsStatus": "Tools"}}
            self.output(hdrData, json=False, tmpl=hdrTmpl)
        for vmName, vm in sorted(vms.items(), key=lambda x: x[0]):
            data = {vmName: {}}
            if not shortList:
                standardData = self._lsStandard(vm)
                data[vmName].update(standardData)

            if longList:
                extendedData = self._lsExtended(vm)
                data[vmName].update(extendedData)

            self.output(data, tmpl=rowTmpl)

        return 0

    def _lsStandard(self, vm):
        summary = vm.summary
        guest = summary.guest
        config = summary.config
        runtime = summary.runtime

        power = runtime.powerState
        if power.lower().startswith("powered"):
            power = power[7:]
        cpus = config.numCpu
        memory = config.memorySizeMB
        ip = guest.ipAddress
        if not ip:
            ip = "-"
        tools = guest.toolsStatus
        if not tools:
            tools = "-"
        # strip tools
        if tools.lower().startswith("tools"):
            tools = tools[5:]

        return {"power": power, "numCPUs": cpus, "memorySizeMB": memory,
                "ipAddress": ip, "toolsStatus": tools}

    def _lsExtended(self, vm):
        CDROM = vim.vm.device.VirtualCdrom
        host = vm.runtime.host
        if host:
            host = host.name
        nics = self._getVmNics(vm)
        macs = list(map(lambda nic: nic.macAddress, nics))
        networks = list(map(lambda nic: nic.backing.deviceName, nics))
        layout = VirtualMachineDiskLayout(vm)
        disks = []
        cdroms = []
        for (ctrlNr, slotNr, disk) in layout:
            isCdrom = isinstance(disk, CDROM)
            label = disk.deviceInfo.label
            backing = disk.backing
            # walk throught backing
            fileList = []  # {"path": ..., "uuid": ..., "deltaTo": ...}
            while backing and hasattr(backing, "fileName"):
                delta = None
                uuid = None
                if hasattr(backing, "uuid"):
                    uuid = backing.uuid
                fileName = backing.fileName
                # is the backing linked to another vm
                if not isCdrom:
                    delta = re.sub("^[^\s]+\s+([^/]+)/.*$", "\g<1>", fileName)
                fileList.append({"path": fileName, "uuid": uuid, "deltaTo": delta})
                if not hasattr(backing, "parent"):
                    # may happen with cdrom
                    break
                backing = backing.parent
            diskData = {"label": label, "controllerNumber": ctrlNr,
                    "slotNumber": slotNr, "files": fileList}
            if isCdrom:
                cdroms.append(diskData)
            else:
                disks.append(diskData)

        snapshots = {}  # name: [children]
        for root, snap in self._walkVmSnapshots(vm):
            snapshot = snapshots
            for psnap in root:
                name = psnap.name
                if name not in snapshot:
                    snapshot[name] = {}
                snapshot = snapshot[name]
            snapshot[snap.name] = {}
        extendedData = {"macAddresses": macs, "networks": networks,
                "cdroms": cdroms, "disks": disks, "snapshots": snapshots, "host": host}
        return extendedData

