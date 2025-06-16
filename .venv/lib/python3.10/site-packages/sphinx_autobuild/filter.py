"""Logic for ignoring paths."""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path


class IgnoreFilter:
    def __init__(self, regular, regex_based):
        """Prepare the function that determines whether a path should be ignored."""
        normalised_paths = [Path(p).resolve().as_posix() for p in regular]
        self.regular_patterns = list(dict.fromkeys(normalised_paths))
        self.regex_based_patterns = [*map(re.compile, dict.fromkeys(regex_based))]

    def __repr__(self):
        return (
            f"IgnoreFilter(regular={self.regular_patterns!r}, "
            f"regex_based={self.regex_based_patterns!r})"
        )

    def __call__(self, filename: str, /):
        """Determine if 'path' should be ignored."""
        normalised_path = Path(filename).resolve().as_posix()
        # Any regular pattern matches.
        for pattern in self.regular_patterns:
            # separators are normalised before creating the IgnoreFilter
            if normalised_path.startswith(f"{pattern}/"):
                return True
            if fnmatch.fnmatch(normalised_path, pattern):
                return True

        # Any regular expression matches.
        for regex in self.regex_based_patterns:  # NoQA: SIM110
            if regex.search(normalised_path):
                return True

        return False
