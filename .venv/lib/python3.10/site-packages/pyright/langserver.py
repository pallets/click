from __future__ import annotations

import sys
import subprocess
from typing import Any, NoReturn

from . import node
from ._utils import install_pyright


def main(*args: str, **kwargs: Any) -> int:
    return run(*args, **kwargs).returncode


def run(
    *args: str,
    **kwargs: Any,
) -> subprocess.CompletedProcess[bytes] | subprocess.CompletedProcess[str]:
    pkg_dir = install_pyright(args, quiet=True)
    binary = pkg_dir / 'langserver.index.js'
    if not binary.exists():
        raise RuntimeError(f'Expected language server entrypoint: {binary} to exist')

    # TODO: remove `--`?
    return node.run('node', str(binary), '--', *args, **kwargs)


def entrypoint() -> NoReturn:
    sys.exit(main(*sys.argv[1:]))


if __name__ == '__main__':
    entrypoint()
