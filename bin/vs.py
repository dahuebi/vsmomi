#!/usr/bin/env python

import sys
import os
__file__ = os.path.abspath(__file__)
__scriptdir__ = os.path.dirname(__file__)
sys.path.insert(0, os.path.dirname(__scriptdir__))
import vsmomi

sys.exit(vsmomi.main())
