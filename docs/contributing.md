# Contributing

This is a quick reference for Click-specific development
tasks. For setting up the development environment and the
general contribution workflow, see the Pallets [quick
reference](https://palletsprojects.com/contributing/quick/)
and the [detailed contributing
guide](https://palletsprojects.com/contributing/).

## Extra Test Environments

Click includes some extra test environments:

-   `tox r -e stress` runs stress tests for race conditions
    in Click's test runner.

    ```shell-session
    $ tox r -e stress
    ```

-   `tox r -e random` runs tests in parallel in a random
    order to detect test pollution.

    ```shell-session
    $ tox r -e random
    ```

-   A CI workflow (`.github/workflows/test-flask.yaml`)
    runs Flask's test suite to catch downstream
    regressions.

## Code Style

Avoid ternary expressions (`x if cond else y`): coverage
cannot measure both branches. Use an explicit `if`/`else`
block instead.

Do not add unnecessary dependencies. If a feature can be
implemented with the standard library, do not pull in an
external package for it.

## Formatting

Wrap lines in Markdown files at 80 characters.

## Translations

If you want to work on translations:

* Install gettext. Windows requires a unix-like environment - see [MinGW gettext](https://gnuwin32.sourceforge.net/packages/gettext.htm).

* Compile the translations.
  ```shell-session
  $ bash ./locales/compile.sh
  ```
