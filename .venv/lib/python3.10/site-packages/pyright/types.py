from __future__ import annotations

import sys
from typing import Any

if sys.version_info >= (3, 8):
    from typing import Literal
else:
    from typing_extensions import Literal


# we have to define twice to support runtime type checking
# on python < 3.7 as typing.get_args is not available
Target = Literal['node', 'npm']
_TARGETS = {'node', 'npm'}


def check_target(value: Any) -> None:
    """Raises a TypeError  if the value is not a valid Target."""
    if value not in _TARGETS:
        raise TypeError(f'{value} is not a valid target, expected one of {", ".join(_TARGETS)}')
