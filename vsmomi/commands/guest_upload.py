# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
        print_function, unicode_literals)

from builtins import *
from future.builtins.disabled import *

import re
import os

from ._guest_common import *

class GuestUpload(GuestCommand):
    def __init__(self, *args, **kwargs):
        super(GuestUpload, self).__init__(*args, **kwargs)

    @classmethod
    def addParser(cls, cmdLineParser, subparsers):
        parser = cmdLineParser.getSubParser(
                "guest-upload", subparsers,
                help="Upload to VMs")
        commonArgs = cls._addCommonArgs(cmdLineParser, parser)
        parser.add_argument(
                "--files", nargs="+", required=True,
                metavar="file",
                help="Files to upload")
        parser.add_argument(
                "--guest-dir", type=str,
                required=True,
                metavar="guest-dir",
                dest="guestDir",
                help="Guest upload directory, will be created.")
        parser.set_defaults(guestUploadArgs=commonArgs +
                ["files", "guestDir"])

    @export
    def guestUpload(self, files=[], guestDir=None, **kwargs):
        self._checkType(files, list)
        [self._checkType(x, str) for x in files]
        self._checkType(guestDir, str)

        tmpl = CT.compile(
""" \
#for name, v in $ns.items()
<%="{} -> {} {}".format(v["uploadFile"], name, v["guestFilePath"])%> \
#end for \
""")
        uploadFiles, vmUploadDir = files, guestDir
        rc = 0
        for uploadFile in uploadFiles:
            if not os.path.exists(uploadFile):
                raise LookupError("File not found {}.".format(uploadFile))
        auth, vms = self._guestCommon(**kwargs)
        content = self.content()
        fm = content.guestOperationsManager.fileManager
        fileAttributes = vim.vm.guest.FileManager.FileAttributes()
        for vm in vms:
            vmName = vm.name
            if not self._guestCheckTools(vm, auth):
                self.logger.error("VMTools not OK: {}".format(vmName))
                rc = 1
                continue
            (sep, pathsep) = self.getGuestSeparators(vm)
            uploadDir = self.toGuestPath(sep, vmUploadDir)
            uploadDir = uploadDir.rstrip(sep)
            for uploadFile in uploadFiles:
                guestFilePath = "{}{}{}".format(
                        uploadDir, sep, os.path.basename(uploadFile))
                fileSize = os.stat(uploadFile).st_size
                try:
                    fm.MakeDirectoryInGuest(vm=vm, auth=auth,
                            directoryPath=uploadDir,
                            createParentDirectories=True)
                except vim.fault.FileAlreadyExists:
                    pass
                url = fm.InitiateFileTransferToGuest(vm=vm, auth=auth,
                        guestFilePath=guestFilePath, fileAttributes=fileAttributes,
                        fileSize=fileSize, overwrite=True)
                with open(uploadFile, "rb") as fp:
                    resp = requests.put(url, data=fp, verify=False)
                msg = "{} -> {} {}".format(
                        uploadFile, vmName, guestFilePath)
                data = {vmName: {"uploadFile": uploadFile, "guestFilePath": guestFilePath,
                        "success": resp.status_code == 200}}
                if resp.status_code == 200:
                    self.output(data, tmpl=tmpl)
                else:
                    self.output(data, tmpl=tmpl, level=logging.ERROR)
                    rc = 1
        if rc:
            raise RuntimeError("Upload failed")

