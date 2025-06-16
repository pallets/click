"""Logic for interacting with sphinx-build."""

from __future__ import annotations

import contextlib
import subprocess
import sys
import traceback
from collections.abc import Sequence
from pathlib import Path

import sphinx

from sphinx_autobuild.utils import show_command, show_message


class Builder:
    def __init__(self, sphinx_args, *, url_host, pre_build_commands):
        self.sphinx_args = sphinx_args
        self.pre_build_commands = pre_build_commands
        self.uri = f"http://{url_host}"

    def __call__(self, *, changed_paths: Sequence[Path]):
        """Generate the documentation using ``sphinx``."""
        if changed_paths:
            cwd = Path.cwd()
            rel_paths = []
            for changed_path in changed_paths[:5]:
                if not changed_path.exists():
                    continue
                with contextlib.suppress(ValueError):
                    changed_path = changed_path.relative_to(cwd)
                rel_paths.append(changed_path.as_posix())
            if rel_paths:
                show_message(f"Detected changes ({', '.join(rel_paths)})")
            show_message("Rebuilding...")

        try:
            for command in self.pre_build_commands:
                show_message("pre-build")
                show_command(command)
                subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Pre-build command exited with exit code: {e.returncode}")
            print(
                "Please fix the cause of the error above or press Ctrl+C to stop the "
                "server."
            )
            print(
                "The server will continue serving the build folder, but the contents "
                "being served are no longer in sync with the documentation sources. "
                "Please fix the cause of the error above or press Ctrl+C to stop the "
                "server."
            )
            traceback.print_exception(e)
            return

        if sphinx.version_info[:3] >= (7, 2, 3):
            sphinx_build_args = ["-m", "sphinx", "build"] + self.sphinx_args
        else:
            sphinx_build_args = ["-m", "sphinx"] + self.sphinx_args
        show_command(["python"] + sphinx_build_args)
        try:
            subprocess.run([sys.executable] + sphinx_build_args, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Sphinx exited with exit code: {e.returncode}")
            print(
                "The server will continue serving the build folder, but the contents "
                "being served are no longer in sync with the documentation sources. "
                "Please fix the cause of the error above or press Ctrl+C to stop the "
                "server."
            )
        # Remind the user of the server URL for convenience.
        show_message(f"Serving on {self.uri}")
