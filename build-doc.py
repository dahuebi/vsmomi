#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division,
        print_function, unicode_literals)

from builtins import *
from future.builtins.disabled import *

import sys
import os
import re
import glob
import shutil
from subprocess import check_call

def docpy():
    docbld = "doc-py"
    docsrc = "doc"
    docgen = os.path.join(docsrc, "_gen")
    check_call(["pip", "install", "--requirement", "doc-requirements.txt"])

    dirs = ["vsmomi"]

    try:
        shutil.rmtree(docgen)
    except OSError:
        pass
    for module in dirs:
        check_call(["sphinx-apidoc",
                "--separate",
                "--force",
                "--private",
                "--module-first",
                "--output-dir", docgen,
                module])

    with open(os.path.join(docgen, "modules.rst"), "wb") as fp:
        fp.write("""

.. toctree::
   :maxdepth: 4

""")
        for module in dirs:
            fp.write("   %s.rst\n" % (module))
    try:
        shutil.rmtree(docbld)
    except OSError:
        pass
    check_call(["sphinx-build", "-T", "-W", "-b", "html", docsrc, docbld])

def main():
    docpy()

if __name__ == "__main__":
    main()
