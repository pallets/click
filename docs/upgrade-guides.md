# Upgrade Guides

```{contents}
:depth: 1
:local: true
```

## Upgrading 8.3.X to 9.0
**This is under active construction and will not be finalized until 9.0.0 is released.**

This guide assumes the user is on version 8.3.X.

### Deprecations

For each deprecation, provide a brief explanation, and direct users to new function / class if available.
- `CliRunner.isolated_filesystem()` is deprecated and will be removed in Click 9.0. The helper predates Python 3 and modern pytest, and it relies on `os.chdir`, which mutates process-global state and is therefore not thread-safe. Replace it with a temporary directory (`tempfile.TemporaryDirectory`, or pytest's `tmp_path` fixture) and pass absolute paths to the command instead of relying on the current working directory. To run commands in parallel, use process-based isolation (such as `pytest-xdist`) rather than threads, since `CliRunner.invoke()` also redirects the process-global standard streams and other interpreter-wide state. See [#3700](https://github.com/pallets/click/issues/3700), [#3501](https://github.com/pallets/click/issues/3501) and the [testing guide](testing.md#running-tests-in-parallel).

### Removals with prior deprecation

For each removal, provide a brief explanation, and direct users to new function / class if available. If possible, deprecate and remove in 10.0.0, rather than removing outright.
- TBD

### Removals with no prior deprecation

The changes were not able to be deprecated prior to removal. Explain clearly why then were not able to be deprecated first.
- TBD

### Changes

- TBD

### Fixes

- TBD
