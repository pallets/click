# -*- coding: utf-8 -*-
# pyright: reportUnusedImport=false

__title__ = 'pyright'
__author__ = 'RobertCraigie'
__license__ = 'MIT'
__copyright__ = 'Copyright 2021 Robert Craigie'

import os

from . import errors as errors
from .cli import *
from ._version import (
    __version__ as __version__,
    __pyright_version__ as __pyright_version__,
)

if os.environ.get('PYRIGHT_PYTHON_DEBUG'):
    import logging

    logging.basicConfig(format='%(asctime)-15s - %(levelname)s - %(name)s - %(message)s')
    logging.getLogger('pyright').setLevel(logging.DEBUG)
