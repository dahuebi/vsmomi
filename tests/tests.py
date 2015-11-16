#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
        print_function, unicode_literals)

from builtins import *
from future.builtins.disabled import *

import os

import vsmomi
from vsmomi import DryrunError

try:
    import unittest2 as unittest
except ImportError:
    import unittest

class TestVmomi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = vsmomi.CommandLineParser()

    testArgs = [
["ls"],
["ls", "vm"],
["ls", "vm", "~vm2"],
["ls", "-l"],
["ls", "-s"],
["power", "vm", "--on"],
["power", "vm", "--off"],
["power", "vm", "--reset"],
["power", "vm", "--shutdown"],
["power", "vm", "--halt"],
["power", "vm", "--reboot"],
["destroy", "vm"],
["destroy", "vm", "~vm2"],
["clone", "vm", "--target=toVm"],
["clone", "vm", "--target=toVm", "--snap=snap"],
["clone", "vm", "--target=toVm", "--disk-mode=all"],
["clone", "vm", "--target=toVm", "--disk-mode=none"],
["clone", "vm", "--target=toVm", "--disk-mode", "0-1", "2-2"],
["clone", "vm", "--target=toVm", "--cpus=8"],
["clone", "vm", "--target=toVm", "--mem=1024"],
["clone", "vm", "--target=toVm", "--extra-config", "a=b", "c=d"],
["clone", "vm", "--target=toVm", "--datastore=ds"],
["clone", "vm", "--target=toVm", "--poweron"],
["clone", "vm", "--target=toVm", "--host=host1"],
["clone", "vm", "--target=toVm", "--cms=custom"],
["edit", "vm"],
["edit", "vm", "--cpus=4"],
["edit", "vm", "--mem=256"],
["edit", "vm", "--extra-config", "d=e", "asdf=1234"],
["edit", "vm", "--network=net"],
["edit", "vm", "--iso=[ds] path"],
["edit", "vm", "--disk-new", "size=12341234"],
["edit", "vm", "--disk-new", "size=20G"],
["edit", "vm", "--disk-new", "3-1,size=20G"],
["edit", "vm", "--disk-link", "vm,0-1"],
["edit", "vm", "--disk-link", "0-4,vm,0-1"],
["edit", "vm", "--disk-destroy", "0-0", "0-1"],
["guest-upload", "vm", "--guest-user=user", "--guest-pass=pass", "--files", __file__, __file__, "--guest-dir=/"],
["guest-download", "vm", "--guest-user=user", "--guest-pass=pass", "--files", "f1", "f2", "--host-dir", os.getcwd()],
["guest-delete", "vm", "--guest-user=user", "--guest-pass=pass", "--files", "f1", "f2"],
["guest-execute", "vm", "--guest-user=user", "--guest-pass=pass", "--cmd", "cmd"],
["guest-execute", "vm", "--guest-user=user", "--guest-pass=pass", "--cmd", "bash -c exit 1", "sdlfkj", "-a"],
]

    def testParserArgs(self):
        for args in self.testArgs:
            try:
                which, _, _ = self.parser.parse(args)
                #self.assertEqual(args[0], which)
            except SystemExit:
                assert False, args

    def testAppDryrun(self):
        for args in self.testArgs:
            try:
                with self.assertRaises(DryrunError):
                    vsmomi.main(["--dryrun"] + args)
            except SystemExit:
                assert False, args

if __name__ == "__main__":
    unittest.main()

