import os
import sys
import logging
import platform
from typing import Union, Optional
from pathlib import Path
from functools import lru_cache

from . import _mureq as mureq

PYPI_API_URL: str = 'https://pypi.org/pypi/pyright/json'
log: logging.Logger = logging.getLogger(__name__)


def get_env_dir() -> Path:
    """Returns the directory that contains the nodeenv.

    This first respects the `PYRIGHT_PYTHON_ENV_DIR` variable and delegates to `get_cache_dir()` otherwise.
    """
    env_dir = os.environ.get('PYRIGHT_PYTHON_ENV_DIR')
    if env_dir is not None:
        return Path(env_dir)

    return get_cache_dir() / 'pyright-python' / 'nodeenv'


def get_cache_dir() -> Path:
    """Locate a user's cache directory, respects the XDG environment if present, otherwise defaults to `~/.cache`"""
    custom = os.environ.get('PYRIGHT_PYTHON_CACHE_DIR')
    if custom is not None:
        return Path(custom)

    xdg = os.environ.get('XDG_CACHE_HOME')
    if xdg is not None:
        return Path(xdg)

    return Path.home() / '.cache'


def get_bin_dir(*, env_dir: Path) -> Path:
    name = platform.system().lower()
    if name == 'windows':
        return env_dir / 'Scripts'
    return env_dir / 'bin'


def env_to_bool(key: str, *, default: bool = False) -> bool:
    value = os.environ.get(key)
    if value is None:
        return default

    return value.lower() in {'1', 't', 'on', 'true'}


def maybe_decode(data: Union[str, bytes]) -> str:
    if isinstance(data, bytes):
        return data.decode(sys.getdefaultencoding())

    return data


@lru_cache(maxsize=None)
def get_latest_version() -> Optional[str]:
    """Returns the latest available version of pyright-python.

    This relies on the JSON PyPi API, if PyPi is down or the user is offline then
    None is returned.
    """
    try:
        response = mureq.get(PYPI_API_URL, timeout=1)
        version = response.json()['info']['version']
    except Exception as exc:
        log.debug(
            'Encountered exception while fetching latest release: %s - %s',
            type(exc),
            exc,
        )
        return

    if version.startswith('v'):
        version = version[1:]

    log.debug('Latest pyright-python version is: %s', version)
    return version
