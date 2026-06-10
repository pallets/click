Screenshots
===========

Click uses Playwright_ to capture high-quality screenshots of terminal
output for the documentation. This ensures crisp, accurate visuals across
all platforms.

.. _Playwright: https://playwright.dev

Requirements
------------

Install the screenshot dependencies:

.. code-block:: bash

    pip install playwright
    playwright install chromium

Capturing Screenshots
---------------------

Use the capture script to generate screenshots:

.. code-block:: bash

    # Capture a simple command
    python docs/_scripts/capture.py \
        --command "python -m click --help" \
        --output docs/_static/screenshots/

    # With custom font size
    python docs/_scripts/capture.py \
        --command "python examples/complex.py --help" \
        --font-size 16 \
        --width 1000

CI Integration
--------------

Screenshots are captured automatically in GitHub Actions via the
``screenshots.yaml`` workflow. To trigger manually:

1. Go to the Actions tab
2. Select "Documentation Screenshots"
3. Click "Run workflow"

Adding Screenshots to Docs
--------------------------

Use the ``image`` directive in RST files:

.. code-block:: rst

    .. image:: /_static/screenshots/demo.png
       :alt: Click help output
       :align: center

Guidelines
----------

- Keep screenshots focused: capture only the relevant output
- Use consistent font size (14px default) across all screenshots
- Verify screenshots render correctly on both light and dark backgrounds
- Update screenshots when command behavior changes
