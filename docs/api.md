# API

```{currentmodule} click
```

This part of the documentation lists the full API reference of all public
classes and functions.

```{contents}
:depth: 1
:local: true
```

## Decorators

```{eval-rst}
.. autofunction:: command
```

```{eval-rst}
.. autofunction:: group
```

```{eval-rst}
.. autofunction:: argument
```

```{eval-rst}
.. autofunction:: option
```

```{eval-rst}
.. autofunction:: password_option
```

```{eval-rst}
.. autofunction:: confirmation_option
```

```{eval-rst}
.. autofunction:: version_option
```

```{eval-rst}
.. autofunction:: help_option
```

```{eval-rst}
.. autofunction:: pass_context
```

```{eval-rst}
.. autofunction:: pass_obj
```

```{eval-rst}
.. autofunction:: make_pass_decorator
```

```{eval-rst}
.. autofunction:: click.decorators.pass_meta_key

```

## Utilities

```{eval-rst}
.. autofunction:: echo
```

```{eval-rst}
.. autofunction:: echo_via_pager
```

```{eval-rst}
.. autofunction:: prompt
```

```{eval-rst}
.. autofunction:: confirm
```

```{eval-rst}
.. autofunction:: progressbar
```

```{eval-rst}
.. autofunction:: clear
```

```{eval-rst}
.. autofunction:: style
```

```{eval-rst}
.. autofunction:: unstyle
```

```{eval-rst}
.. autofunction:: secho
```

```{eval-rst}
.. autofunction:: edit
```

```{eval-rst}
.. autofunction:: launch
```

```{eval-rst}
.. autofunction:: getchar
```

```{eval-rst}
.. autofunction:: pause
```

```{eval-rst}
.. autofunction:: get_binary_stream
```

```{eval-rst}
.. autofunction:: get_text_stream
```

```{eval-rst}
.. autofunction:: open_file
```

```{eval-rst}
.. autofunction:: get_app_dir
```

```{eval-rst}
.. autofunction:: format_filename
```

## Commands

```{eval-rst}
.. autoclass:: BaseCommand
   :members:
```

```{eval-rst}
.. autoclass:: Command
   :members:
```

```{eval-rst}
.. autoclass:: MultiCommand
   :members:
```

```{eval-rst}
.. autoclass:: Group
   :members:
```

```{eval-rst}
.. autoclass:: CommandCollection
   :members:
```

## Parameters

```{eval-rst}
.. autoclass:: Parameter
   :members:
```

```{eval-rst}
.. autoclass:: Option
```

```{eval-rst}
.. autoclass:: Argument
```

## Context

```{eval-rst}
.. autoclass:: Context
   :members:
```

```{eval-rst}
.. autofunction:: get_current_context
```

```{eval-rst}
.. autoclass:: click.core.ParameterSource
    :members:
    :member-order: bysource
```

(click-api-types)=

## Types

```{eval-rst}
.. autodata:: STRING
```

```{eval-rst}
.. autodata:: INT
```

```{eval-rst}
.. autodata:: FLOAT
```

```{eval-rst}
.. autodata:: BOOL
```

```{eval-rst}
.. autodata:: UUID
```

```{eval-rst}
.. autodata:: UNPROCESSED
```

```{eval-rst}
.. autoclass:: File
```

```{eval-rst}
.. autoclass:: Path
```

```{eval-rst}
.. autoclass:: Choice
   :members:
```

```{eval-rst}
.. autoclass:: IntRange
```

```{eval-rst}
.. autoclass:: FloatRange
```

```{eval-rst}
.. autoclass:: DateTime
```

```{eval-rst}
.. autoclass:: Tuple
```

```{eval-rst}
.. autoclass:: ParamType
   :members:
```

## Exceptions

```{eval-rst}
.. autoexception:: ClickException
```

```{eval-rst}
.. autoexception:: Abort
```

```{eval-rst}
.. autoexception:: UsageError
```

```{eval-rst}
.. autoexception:: BadParameter
```

```{eval-rst}
.. autoexception:: FileError
```

```{eval-rst}
.. autoexception:: NoSuchOption
```

```{eval-rst}
.. autoexception:: BadOptionUsage
```

```{eval-rst}
.. autoexception:: BadArgumentUsage
```

## Formatting

```{eval-rst}
.. autoclass:: HelpFormatter
   :members:
```

```{eval-rst}
.. autofunction:: wrap_text
```

## Parsing

```{eval-rst}
.. autoclass:: OptionParser
   :members:

```

## Shell Completion

See `/shell-completion` for information about enabling and
customizing Click's shell completion system.

```{eval-rst}
.. currentmodule:: click.shell_completion
```

```{eval-rst}
.. autoclass:: CompletionItem
```

```{eval-rst}
.. autoclass:: ShellComplete
    :members:
    :member-order: bysource
```

```{eval-rst}
.. autofunction:: add_completion_class

```

(testing)=

## Testing

```{eval-rst}
.. currentmodule:: click.testing
```

```{eval-rst}
.. autoclass:: CliRunner
   :members:
```

```{eval-rst}
.. autoclass:: Result
   :members:
```
