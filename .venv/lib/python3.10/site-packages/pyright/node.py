from __future__ import annotations

import os
import re
import sys
import json
import shutil
import logging
import platform
import subprocess
import importlib.util
from typing import Any, Dict, Tuple, Union, Mapping, Optional, NamedTuple, cast
from pathlib import Path
from functools import lru_cache
from typing_extensions import Literal, assert_never

from . import errors
from .types import Target, check_target
from .utils import env_to_bool, get_bin_dir, get_env_dir, maybe_decode

log: logging.Logger = logging.getLogger(__name__)

ENV_DIR: Path = get_env_dir()
BINARIES_DIR: Path = get_bin_dir(env_dir=ENV_DIR)
USE_GLOBAL_NODE = env_to_bool('PYRIGHT_PYTHON_GLOBAL_NODE', default=True)
USE_NODEJS_WHEEL = env_to_bool('PYRIGHT_PYTHON_NODEJS_WHEEL', default=True)
NODE_VERSION = os.environ.get('PYRIGHT_PYTHON_NODE_VERSION', default=None)
VERSION_RE = re.compile(r'\d+\.\d+\.\d+')


def _is_windows() -> bool:
    return platform.system().lower() == 'windows'


def _postfix_for_target(target: Target) -> str:
    if not _is_windows():
        return ''

    if target == 'node':
        return '.exe'
    return '.cmd'


def _ensure_node_env(target: Target) -> Path:
    log.debug('Checking for nodeenv %s binary', target)

    path = _get_nodeenv_path(target)
    log.debug('Using %s path for binary', path)

    if path.exists() and not NODE_VERSION:
        log.debug('Binary at %s exists, skipping nodeenv installation', path)
    else:
        log.debug('Installing nodeenv as a binary at %s could not be found', path)
        _install_node_env()

    if not path.exists():
        raise errors.BinaryNotFound(path=path, target=target)
    return path


def _get_nodeenv_path(target: Target) -> Path:
    return BINARIES_DIR.joinpath(target + _postfix_for_target(target))


def _get_global_binary(target: Target) -> Optional[Path]:
    log.debug('Checking for global target binary: %s', target)

    path = target + _postfix_for_target(target)

    which = shutil.which(path)
    if which is not None:
        log.debug('Found global binary at: %s', which)

        path = Path(which)
        if path.exists():
            log.debug('Global binary exists at: %s', which)
            return path

    log.debug('Global target binary: %s not found', target)
    return None


def _install_node_env() -> None:
    log.debug('Installing nodeenv to %s', ENV_DIR)
    args = [sys.executable, '-m', 'nodeenv']
    if NODE_VERSION:
        log.debug(f'Using user specified node version: {NODE_VERSION}')
        args += ['--node', NODE_VERSION, '--force']
    args.append(str(ENV_DIR))
    log.debug('Running command with args: %s', args)

    try:
        subprocess.run(args, check=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            'nodeenv failed; for more reliable node.js binaries try `pip install pyright[nodejs]`'
        ) from exc


class GlobalStrategy(NamedTuple):
    type: Literal['global']
    path: Path


class NodeJSWheelStrategy(NamedTuple):
    type: Literal['nodejs_wheel']


class NodeenvStrategy(NamedTuple):
    type: Literal['nodeenv']
    path: Path


Strategy = Union[GlobalStrategy, NodeJSWheelStrategy, NodeenvStrategy]


def _resolve_strategy(target: Target) -> Strategy:
    if USE_NODEJS_WHEEL:
        if importlib.util.find_spec('nodejs_wheel') is not None:
            log.debug('Using nodejs_wheel package for resolving binaries')
            return NodeJSWheelStrategy(type='nodejs_wheel')

    if USE_GLOBAL_NODE:
        path = _get_global_binary(target)
        if path is not None:
            log.debug('Using global %s binary', target)
            return GlobalStrategy(type='global', path=path)

    log.debug('Installing binaries using nodeenv')
    return NodeenvStrategy(type='nodeenv', path=_ensure_node_env(target))


