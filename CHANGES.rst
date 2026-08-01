# CHANGES

## TBR (TBR)

-   **Multiple options with defaults now merge defaults with CLI values.**
    When using ``@click.option(..., multiple=True, default=(...))``, the
    default values are now prepended to any user-provided command-line values
    instead of being discarded entirely. This resolves the long-standing
    behavior reported in `#117
    <https://github.com/pallets/click/issues/117>`_ where defaults for
    ``multiple=True`` options were silently dropped as soon as any values were
    passed on the command line.
