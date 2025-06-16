from __future__ import annotations

import os
import sys
import json
import logging
import subprocess
from typing import Any
from pathlib import Path

from . import node, _mureq as mureq
from .utils import env_to_bool, get_cache_dir, get_latest_version
from ._version import __version__, __pyright_version__

ROOT_CACHE_DIR = get_cache_dir() / 'pyright-python'
DEFAULT_PACKAGE_JSON: dict[str, Any] = {
    'name': 'pyright-binaries',
    'version': '1.0.0',
    'private': True,
    'description': 'Cache directory created by Pyright Python to store downloads of the NPM package',
    'main': 'node_modules/pyright/index.js',
    'author': 'RobertCraigie',
    'license': 'Apache-2.0',
}
log: logging.Logger = logging.getLogger(__name__)


def install_pyright(args: tuple[object, ...], *, quiet: bool | None) -> Path:
    """Internal helper function to install the Pyright npm package to a cache.

    This returns the path to the installed package.

    This accepts a single argument which corresponds to the arguments given to the CLI / langserver
    which are used to determine whether or not certain warnings / logs will be printed.
    """
    version = _get_configured_pyright_version()
    if version == 'latest':
        version = node.latest('pyright')
    else:
        if _should_warn_version(args=args, quiet=quiet):
            print(
                f'WARNING: there is a new pyright version available (v{version} -> v{get_latest_version()}).\n'
                + 'Please install the new version or set PYRIGHT_PYTHON_FORCE_VERSION to `latest`\n'
            )

    cache_dir = ROOT_CACHE_DIR / version
    cache_dir.mkdir(exist_ok=True, parents=True)

    pkg_dir = cache_dir / 'node_modules' / 'pyright'
    package_json = cache_dir / 'package.json'
    current_version = node.get_pkg_version(pkg_dir / 'package.json')

    if current_version is None or current_version != version:
        # We need to create a dummy `package.json` file so that `npm` doesn't try
        # and search for it elsewhere.
        #
        # If it finds a different `package.json` file then the `pyright` package
        # will be installed there instead of our cache directory.
        if not package_json.exists():
            package_json.write_text(json.dumps(DEFAULT_PACKAGE_JSON, indent=2))

        silent = '--outputjson' in args
        node.run(
            'npm',
            'install',
            f'pyright@{version}',
            cwd=str(cache_dir),
            check=True,
            stdout=subprocess.PIPE if silent else sys.stdout,
            stderr=subprocess.PIPE if silent else sys.stderr,
        )

    return pkg_dir


def _get_configured_pyright_version() -> str:
    force_version = os.environ.get('PYRIGHT_PYTHON_FORCE_VERSION')
    if force_version:
        return force_version

    pylance_version = os.environ.get('PYRIGHT_PYTHON_PYLANCE_VERSION')
    if pylance_version:
        return _get_pylance_pyright_version(pylance_version)

    return __pyright_version__


def _get_pylance_pyright_version(pylance_version: str) -> str:
    url = f'https://raw.githubusercontent.com/microsoft/pylance-release/main/releases/{pylance_version}.json'

    try:
        response = mureq.get(url, timeout=1)
        response.raise_for_status()

        data = response.json()
        log.debug(f'Pylance release data: {data}')
        version = data['pyrightVersion']

        log.debug(f'Pylance {pylance_version} uses pyright version {version}')
        return version
    except Exception as exc:
        log.debug(f'Failed to download release metadata for Pylance {pylance_version} from {url}: {type(exc)} - {exc}')
        raise


def _should_warn_version(
    *,
    args: tuple[object, ...],
    quiet: bool | None,
) -> bool:
    if quiet:
        # This flag is set by the language server as the output must always be machine parseable
        return False

    if '--outputjson' in args:
        # If this flag is set then the output must be machine parseable
        return False

    if env_to_bool('PYRIGHT_PYTHON_IGNORE_WARNINGS', default=False):
        return False

    # Don't warn about the pyright version if a Pylance version is specified, since the latest
    # Pylance release may not include the latest pyright release yet.
    if os.environ.get('PYRIGHT_PYTHON_PYLANCE_VERSION'):
        return False

    force_version = os.environ.get('PYRIGHT_PYTHON_FORCE_VERSION')
    if force_version and force_version != __pyright_version__:
        return True

    # NOTE: there is an edge case here where a new pyright version has been released
    # but we haven't made a new pyright-python release yet and the user has set
    # PYRIGHT_PYTHON_FORCE_VERSION to the new pyright version.
    # This should rarely happen as we make new releases very frequently after
    # pyright does. Also in order to correctly compare versions we would need an additional
    # dependency. As such this is an acceptable bug.
    latest = get_latest_version()
    return latest is not None and latest != __version__
