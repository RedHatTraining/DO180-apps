# -*- coding: utf-8 -*-

__version__ = '1.0.0'

# makes all the functions available at `string_utils` level
# as they were in older versions (before 1.0.0) when it was a single python module
from .validation import *
from .manipulation import *
from .generation import *