def run(
    target: Target, *args: str, **kwargs: Any
) -> Union['subprocess.CompletedProcess[bytes]', 'subprocess.CompletedProcess[str]']:
    check_target(target)

    strategy = _resolve_strategy(target)
    if strategy.type == 'global':
        node_args = [str(strategy.path), *args]
        log.debug('Running global node command with args: %s', node_args)
        return cast(
            'subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]',
            subprocess.run(node_args, **kwargs),
        )
    elif strategy.type == 'nodejs_wheel':
        import nodejs_wheel

        if target == 'node':
            return cast(
                'subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]',
                nodejs_wheel.node(args, return_completed_process=True, **kwargs),
            )
        elif target == 'npm':
            return cast(
                'subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]',
                nodejs_wheel.npm(args, return_completed_process=True, **kwargs),
            )
        else:
            assert_never(target)
    elif strategy.type == 'nodeenv':
        env = kwargs.pop('env', None) or os.environ.copy()
        env.update(get_env_variables())

        # If we're using `nodeenv` to resolve the node binary then we also need
        # to ensure that `node` is in the PATH so that any install scripts that
        # assume it is present will work.
        env.update(PATH=_update_path_env(env=env, target_bin=strategy.path.parent))
        node_args = [str(strategy.path), *args]
        log.debug('Running nodeenv command with args: %s', node_args)
        return cast(
            'subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]',
            subprocess.run(node_args, env=env, **kwargs),
        )
    else:
        assert_never(strategy)


def version(target: Target) -> Tuple[int, ...]:
    proc = run(target, '--version', stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = maybe_decode(proc.stdout)
    match = VERSION_RE.search(output)
    if not match:
        print(output, file=sys.stderr)
        raise errors.VersionCheckFailed(f'Could not find version from `{target} --version`, see output above')

    info = tuple(int(value) for value in match.group(0).split('.'))
    log.debug('Version check for %s returning %s', target, info)
    return info


@lru_cache(maxsize=None)
def latest(package: str) -> str:
    """Return the latest version for the given package"""
    proc = run(
        'npm',
        'info',
        package,
        'version',
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    stdout = maybe_decode(proc.stdout)

    if proc.returncode != 0:
        print(stdout, file=sys.stderr)
        raise errors.VersionCheckFailed(f'Version check for {package} failed, see output above.')

    match = VERSION_RE.search(stdout)
    if not match:
        print(stdout, file=sys.stderr)
        raise errors.VersionCheckFailed(f'Could not find version for {package}, see output above')

    value = match.group(0)
    log.debug('Version check for %s returning %s', package, value)
    return value


def get_env_variables() -> Dict[str, Any]:
    """Return the environmental variables that should be passed to a binary"""
    # NOTE: I do not actually know if these result in the intended behaviour
    #       I simply copied them from bin/shim in nodeenv
    return {
        'NODE_PATH': str(ENV_DIR / 'lib' / 'node_modules'),
        'NPM_CONFIG_PREFIX': str(ENV_DIR),
        'npm_config_prefix': str(ENV_DIR),
    }


def get_pkg_version(pkg: Path) -> str | None:
    """Given a path to a `package.json` file, parse it and returns the `version` property

    Returns `None` if the version could not be resolved for any reason.
    """
    if not pkg.exists():
        return None

    try:
        data = json.loads(pkg.read_text())
    except Exception:
        # TODO: test this
        log.debug('Ignoring error while reading/parsing the %s file', pkg, exc_info=True)
        return None

    return data.get('version')


def _update_path_env(
    *,
    env: Mapping[str, str] | None,
    target_bin: Path,
    sep: str = os.pathsep,
) -> str:
    """Returns a modified version of the `PATH` environment variable that has been updated
    to include the location of the downloaded Node binaries.
    """
    if env is None:
        env = dict(os.environ)

    log.debug('Attempting to prepend %s to the PATH', target_bin)
    assert target_bin.exists(), f'Target directory {target_bin} does not exist'

    path = env.get('PATH', '') or os.environ.get('PATH', '')
    if path:
        log.debug('Found PATH contents: %s', path)

        # handle the case where the PATH already starts with the separator (this probably shouldn't happen)
        if path.startswith(sep):
            path = f'{target_bin.absolute()}{path}'
        else:
            path = f'{target_bin.absolute()}{sep}{path}'
    else:
        # handle the case where there is no PATH set (unlikely / impossible to actually happen?)
        path = str(target_bin.absolute())

    log.debug('Using PATH environment variable: %s', path)
    return path
