# API

This part of the documentation lists the full API reference of all public classes and functions.

```{contents}
---
depth: 1
local: true
---
```

## Decorators

```{eval-rst}
.. autofunction:: click.command
```

```{eval-rst}
.. autofunction:: click.group
```

```{eval-rst}
.. autofunction:: click.argument
```

```{eval-rst}
.. autofunction:: click.option
```

```{eval-rst}
.. autofunction:: click.password_option
```

```{eval-rst}
.. autofunction:: click.confirmation_option
```

```{eval-rst}
.. autofunction:: click.version_option
```

```{eval-rst}
.. autofunction:: click.help_option
```

```{eval-rst}
.. autofunction:: click.pass_context
```

```{eval-rst}
.. autofunction:: click.pass_obj
```

```{eval-rst}
.. autofunction:: click.make_pass_decorator
```

```{eval-rst}
.. autofunction:: click.decorators.pass_meta_key
```

## Utilities

```{eval-rst}
.. autofunction:: click.echo
```

```{eval-rst}
.. autofunction:: click.get_binary_stream
```

```{eval-rst}
.. autofunction:: click.get_text_stream
```

```{eval-rst}
.. autofunction:: click.open_file
```

```{eval-rst}
.. autofunction:: click.get_app_dir
```

```{eval-rst}
.. autofunction:: click.format_filename
```

```{eval-rst}
.. autofunction:: click.echo_via_pager
```

```{eval-rst}
.. autofunction:: click.prompt
```

```{eval-rst}
.. autofunction:: click.confirm
```

```{eval-rst}
.. autofunction:: click.progressbar
```

```{eval-rst}
.. autofunction:: click.clear
```

```{eval-rst}
.. autofunction:: click.style
```

```{eval-rst}
.. autofunction:: click.unstyle
```

```{eval-rst}
.. autofunction:: click.secho
```

```{eval-rst}
.. autofunction:: click.edit
```

```{eval-rst}
.. autofunction:: click.launch
```

```{eval-rst}
.. autofunction:: click.getchar
```

```{eval-rst}
.. autofunction:: click.pause
```

## Commands

```{eval-rst}
.. autoclass:: click.BaseCommand
   :members:
```

```{eval-rst}
.. autoclass:: click.Command
   :members:
```

```{eval-rst}
.. autoclass:: click.MultiCommand
   :members:
```

```{eval-rst}
.. autoclass:: click.Group
   :members:
```

```{eval-rst}
.. autoclass:: click.CommandCollection
   :members:
```

## Parameters

```{eval-rst}
.. autoclass:: click.Parameter
   :members:
```

```{eval-rst}
.. autoclass:: click.Option
```

```{eval-rst}
.. autoclass:: click.Argument
```

## Context

```{eval-rst}
.. autoclass:: click.Context
   :members:
```

```{eval-rst}
.. autofunction:: click.get_current_context
```

```{eval-rst}
.. autoclass:: click.core.ParameterSource
   :members:
   :member-order: bysource
```

(click-api-types)=

## Types

```{eval-rst}
.. autodata:: click.STRING
```

```{eval-rst}
.. autodata:: click.INT
```

```{eval-rst}
.. autodata:: click.FLOAT
```

```{eval-rst}
.. autodata:: click.BOOL
```

```{eval-rst}
.. autodata:: click.UUID
```

```{eval-rst}
.. autodata:: click.UNPROCESSED
```

```{eval-rst}
.. autoclass:: click.File
```

```{eval-rst}
.. autoclass:: click.Path
```

```{eval-rst}
.. autoclass:: click.Choice
   :members:
```

```{eval-rst}
.. autoclass:: click.IntRange
```

```{eval-rst}
.. autoclass:: click.FloatRange
```

```{eval-rst}
.. autoclass:: click.DateTime
```

```{eval-rst}
.. autoclass:: click.Tuple
```

```{eval-rst}
.. autoclass:: click.ParamType
   :members:
```

## Exceptions

```{eval-rst}
.. autoexception:: click.ClickException
```

```{eval-rst}
.. autoexception:: click.Abort
```

```{eval-rst}
.. autoexception:: click.UsageError
```

```{eval-rst}
.. autoexception:: click.BadParameter
```

```{eval-rst}
.. autoexception:: click.FileError
```

```{eval-rst}
.. autoexception:: click.NoSuchOption
```

```{eval-rst}
.. autoexception:: click.BadOptionUsage
```

```{eval-rst}
.. autoexception:: click.BadArgumentUsage
```

## Formatting

```{eval-rst}
.. autoclass:: click.HelpFormatter
   :members:
```

```{eval-rst}
.. autofunction:: click.wrap_text
```

## Parsing

```{eval-rst}
.. autoclass:: click.OptionParser
   :members:
```

## Shell Completion

See {ref}`shell-completion` for information about enabling and customizing Click's shell completion system.

```{eval-rst}
.. autoclass:: click.shell_completion.CompletionItem
```

```{eval-rst}
.. autoclass:: click.shell_completion.ShellComplete
   :members:
   :member-order: bysource
```

```{eval-rst}
.. autofunction:: click.shell_completion.add_completion_class
```

(testing)=

## Testing

```{eval-rst}
.. autoclass:: click.testing.CliRunner
   :members:
```

```{eval-rst}
.. autoclass:: click.testing.Result
   :members:
```
