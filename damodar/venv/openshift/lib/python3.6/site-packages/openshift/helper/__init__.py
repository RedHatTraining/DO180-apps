# -*- coding: utf-8 -*-
from __future__ import absolute_import

import re

PRIMITIVES = ('str', 'int', 'bool', 'float', 'object')
VERSION_RX = re.compile(".*V\d((alpha|beta)\d)?")
