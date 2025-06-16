import sys
import logging
import subprocess
from typing import Any, List, Union, NoReturn

from . import node
from ._utils import install_pyright

__all__ = (
    'run',
    'main',
)

log: logging.Logger = logging.getLogger(__name__)


def main(args: List[str], **kwargs: Any) -> int:
    return run(*args, **kwargs).returncode


def run(*args: str, **kwargs: Any) -> Union['subprocess.CompletedProcess[bytes]', 'subprocess.CompletedProcess[str]']:
    pkg_dir = install_pyright(args, quiet=None)
    script = pkg_dir / 'index.js'
    if not script.exists():
        raise RuntimeError(f'Expected CLI entrypoint: {script} to exist')

    return node.run('node', str(script), *args, **kwargs)


def entrypoint() -> NoReturn:
    sys.exit(main(sys.argv[1:]))
