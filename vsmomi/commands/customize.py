# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
        print_function, unicode_literals)

from builtins import *
from future.builtins.disabled import *

import re

from ._common import *

class Customize(SubCommand):
    def __init__(self, *args, **kwargs):
        super(Customize, self).__init__(*args, **kwargs)

    @classmethod
    def addParser(self, cmdLineParser, subparsers):
        parser = cmdLineParser.getSubParser(
                "customize", subparsers,
                help="Customize VMs")
        parser.add_argument(
                "name",
                metavar="name",
                help="VM to clone from")
        parser.add_argument(
                "--csm", type=str,
                metavar="customization",
                help="Path to customication file")
        parser.add_argument(
                "--nic-add", nargs="+",
                default=[], type=cmdLineParser.nicAddType,
                metavar="<nic-add>",
                dest="nicAdd",
                help="Customize network interfaces.\n" \
                "[mac=,ip=x.x.x.x/mask,gw=]")

        parser.set_defaults(cloneArgs=["name", "csm", "nicAdd"])

    @export
    def customize(self, name=None, csm=None, nicAdd=[]):
        self._checkType(name, (str, vim.VirtualMachine))
        self._checkType(csm, (str, type(None)))
        self._checkType(nicAdd, list)
        for nc in nicAdd:
            assert "map" in nc
            assert "ip" in nc
            assert "mask" in nc
            assert "gw" in nc
            self._checkType(nc["map"], str)
            self._checkType(nc["ip"], str)
            self._checkType(nc["mask"], int)
            self._checkType(nc["gw"], str)


        regexps = [re.compile("^{}$".format(re.escape(name)))]
        vm = self.getRegisteredVms(regexps=regexps)[0]
        customSpec = vim.vm.customization.Specification()
        if csm:
            customSpec = self.getCSMByName(csm)

        for nicDesc in nicAdd:
            mac = nicDesc["map"]
            ip = nicDesc["ip"]
            mask = nicDesc["mask"]
            gw = nicDesc["gw"]
            adapterMap = vim.vm.customization.AdapterMapping()
            if mac:
                adapterMap.macAddress = mac
            if not ip:
                adapterMap.ip = vim.vm.customization.DhcpIpGenerator()
            else:
                adapterMap.ip = vim.vm.customization.FixedIp(ipAddress=ip)
                if mask:
                    adapterMap.subnetMask = mask
                if gw:
                    adapterMap.gateway = gw
                # adapterMap.dnsDomain
            csm.nicSettingsMap.append(adapterMap)
        # hostname/domain
        # ident = vim.vm.customization.LinuxPrep(hostName=hostname, domain=domain)
        # customSpec.identity = ident
        # windows ???

        # dnsServerList, dnsSuffixList
        # globalIPSettings = vim.vm.customization.GlobalIPSettings(dnsServerList=dnsServerList,
        #           dnsSuffixList=dnsSuffixList)
        # customSpec.globalIPSettings = globalIPSettings

        task = vm.CustomizeVM(customSpec)
        vcTask = VcTask(task)
        vcTask.waitTaskDone()
        if vcTask.isSuccess():
            self.logger.info("Success")
        else:
            msg = vcTask.error()
            self.logger.error("Failed {}".format(repr(msg)))
            raise RuntimeError("CMS failed")

        return 0

