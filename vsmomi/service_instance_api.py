# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
        print_function, unicode_literals)

from builtins import *
from future.builtins.disabled import *

import re
import fnmatch
import logging

from pyVmomi import vim

from ._service_instance import ServiceInstance

class DryrunError(Exception):
    pass

class ServiceInstanceAPI(object):
    def __init__(self, host, username, password, dryrun=False):
        self.logger = logging.getLogger("vc")
        self.logger.addHandler(logging.StreamHandler())
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False
        self.dryrun = dryrun
        self.si = None
        if not dryrun:
            self.si = ServiceInstance(host, username, password)
            self.si.CurrentTime()

    def content(self):
        if self.dryrun:
            raise DryrunError()
        return self.si.RetrieveContent()

    def _getObj(self, vimtype, name):
        """
        Get the vsphere object associated with a given text name
        """
        obj = None
        content = self.content()
        container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
        for c in container.view:
            if c.name == name:
                obj = c
                break
        return obj

    def _getAllObjs(self, vimtype):
        """
        Get all the vsphere objects associated with a given type
        """
        obj = {}
        content = self.content()
        container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
        for c in container.view:
            obj.update({c: c.name})
        return obj

    def getVmByName(self, name):
        """
        Find a virtual machine by it's name and return it
        """
        return self._getObj([vim.VirtualMachine], name)

    def getHostByName(self, name):
        """
        Find a virtual machine by it's name and return it
        """
        return self._getObj([vim.HostSystem], name)


    def getCSMByName(self, name):
        content = self.content()
        csm = content.customizationSpecManager
        csi = csm.GetCustomizationSpec(name)
        spec = csi.spec
        return spec

    #def getResourcePool(self, name):
    #    """
    #    Find a virtual machine by it's name and return it
    #    """
    #    return self._getObj([vim.ResourcePool], name)

    def getPoolHostByHostname(self, hostname):
        host = None
        pool = None
        pools = self.getResourcePools().keys()
        for p in pools:
            hosts = list(set([vm.runtime.host for vm in p.vm]))
            for h in hosts:
                name = h.name
                if name.lower().startswith(hostname.lower()):
                    # found resource pool
                    pool = p
                    host = h
                    break

        return (pool, host)

    def getResourcePools(self):
        """
        Returns all resource pools
        """
        return self._getAllObjs([vim.ResourcePool])

    def getDatastores(self):
        """
        Returns all datastores
        """
        return self._getAllObjs([vim.Datastore])

    def getDatastoreByName(self, name):
        datastores = self.getDatastores()
        datastore = None
        for ds in datastores:
             if ds.name.lower() == name.lower():
                datastore = ds
                break
        return datastore

    def getHosts(self):
        """
        Returns all hosts
        """
        return self._getAllObjs([vim.HostSystem])

    def getDatacenters(self):
        """
        Returns all datacenters
        """
        return self._getAllObjs([vim.Datacenter])

    def getRegisteredVms(self, regexps=[], sort=True):
        """
        Returns all vms
        """
        assert isinstance(regexps, (list, tuple))
        allVms = map(lambda vm: (vm.name, vm),
                self._getAllObjs([vim.VirtualMachine]))
        if sort and not regexps:
            regexps = [re.compile(".*")]
        vms = []
        if regexps:
            for name, vm in allVms:
                for regexp in regexps:
                    if regexp.search(name):
                        vms.append((name, vm))
                        break
        else:
            vms = list(allVms)
        if sort:
            vms = sorted(vms, key=lambda x: x[0])
        if not vms:
            raise LookupError("No VMs found")
        return list(map(lambda item: item[1], vms))

    def getNetworks(self):
        """
        Returns all networks
        """
        return self._getAllObjs([vim.Network])

