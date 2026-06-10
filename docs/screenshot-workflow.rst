Screenshot Workflow Research
============================

**Issue**: `#3081 <https://github.com/pallets/click/issues/3081>`__ - Add Screenshot workflow for docs
**Status**: Approved for implementation

Requirements
------------

- Run locally for doc generation (no external API calls)
- Run in CI (GitHub Actions)
- No extra dependencies beyond pip-installable packages
- Non-blurry screenshots
- Draw annotation boxes around sections

Options Considered
------------------

Option 1: Playwright *(Recommended)*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **Dependency**: ``playwright`` (pip install)
- Uses real headless Chromium → sharp, accurate screenshots
- CI compatible: ``playwright install chromium`` in GHA
- Annotation: inject CSS before screenshot to draw boxes

**Pros**: High fidelity, mature, CI-tested, pip-only
**Cons**: Browser engine adds ~100MB download

Option 2: Pillow + iTerm Graphics Protocol
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Uses terminal image protocol (no screenshot needed)
- Works natively in iTerm2/kitty only

**Cons**: Not portable, user must have compatible terminal

Option 3: asciicast2gif / Terminalizer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Records terminal session as GIF
- Requires external tools or JS runtime

**Cons**: Complex setup, not reliable in CI

Recommendation: Playwright
--------------------------

Meets all requirements with minimal friction. The Pallets ecosystem
already uses Playwright in some projects for browser testing.

Implementation in This PR
--------------------------

1. Added ``playwright`` to docs dependency group in ``pyproject.toml``
2. Added ``docs/_scripts/`` directory for capture tools
3. Created ``docs/_scripts/capture.py`` - the main capture utility
4. Added ``.github/workflows/screenshots.yaml`` for CI automation
5. Created ``docs/screenshots.rst`` as user documentation

Files Changed
-------------

- ``pyproject.toml`` - Added playwright to docs dependencies
- ``docs/_scripts/capture.py`` - Screenshot capture script
- ``docs/screenshots.rst`` - User documentation
- ``.github/workflows/screenshots.yaml`` - CI workflow
- ``docs/screenshot-workflow.rst`` - This research document
