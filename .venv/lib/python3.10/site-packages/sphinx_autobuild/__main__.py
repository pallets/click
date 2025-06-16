"""Entrypoint for ``python -m sphinx_autobuild``."""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path

import colorama
import uvicorn

# This isn't public API, but there aren't many better options
from sphinx.cmd.build import get_parser as sphinx_get_parser
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Mount, WebSocketRoute
from starlette.staticfiles import StaticFiles

from sphinx_autobuild import __version__
from sphinx_autobuild.build import Builder
from sphinx_autobuild.filter import IgnoreFilter
from sphinx_autobuild.middleware import JavascriptInjectorMiddleware
from sphinx_autobuild.server import RebuildServer
from sphinx_autobuild.utils import find_free_port, open_browser, show_message


def main(argv=()):
    """Actual application logic."""
    colorama.just_fix_windows_console()

    if not argv:
        # entry point functions don't receive args
        argv = sys.argv[1:]

    args, build_args = _parse_args(list(argv))

    src_dir = Path(args.sourcedir)
    out_dir = Path(args.outdir)
    out_dir.mkdir(parents=True, exist_ok=True)

    serve_dir = out_dir
    if args.make_mode_builder:
        serve_dir = out_dir / args.make_mode_builder
        serve_dir.mkdir(parents=True, exist_ok=True)

    host_name = args.host
    port_num = args.port or find_free_port()
    url_host = f"{host_name}:{port_num}"

    pre_build_commands = list(map(shlex.split, args.pre_build))

    builder = Builder(
        build_args,
        url_host=url_host,
        pre_build_commands=pre_build_commands,
    )

    watch_dirs = [src_dir] + args.additional_watched_dirs
    ignore_dirs = [
        ".git",
        ".hg",
        ".idea",
        ".mypy_cache",
        "node_modules",
        ".nox",
        ".ruff_cache",
        ".pytest_cache",
        ".pytype",
        ".svn",
        ".tox",
        ".venv",
        "venv",
        ".vscode",
        *args.ignore,
        out_dir,
        args.warnings_file,
        args.doctree_dir,
    ]
    ignore_dirs = list(filter(None, ignore_dirs))
    ignore_handler = IgnoreFilter(ignore_dirs, args.re_ignore)
    app = _create_app(watch_dirs, ignore_handler, builder, serve_dir, url_host)

    if not args.no_initial_build:
        show_message("Starting initial build")
        builder(changed_paths=())

    if args.open_browser:
        open_browser(url_host, args.delay)

    show_message("Waiting to detect changes...")
    try:
        uvicorn.run(app, host=host_name, port=port_num, log_level="warning")
    except KeyboardInterrupt:
        show_message("Server ceasing operations. Cheerio!")


def _create_app(watch_dirs, ignore_handler, builder, out_dir, url_host):
    watcher = RebuildServer(watch_dirs, ignore_handler, change_callback=builder)

    return Starlette(
        routes=[
            WebSocketRoute("/websocket-reload", watcher, name="reload"),
            Mount("/", app=StaticFiles(directory=out_dir, html=True), name="static"),
        ],
        middleware=[Middleware(JavascriptInjectorMiddleware, ws_url=url_host)],
        lifespan=watcher.lifespan,
    )


def _parse_args(argv):
    # Parse once with the Sphinx parser to emit errors
    # and capture the ``-d`` and ``-w`` options.
    # NOTE:
    # The Sphinx parser is not considered to be public API,
    # but as this is a first-party project, we can cheat a little bit.
    sphinx_args = _get_sphinx_build_parser().parse_args(argv.copy())

    # Parse a second time with just our parser
    parser = _get_parser()
    args, build_args = parser.parse_known_args(argv.copy())

    # Copy needed settings
    args.sourcedir = Path(sphinx_args.sourcedir).resolve(strict=True)
    args.outdir = Path(sphinx_args.outputdir).resolve()
    if sphinx_args.doctreedir:
        args.doctree_dir = Path(sphinx_args.doctreedir).resolve()
    else:
        args.doctree_dir = None
    if sphinx_args.warnfile:
        args.warnings_file = Path(sphinx_args.warnfile).resolve()
    else:
        args.warnings_file = None

    # Copy the make-mode builder, if present
    args.make_mode_builder = sphinx_args.use_make_mode or ""

    return args, build_args


def _get_sphinx_build_parser():
    # NOTE:
    # sphinx.cmd.build.get_parser is not considered to be public API,
    # but as this is a first-party project, we can cheat a little bit.
    sphinx_build_parser = sphinx_get_parser()
    sphinx_build_parser.description = None
    sphinx_build_parser.epilog = None
    sphinx_build_parser.prog = "sphinx-autobuild"
    for action in sphinx_build_parser._actions:
        if hasattr(action, "version"):
            # Fix the version
            action.version = f"%(prog)s {__version__}"
            break
    sphinx_build_parser.add_argument(
        "-M",
        dest="use_make_mode",
        help=argparse.SUPPRESS,
    )
    _add_autobuild_arguments(sphinx_build_parser)

    return sphinx_build_parser


def _get_parser():
    """Get the application's argument parser."""
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument(
        "--version", action="version", version=f"sphinx-autobuild {__version__}"
    )
    _add_autobuild_arguments(parser)

    return parser


def _add_autobuild_arguments(parser):
    group = parser.add_argument_group("autobuild options")
    group.add_argument(
        "--port",
        type=int,
        default=8000,
        help="port to serve documentation on. 0 means find and use a free port",
    )
    group.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="hostname to serve documentation on",
    )
    group.add_argument(
        "--re-ignore",
        action="append",
        default=[],
        help="regular expression for files to ignore, when watching for changes",
    )
    group.add_argument(
        "--ignore",
        action="append",
        default=[],
        help="glob expression for files to ignore, when watching for changes",
    )
    group.add_argument(
        "--no-initial",
        dest="no_initial_build",
        action="store_true",
        default=False,
        help="skip the initial build",
    )
    group.add_argument(
        "--open-browser",
        action="store_true",
        default=False,
        help="open the browser after building documentation",
    )
    group.add_argument(
        "--delay",
        dest="delay",
        type=float,
        default=5,
        help="how long to wait before opening the browser",
    )
    group.add_argument(
        "--watch",
        action="append",
        metavar="DIR",
        default=[],
        help="additional directories to watch",
        dest="additional_watched_dirs",
    )
    group.add_argument(
        "--pre-build",
        action="append",
        metavar="COMMAND",
        default=[],
        help="additional command(s) to run prior to building the documentation",
    )
    return group


if __name__ == "__main__":
    main(sys.argv[1:])
