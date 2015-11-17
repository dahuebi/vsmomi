# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
        print_function, unicode_literals)

from builtins import *
from future.builtins.disabled import *

from six import string_types

import re
import logging
import sys
import os
import base64
import configparser
import json
import pprint
import traceback

import codecs
if not sys.stdout.isatty():
    sys.stdout = codecs.getwriter('utf8')(sys.stdout)
    sys.stderr = codecs.getwriter('utf8')(sys.stderr)

from Cheetah.Template import Template as CT
from pyVmomi import vim

from .service_instance_api import ServiceInstanceAPI
from .command_line_parser import CommandLineParser

from . import commands

class Application(ServiceInstanceAPI):
    def __init__(self, *args, **kwargs):
        super(Application, self).__init__(*args, **kwargs)
        self.isM2M = False
        self.subCommands = []
        for mod in commands.commands:
            self.subCommands.append(mod(self))

    def __getattr__(self, name):
        for subCommand in self.subCommands:
            try:
                return object.__getattribute__(subCommand, name)
            except AttributeError:
                pass
        raise AttributeError("'{}' object has no attribute '{}'".format(
                type(self).__name__, name))

    def _checkType(self, param, types):
        # fix str type, user six,string_types
        _types = []
        if not isinstance(types, (tuple, list)):
            _types.append(types)
        else:
            _types += list(types)
        types = []
        for typ in _types:
            if typ is str:
                types += string_types
            else:
                types.append(typ)

        types = tuple(set(types))
        assert isinstance(param, types), "{} in {})".format(type(param), types)

    def _checkPatternType(self, patterns):
        self._checkType(patterns, list)
        [self._checkType(x, type(re.compile(""))) for x in patterns]

    @classmethod
    def convert(cls, data):
        import collections
        if isinstance(data, basestring):
            return data.encode("utf-8")
        elif isinstance(data, collections.Mapping):
            return dict(map(cls.convert, data.iteritems()))
        elif isinstance(data, collections.Iterable):
            return type(data)(map(cls.convert, data))
        else:
            return data

    def output(self, data, json=True, tmpl=None, level=logging.INFO):
        if not self.isM2M:
            s = ""
            if level != logging.INFO:
                s += "[{}] ".format(logging.getLevelName(level))
            if tmpl:
                _data = self.convert(data)
                s += str(tmpl(namespaces={"ns": _data}))
            else:
                s += pprint.pformat(data)
            self.logger.log(level, s)
        elif json:
            self.jsonObj.update(data)

    def _getVmNics(self, vm):
        NIC = vim.vm.device.VirtualEthernetCard
        devices = vm.config.hardware.device
        nics = list(filter(lambda dev: isinstance(dev, NIC), devices))
        return nics

    def _getNicMacs(self, nics):
        return list(map(lambda nic: nic.macAddress, nics))

    def _walkVmSnapshots(self, vm):
        snapshots = vm.snapshot
        if not snapshots:
            raise StopIteration()
        def walkSnapList(snapList, parents):
            for snap in snapList:
                yield parents, snap
                if snap.childSnapshotList:
                    parents.append(snap)
                    for x in walkSnapList(snap.childSnapshotList, parents):
                        yield x
                    parents.pop()

        for x in walkSnapList(snapshots.rootSnapshotList, []):
            yield x
        raise StopIteration()

    def _configSpecAddExtraConfig(self, configSpec, extraConfig=[]):
        for key, value in extraConfig:
            option = vim.option.OptionValue()
            option.key = key
            option.value = value
            configSpec.extraConfig.append(option)

    def _toNativeInt(self, number):
        if number is not None:
            return eval("{}".format(number))
        return None

    @classmethod
    def loadAuth(cls, authFile, vcenter=None):
        vcUser, vcPass = None, None
        cfg = configparser.ConfigParser()
        cfg.read(authFile)
        if not vcenter:
            vcenter = cfg.sections()[0]
        if cfg.has_section(vcenter):
            if (not cfg.has_option(vcenter, "username") or
                    not cfg.has_option(vcenter, "password")):
                raise LookupError("{} section {} has no username/password".format(
                    authFile, vcenter))
            vcUser = cfg.get(vcenter, "username")
            vcPass = cfg.get(vcenter, "password")
        return vcenter, vcUser, vcPass

    @classmethod
    def saveAuth(cls, authFile, vcenter, vcUser, vcPass):
        cfg = configparser.ConfigParser()
        with open(authFile, "a") as fp:
            cfg.readfp(fp)
            fp.seek(0)
            if not cfg.has_section(vcenter):
                cfg.add_section(vcenter)
            cfg.set(vcenter, "username", vcUser)
            cfg.set(vcenter, "password", vcPass)
            cfg.write(fp)

    @classmethod
    def loadCreds(cls, authFile, vcenter, vcUser, vcPass):
        # check environment
        if not vcenter:
            vcenter = os.environ.get("VC_VCENTER", None)
        if not vcPass:
            vcPass = os.environ.get("VC_VCPASS", None)
        if not vcUser:
            vcUser= os.environ.get("VC_VCUSER", None)
        if not authFile:
            authFile = os.environ.get("VC_AUTH", None)

        # load form auth file
        if authFile and os.path.exists(authFile) and (not vcUser or not vcPass):
            vcenter, _vcUser, _vcPass = cls.loadAuth(authFile, vcenter)
            if not vcUser:
                vcUser = _vcUser
            if not vcPass:
                vcPass = _vcPass

        if vcPass:
            try:
                _ = base64.b64decode(vcPass)
            except:
                vcPass = base64.b64encode(vcPass)

        if (not vcenter or not vcUser or not vcPass):
            raise LookupError("No vcenter/username/password")

        return vcenter, vcUser, vcPass

    @classmethod
    def main(cls, argv=sys.argv[1:]):
        which, args, parserArgs = \
                CommandLineParser().parse(argv=argv)
        if args.dryrun:
            args.vcenter = "vcenter"
            args.vcUser = "vc_user"
            args.vcPass = "vc_pass"
            args.saveAuth = False

        vcenter = args.vcenter
        vcenter, vcUser, vcPass = cls.loadCreds(args.auth,
                args.vcenter, args.vcUser, args.vcPass)

        # check credentials
        app = Application(vcenter, vcUser, vcPass, dryrun=args.dryrun)
        if args.saveAuth:
            cls.saveAuth(authFile, vcenter, vcUser, vcPass)

        rc = 24
        if args.m2m:
            rc = app.m2m(which=which, **parserArgs)
        else:
            func = getattr(app, which)
            rc = func(**parserArgs)

        if isinstance(rc, (tuple, list)):
            return rc[0]
        return rc

