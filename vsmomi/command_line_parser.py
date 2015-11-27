# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
        print_function, unicode_literals)

from builtins import *
from future.builtins.disabled import *

import sys
import fnmatch
import re
import os
import argparse
from argparse import ArgumentTypeError

from . import commands

class CommandLineParser(object):
    def __init__(self):
        self.initParser()

    def toNumber(self, value):
        number = value
        try:
            number = int(value)
            # need native int not newint
            number = eval("{}".format(number))
        except (TypeError, ValueError):
            pass
        return number

    def unitToFactor(self, unit):
        units = {
            "k": 1024,
            "m": 1024*1024,
            "g": 1024*1024*1024,
            "t": 1024*1024*1024*1024,
        }
        factor = 1
        try:
            if unit:
                factor = units[unit[0].lower()]
        except KeyError:
            raise KeyError("Unsupported unit '{}'".format(unit))
        return factor

    def patternToRegexp(self, pattern):
        regexp = None
        if pattern.startswith("~"):
            regexp = re.compile(pattern[1:])
        else:
            pattern = fnmatch.translate(pattern)
            regexp = re.compile("^"+pattern)
        return regexp

    def diskModeType(self, s):
        fmt = "all | none | <ctrlNr>-<slotNr> [<ctrlNr>-<slotNr>]"
        s = s.lower()
        if s == "all":
            return s
        elif s == "none":
            return None
        pattern = "^(\d+)-(\d+)$"
        match = self.matchPattern(pattern, fmt, s)
        n, m = (self.toNumber(x) for x in match.groups())
        return (n, m)

    def memoryType(self, s):
        fmt = "<number>[m|g]"
        pattern = "^(\d+)(?([m|g].?))$"
        pattern = "^([\d.]+)(:?([m|M|g|G]).?)$"
        match = self.matchPattern(pattern, fmt, s)
        mem, unit = match.groups()
        factor = self.unitToFactor(unit)
        if factor == 1:
            factor = 1024
        mem = float(mem)
        mem = factor * mem
        return int(mem)

    def extraConfigType(self, s):
        fmt = "<key>=<value>"
        pattern = "^([^=]+)=(.*)$"
        match = self.matchPattern(pattern, fmt, s)
        key, value = match.groups()
        return (key, value)

    def isoType(self, s):
        fmt = "\[datastore\] <path>"
        pattern = "^\[[^\]]+\]\s.*$"
        match = self.matchPattern(pattern, fmt, s)
        return s

    def diskLinkedType(self, s):
        fmt = "[<ctrlNr>-<slotNr>,]vm[:snapshot],<ctrlNr>-<slotNr>"
        pattern = "^(?:(\d+)-(\d+),)?([^:,]+)(?::([^,]+))?(?:,(\d+)-(\d+))$"
        match = self.matchPattern(pattern, fmt, s)
        n, m, vm, snapshot, x, y = (self.toNumber(x) for x in match.groups())
        return {"slot": (n, m), "vm": (vm, snapshot), "vmSlot": (x, y)}

    def diskNewType(self, s):
        fmt = "[<ctrlNr>-<slotNr>,]size=<capacity>[mb|gb|tb]"
        pattern = "^(?:(\d+)-(\d+),)?size=(\d+)([m|M|g|G|t|T].?)?$"
        match = self.matchPattern(pattern, fmt, s)
        n, m, size, unit = (self.toNumber(x) for x in match.groups())
        factor = self.unitToFactor(unit)
        size = factor * size
        return {"slot": (n, m), "capacity": size}

    def diskDestroyType(self, s):
        fmt = "<ctrlNr>-<slotNr>"
        pattern = "^(\d+)-(\d+)$"
        match = self.matchPattern(pattern, fmt, s)
        n, m = (self.toNumber(x) for x in match.groups())
        return (n, m)

    def nicAddType(self, s):
        fmt = "[mac=xx:xx:xx:xx:xx:xx,ip=a.b.c.d/8,gw=u,v,w,x]"
        macPattern = "[.:]".join(["[0-9A-F]{2}"] * 6)
        ipPattern = "\.".join(["\d+"] * 4)
        pattern = "^(?:mac=({0}),?)?(?:ip=({1})(?:/(\d+))?,?)?(?:gw=({1}),?)?$".format(
                macPattern, ipPattern)
        match = self.matchPattern(pattern, fmt, s)
        mac, ip, mask, gw = match.groups()
        return {"mac": mac, "ip": ip, "mask": mask, "gw": gw}

    def matchPattern(self, pattern, fmt, s):
        reg = re.compile(pattern, re.I)
        match = reg.search(s)
        if not match:
            raise argparse.ArgumentTypeError(
                    "'{}' does not match format'{}'".format(s, fmt))
        return match

    def getSubParser(self, function, subparsers, **kwargs):
        parser = subparsers.add_parser(
                function,
                formatter_class=argparse.RawTextHelpFormatter,
                **kwargs)
        return parser

    def initParser(self):
        parser = argparse.ArgumentParser(
                formatter_class=argparse.RawTextHelpFormatter)
        self.parser = parser
        parser.add_argument(
                "--dryrun", action="store_true",
                help=argparse.SUPPRESS)
        parser.add_argument(
                "--vcenter",
                type=str,
                metavar="host",
                help="Hostname/IP of the VCenter")
        parser.add_argument(
                "--vc-user",
                type=str,
                metavar="user", dest="vcUser",
                help="VCenter username")
        parser.add_argument(
                "--vc-pass",
                type=str,
                metavar="password", dest="vcPass",
                help="VCenter password, may be base64 encoded")
        parser.add_argument(
                "--auth",
                type=str,
                default="auth.ini",
                metavar="auth.ini",
                help="Load credentials from auth file")
        parser.add_argument(
                "--save-auth",
                action="store_true", dest="saveAuth",
                help="Save/update auth file")
        parser.add_argument(
                "--ask-cred", action="store_true", dest="askCred",
                help="Force user to enter credentials")
        subparsers = parser.add_subparsers(dest="which")
        subparsers.required = True
        for mod in commands.commands:
            mod.addParser(self, subparsers)

    def _currentParserArgs(self, args):
        which = args.which
        keys = getattr(args, "{}Args".format(which))
        parserArgs = {}
        for k, v in vars(args).items():
            if k in keys:
                parserArgs[k] = v
        return parserArgs

    def showFullHelp(self):
        # http://stackoverflow.com/questions/20094215/argparse-subparser-monolithic-help-output
        parser = self.parser
        # print main help
        print(parser.format_help())
        # retrieve subparsers from parser
        subparsers_actions = [
            action for action in parser._actions 
            if isinstance(action, argparse._SubParsersAction)]
        # there will probably only be one subparser_action,
        # but better save than sorry
        for subparsers_action in subparsers_actions:
            # get all subparsers and print help
            for choice, subparser in subparsers_action.choices.items():
                print("--------------------------------------------------------------------------------")
                print("Command '{}'".format(choice))
                print(subparser.format_help())

    def parse(self, argv=sys.argv[1:]):
        args, nestedArgv = self.parser.parse_known_args(argv)
        args.m2m = False
        if args.which == "m2m":
            args.m2m = True
            if not nestedArgv or nestedArgv[0] == "-":
                # read json args from stdin
                raise NotImplementedError()
            else:
                self.parser.parse_args(nestedArgv, namespace=args)
        else:
            self.parser.parse_args(argv, namespace=args)
        # camelCase, remove unwanted characters
        which = args.which
        which = which.title()
        which = re.sub("-", "", which)
        which = which[0].lower() + which[1:]
        args.which = which
        parserArgs = self._currentParserArgs(args)
        return which, args, parserArgs

