# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
        print_function, unicode_literals)

from builtins import *
from future.builtins.disabled import *

import re
import os

from ._guest_common import *

class GuestDownload(GuestCommand):
    def __init__(self, *args, **kwargs):
        super(GuestDownload, self).__init__(*args, **kwargs)

    @classmethod
    def addParser(cls, cmdLineParser, subparsers):
        parser = cmdLineParser.getSubParser(
                "guest-download", subparsers,
                help="Download from VMs")
        commonArgs = cls._addCommonArgs(cmdLineParser, parser)
        parser.add_argument(
                "--files", nargs="+", required=True,
                metavar="file",
                help="Files to upload")
        parser.add_argument(
                "--host-dir", type=str,
                default=os.getcwd(),
                metavar="host-dir",
                dest="hostDir",
                help="Host download directory, will be created.")
        parser.set_defaults(guestDownloadArgs=commonArgs +
                ["files", "hostDir"])

    def guestDownload(self, files=[], hostDir=None, **kwargs):
        assert isinstance(files, list)
        assert isinstance(hostDir, str)
        vmDownloadFiles, downloadDir = files, hostDir
        tmpl = CT.compile(
""" \
#for name, v in $ns.items()
<%="{} {} -> {}".format(name, v["guestFilePath"], v["localFile"])%> \
#end for \
""")
        rc = 0
        try:
            os.makedirs(downloadDir)
        except OSError:
            pass
        auth, vms = self._guestCommon(**kwargs)
        content = self.content()
        fm = content.guestOperationsManager.fileManager
        for vm in vms:
            vmName = vm.name
            if vm.guest.toolsStatus != "toolsOk":
                self.logger.error("VMTools not OK: {}".format(vmName))
                rc = 1
                continue
            guestId = vm.summary.config.guestId
            sep = "/"
            if guestId.lower().startswith("win"):
                sep = r"\\"

            for downloadFile in vmDownloadFiles:
                guestFilePath = re.sub(r"[\\/]", sep, downloadFile)
                fti = fm.InitiateFileTransferFromGuest(vm=vm, auth=auth,
                        guestFilePath=guestFilePath)
                fileAttributes = fti.attributes
                mtime = fileAttributes.modificationTime
                utcNaive = mtime.replace(tzinfo=None) - mtime.utcoffset()
                ts = timestamp = (utcNaive - datetime.datetime(1970, 1, 1)).total_seconds()
                url = fti.url
                resp = requests.get(url, verify=False)
                name = re.sub(r".*[\\/]", "", downloadFile)
                dstFile = os.path.join(downloadDir, name)
                data = {vmName: {"guestFilePath": guestFilePath, "localFile": dstFile,
                        "success": resp.status_code == 200}}
                if resp.status_code == 200:
                    with open(dstFile, "wb") as fp:
                        fp.write(resp.content)
                    os.utime(dstFile, (ts, ts))
                    self.output(data, tmpl=tmpl)
                else:
                    self.output(data, tmpl=tmpl, level=logging.ERROR)
                    rc = 1
        if rc:
            raise RuntimeError("Upload failed")

