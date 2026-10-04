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
- A parameter name that is not a valid Python identifier, or that is a [Python keyword](https://docs.python.org/3/reference/lexical_analysis.html#keywords), is deprecated and raises `TypeError` in 9.0. [`str.isidentifier()`](https://docs.python.org/3/library/stdtypes.html#str.isidentifier) decides the first case, so `click.argument("0foo")` fails it. It accepts a keyword, so `click.option("--from")` names a parameter `from`, which no callback can declare. [Soft keywords](https://docs.python.org/3/reference/lexical_analysis.html#soft-keywords) such as `match` and `type` are contextual and unaffected, and `--True` and `--None` lower case out of the keyword set. To migrate, pass an explicit name (`click.option("--from", "source")`, `click.option("--0-file", "zero_file")`). An argument takes one declaration and has no explicit-name channel, so rename it and pass `metavar` to keep its old display (`click.argument("zero_file", metavar="0-FILE")`). See [#3827](https://github.com/pallets/click/pull/3827) and [#3866](https://github.com/pallets/click/pull/3866).
- An option name written as a Python identifier is deprecated when it is not already lower cased: `click.option("--x", "Foo_Bar")` names `foo_bar` rather than `Foo_Bar`. To migrate, spell the name the way the callback declares it. See [#3827](https://github.com/pallets/click/pull/3827).
- `CliRunner.isolated_filesystem()` is deprecated and will be removed in Click 9.0. The helper predates Python 3 and modern pytest, and it relies on `os.chdir`, which mutates process-global state and is therefore not thread-safe. Replace it with a temporary directory (`tempfile.TemporaryDirectory`, or pytest's `tmp_path` fixture) and pass absolute paths to the command instead of relying on the current working directory. To run commands in parallel, use process-based isolation (such as `pytest-xdist`) rather than threads, since `CliRunner.invoke()` also redirects the process-global standard streams and other interpreter-wide state. See [#3700](https://github.com/pallets/click/issues/3700), [#3501](https://github.com/pallets/click/issues/3501) and the [testing guide](testing.md#running-tests-in-parallel).
- `Parameter.human_readable_name` is deprecated and will be removed in Click 9.0. Use `Parameter.spec` instead, which returns how the user spells the parameter on the command line. For an argument the two agree, since both return the metavar. For an option the old property returned the internal `name`, so the value changes from `my_option` to `--my-option`. Click no longer reads the property, so an override in a subclass has no effect: override `Parameter.spec` instead. Defining a subclass that still overrides `human_readable_name` emits a `DeprecationWarning`. See the [parameter names](parameters.md#parameter-names) section for the three strings that designate a parameter.

### Removals with prior deprecation

For each removal, provide a brief explanation, and direct users to new function / class if available. If possible, deprecate and remove in 10.0.0, rather than removing outright.
- TBD

### Removals with no prior deprecation

The changes were not able to be deprecated prior to removal. Explain clearly why then were not able to be deprecated first.
- TBD

### Changes

- Error messages and deprecation warnings name an option by its spec rather than its internal name, so `The option 'my_option' is deprecated.` now reads `The option '--my-option' is deprecated.` Tests asserting on the old wording need updating.

### Fixes

- TBD
