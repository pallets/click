# API

This part of the documentation lists the full API reference of all public classes and functions.

```{contents}
---
depth: 1
local: true
---
```

## Decorators

:::{autodoc2-object} click.decorators.command
:::

:::{autodoc2-object} click.decorators.group
:::

:::{autodoc2-object} click.decorators.argument
:::

:::{autodoc2-object} click.decorators.option
:::

:::{autodoc2-object} click.decorators.password_option
:::

:::{autodoc2-object} click.decorators.confirmation_option
:::

:::{autodoc2-object} click.decorators.version_option
:::

:::{autodoc2-object} click.decorators.help_option
:::

:::{autodoc2-object} click.decorators.pass_context
:::

:::{autodoc2-object} click.decorators.pass_obj
:::

:::{autodoc2-object} click.decorators.make_pass_decorator
:::

:::{autodoc2-object} click.decorators.pass_meta_key
:::

## Utilities

:::{autodoc2-object} click.utils.echo
:::

:::{autodoc2-object} click.utils.get_binary_stream
:::

:::{autodoc2-object} click.utils.get_text_stream
:::

:::{autodoc2-object} click.utils.open_file
:::

:::{autodoc2-object} click.utils.get_app_dir
:::

:::{autodoc2-object} click.utils.format_filename
:::

:::{autodoc2-object} click.termui.echo_via_pager
:::

:::{autodoc2-object} click.termui.prompt
:::

:::{autodoc2-object} click.termui.confirm
:::

:::{autodoc2-object} click.termui.progressbar
:::

:::{autodoc2-object} click.termui.clear
:::

:::{autodoc2-object} click.termui.style
:::

:::{autodoc2-object} click.termui.unstyle
:::

:::{autodoc2-object} click.termui.secho
:::

:::{autodoc2-object} click.termui.edit
:::

:::{autodoc2-object} click.termui.launch
:::

:::{autodoc2-object} click.termui.getchar
:::

:::{autodoc2-object} click.termui.pause
:::

## Commands

:::{autodoc2-object} click.core._BaseCommand
:::

:::{autodoc2-object} click.core.Command
:::

:::{autodoc2-object} click.core._MultiCommand
:::

:::{autodoc2-object} click.core.Group
:::

:::{autodoc2-object} click.core.CommandCollection
:::

## Parameters

:::{autodoc2-object} click.core.Parameter
:::

:::{autodoc2-object} click.core.Option
:::

:::{autodoc2-object} click.core.Argument
:::

## Context

:::{autodoc2-object} click.core.Context
:::

:::{autodoc2-object} click.globals.get_current_context
:::

:::{autodoc2-object} click.core.ParameterSource
:::

(click-api-types)=

## Types

:::{autodoc2-object} click.types.STRING
:::

:::{autodoc2-object} click.types.INT
:::

:::{autodoc2-object} click.types.FLOAT
:::

:::{autodoc2-object} click.types.BOOL
:::

:::{autodoc2-object} click.types.UUID
:::

:::{autodoc2-object} click.types.UNPROCESSED
:::

:::{autodoc2-object} click.types.File
:::

:::{autodoc2-object} click.types.Path
:::

:::{autodoc2-object} click.types.Choice
:::

:::{autodoc2-object} click.types.IntRange
:::

:::{autodoc2-object} click.types.FloatRange
:::

:::{autodoc2-object} click.types.DateTime
:::

:::{autodoc2-object} click.types.Tuple
:::

:::{autodoc2-object} click.types.ParamType
:::

## Exceptions

:::{autodoc2-object} click.exceptions.ClickException
:::

:::{autodoc2-object} click.exceptions.Abort
:::

:::{autodoc2-object} click.exceptions.UsageError
:::

:::{autodoc2-object} click.exceptions.BadParameter
:::

:::{autodoc2-object} click.exceptions.FileError
:::

:::{autodoc2-object} click.exceptions.NoSuchOption
:::

:::{autodoc2-object} click.exceptions.BadOptionUsage
:::

:::{autodoc2-object} click.exceptions.BadArgumentUsage
:::

## Formatting

:::{autodoc2-object} click.formatting.HelpFormatter
:::

:::{autodoc2-object} click.formatting.wrap_text
:::

## Parsing

:::{autodoc2-object} click.parser._OptionParser
:::

## Shell Completion

See {ref}`shell-completion` for information about enabling and customizing Click's shell completion system.

:::{autodoc2-object} click.shell_completion.CompletionItem
:::

:::{autodoc2-object} click.shell_completion.ShellComplete
:::

:::{autodoc2-object} click.shell_completion.add_completion_class
:::

(testing)=

## Testing

:::{autodoc2-object} click.testing.CliRunner
:::

:::{autodoc2-object} click.testing.Result
:::
