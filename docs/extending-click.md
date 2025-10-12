# Extending Click

```{currentmodule} click
```

In addition to common functionality that is implemented in the library itself, there are countless patterns that can be
implemented by extending Click. This page should give some insight into what can be accomplished.

```{contents}
:depth: 2
:local: true
```

(custom-groups)=

## Custom Groups

You can customize the behavior of a group beyond the arguments it accepts by subclassing {class}`click.Group`.

The most common methods to override are {meth}`~click.Group.get_command` and {meth}`~click.Group.list_commands`.

The following example implements a basic plugin system that loads commands from Python files in a folder. The command is
lazily loaded to avoid slow startup.

```python
import importlib.util
import os
import click

class PluginGroup(click.Group):
    def __init__(self, name=None, plugin_folder="commands", **kwargs):
        super().__init__(name=name, **kwargs)
        self.plugin_folder = plugin_folder

    def list_commands(self, ctx):
        rv = []

        for filename in os.listdir(self.plugin_folder):
            if filename.endswith(".py"):
                rv.append(filename[:-3])

        rv.sort()
        return rv

    def get_command(self, ctx, name):
        path = os.path.join(self.plugin_folder, f"{name}.py")
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.cli

cli = PluginGroup(
    plugin_folder=os.path.join(os.path.dirname(__file__), "commands")
)

if __name__ == "__main__":
    cli()
```

Custom classes can also be used with decorators:

```python
@click.group(
    cls=PluginGroup,
    plugin_folder=os.path.join(os.path.dirname(__file__), "commands")
)
def cli():
    pass
```

(aliases)=

## Command Aliases

Many tools support aliases for commands. For example, you can configure `git` to accept `git ci` as alias for
`git commit`. Other tools also support auto-discovery for aliases by automatically shortening them.

It's possible to customize {class}`Group` to provide this functionality. As explained in {ref}`custom-groups`, a group
provides two methods: {meth}`~Group.list_commands` and {meth}`~Group.get_command`. In this particular case, you only
need to override the latter as you generally don't want to enumerate the aliases on the help page in order to avoid
confusion.

The following example implements a subclass of {class}`Group` that accepts a prefix for a command. If there was a
command called `push`, it would accept `pus` as an alias (so long as it was unique):

```{eval-rst}
.. click:example::

    class AliasedGroup(click.Group):
        def get_command(self, ctx, cmd_name):
            rv = super().get_command(ctx, cmd_name)

            if rv is not None:
                return rv

            matches = [
                x for x in self.list_commands(ctx)
                if x.startswith(cmd_name)
            ]

            if not matches:
                return None

            if len(matches) == 1:
                return click.Group.get_command(self, ctx, matches[0])

            ctx.fail(f"Too many matches: {', '.join(sorted(matches))}")

        def resolve_command(self, ctx, args):
            # always return the full command name
            _, cmd, args = super().resolve_command(ctx, args)
            return cmd.name, cmd, args
```

It can be used like this:

```python

    @click.group(cls=AliasedGroup)
    def cli():
        pass

    @cli.command
    def push():
        pass

    @cli.command
    def pop():
        pass
```

See the [alias example](https://github.com/pallets/click/tree/main/examples/aliases) in Click's repository for another example.
