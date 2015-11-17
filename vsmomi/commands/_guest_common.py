# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
        print_function, unicode_literals)

from builtins import *
from future.builtins.disabled import *

import re
import os
import datetime

from future.standard_library import install_aliases
install_aliases()
from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import requests

from ._common import *

class GuestCommand(SubCommand):
    def __init__(self, *args, **kwargs):
        super(GuestCommand, self).__init__(*args, **kwargs)

    @classmethod
    def _addCommonArgs(cls, cmdLineParser, parser):
        parser.add_argument(
                "patterns", nargs="+",
                type=cmdLineParser.patternToRegexp,
                metavar="pattern",
                help="VMs to select")
        parser.add_argument(
                "--guest-user", type=str,
                required=True,
                metavar="user",
                dest="guestUser",
                help="Guest username")
        parser.add_argument(
                "--guest-pass", type=str,
                required=True,
                metavar="password",
                dest="guestPass",
                help="Guest password")
        return ["patterns", "guestUser", "guestPass"]

    def _getGuestAuth(self, username, password):
        return vim.vm.guest.NamePasswordAuthentication(
                username=username, password=password)

    def _guestCommon(self, patterns=["~^$"], guestUser=None, guestPass=None):
        self._checkPatternType(patterns)
        self._checkType(guestUser, str)
        self._checkType(guestPass, str)
        # convert to proper str (newstr from feature does not work)
        guestUser, guestPass = "{}".format(guestUser), "{}".format(guestPass)
        auth = self._getGuestAuth(guestUser, guestPass)
        vms = self.getRegisteredVms(regexps=patterns)
        return auth, vms

