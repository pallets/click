# Advanced Patterns

In addition to common functionality, Click offers some advanced features.

```{contents}
---
depth: 1
local: true
---
```

## Callbacks and Eager Options

Sometimes, you want a parameter to completely change the execution flow. For instance, this is the case when you want to
have a `--version` parameter that prints out the version and then exits the application.

Note: an actual implementation of a `--version` parameter that is reusable is available in Click as
{func}`click.version_option`. The code here is merely an example of how to implement such a flag.

In such cases, you need two concepts: eager parameters and a callback. An eager parameter is a parameter that is handled
before others, and a callback is what executes after the parameter is handled. The eagerness is necessary so that an
earlier required parameter does not produce an error message. For instance, if `--version` was not eager and a parameter
`--foo` was required and defined before, you would need to specify it for `--version` to work. For more information, see
{ref}`callback-evaluation-order`.

A callback is a function that is invoked with three parameters: the current {func}`click.Context`, the current
{func}`click.Parameter`, and the value. The context provides some useful features such as quitting the application and gives
access to other already processed parameters.

Here's an example for a `--version` flag:

```python
def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo('Version 1.0')
    ctx.exit()

@click.command()
@click.option('--version', is_flag=True, callback=print_version,
              expose_value=False, is_eager=True)
def hello():
    click.echo('Hello World!')
```


The `expose_value` parameter prevents the pretty pointless `version` parameter from being passed to the callback. If
that was not specified, a boolean would be passed to the `hello` script. The `resilient_parsing` flag is applied to the
context if Click wants to parse the command line without any destructive behavior that would change the execution flow.
In this case, because we would exit the program, we instead do nothing.

What it looks like:

```console
$ hello
Hello World!

$ hello --version
Version 1.0
```

## Callbacks for Validation

```{versionchanged} 2.0 
```

If you want to apply custom validation logic, you can do this in the parameter callbacks. These callbacks can both
modify values as well as raise errors if the validation does not work. The callback runs after type conversion. It is
called for all sources, including prompts.

In Click 1.0, you can only raise the {func}`click.UsageError` but starting with Click 2.0, you can also raise the
{func}`click.BadParameter` error, which has the added advantage that it will automatically format the error message to also
contain the parameter name.

```python
def validate_rolls(ctx, param, value):
    if isinstance(value, tuple):
        return value

    try:
        rolls, _, dice = value.partition("d")
        return int(dice), int(rolls)
    except ValueError:
        raise click.BadParameter("format must be 'NdM'")

@click.command()
@click.option(
    "--rolls", type=click.UNPROCESSED, callback=validate_rolls,
    default="1d6", prompt=True,
)
def roll(rolls):
    sides, times = rolls
    click.echo(f"Rolling a {sides}-sided dice {times} time(s)")
```

```console
$ roll --rolls=42
Usage: roll [OPTIONS]
Try 'roll --help' for help.

Error: Invalid value for '--rolls': format must be 'NdM'

$ roll --rolls=2d12
Rolling a 12-sided dice 2 time(s)

$ roll
Rolls [1d6]: 42
Error: format must be 'NdM'
Rolls [1d6]: 2d12
Rolling a 12-sided dice 2 time(s)
```


## Parameter Modifications

Parameters (options and arguments) are forwarded to the command callbacks as you have seen. One common way to prevent a
parameter from being passed to the callback is the `expose_value` argument to a parameter which hides the parameter
entirely. The way this works is that the {func}`click.Context` object has a {func}`click.Context.params` attribute which is a
dictionary of all parameters. Whatever is in that dictionary is being passed to the callbacks.

This can be used to make up additional parameters. Generally this pattern is not recommended but in some cases it can be
useful. At the very least it's good to know that the system works this way.

```python
import urllib

def open_url(ctx, param, value):
    if value is not None:
        ctx.params['fp'] = urllib.urlopen(value)
        return value

@click.command()
@click.option('--url', callback=open_url)
def cli(url, fp=None):
    if fp is not None:
        click.echo(f"{url}: {fp.code}")
```

In this case the callback returns the URL unchanged but also passes a second `fp` value to the callback. What's more
recommended is to pass the information in a wrapper however:

```python
import urllib

class URL(object):

    def __init__(self, url, fp):
        self.url = url
        self.fp = fp

def open_url(ctx, param, value):
    if value is not None:
        return URL(value, urllib.urlopen(value))

@click.command()
@click.option('--url', callback=open_url)
def cli(url):
    if url is not None:
        click.echo(f"{url.url}: {url.fp.code}")
```

## Token Normalization

:::{versionadded} 2.0
:::

Starting with Click 2.0, it's possible to provide a function that is used for normalizing tokens. Tokens are option
names, choice values, or command values. This can be used to implement case insensitive options, for instance.

In order to use this feature, the context needs to be passed a function that performs the normalization of the token.
For instance, you could have a function that converts the token to lowercase:

```python
CONTEXT_SETTINGS = dict(token_normalize_func=lambda x: x.lower())

@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--name', default='Pete')
def cli(name):
    click.echo(f"Name: {name}")
```

And how it works on the command line:

```console
$ cli --NAME=Pete
Name: Pete
```

## Invoking Other Commands

Sometimes, it might be interesting to invoke one command from another command. This is a pattern that is generally
discouraged with Click, but possible nonetheless. For this, you can use the {func}`click.Context.invoke` or
{func}`click.Context.forward` methods.

They work similarly, but the difference is that {func}`click.Context.invoke` merely invokes another command with the arguments
you provide as a caller, whereas {func}`click.Context.forward` fills in the arguments from the current command. Both accept
the command as the first argument and everything else is passed onwards as you would expect.

Example:

```python
cli = click.Group()

@cli.command()
@click.option('--count', default=1)
def test(count):
    click.echo(f'Count: {count}')

@cli.command()
@click.option('--count', default=1)
@click.pass_context
def dist(ctx, count):
    ctx.forward(test)
    ctx.invoke(test, count=42)
```

And what it looks like:

```console
$ cli dist
Count: 1
Count: 42
```

(forwarding-unknown-options)=

## Forwarding Unknown Options

In some situations it is interesting to be able to accept all unknown options for further manual processing. Click can
generally do that as of Click 4.0, but it has some limitations that lie in the nature of the problem. The support for
this is provided through a parser flag called `ignore_unknown_options` which will instruct the parser to collect all
unknown options and to put them to the leftover argument instead of triggering a parsing error.

This can generally be activated in two different ways:

1. It can be enabled on custom {func}`click.Command` subclasses by changing the {func}`click.Command.ignore_unknown_options`
   attribute.
1. It can be enabled by changing the attribute of the same name on the context class
   ({attr}`click.Context.ignore_unknown_options`). This is best changed through the `context_settings` dictionary on the
   command.

For most situations the easiest solution is the second. Once the behavior is changed something needs to pick up those
leftover options (which at this point are considered arguments). For this again you have two options:

1. You can use {func}`click.pass_context` to get the context passed. This will only work if in addition to
   {func}`click.Context.ignore_unknown_options` you also set {func}`click.Context.allow_extra_args` as otherwise the command will
   abort with an error that there are leftover arguments. If you go with this solution, the extra arguments will be
   collected in {attr}`click.Context.args`.
1. You can attach an {func}`click.argument` with `nargs` set to `-1` which will eat up all leftover arguments. In this case
   it's recommended to set the `type` to {data}`click.UNPROCESSED` to avoid any string processing on those arguments as
   otherwise they are forced into unicode strings automatically which is often not what you want.

In the end you end up with something like this:

```python
import sys
from subprocess import call

@click.command(context_settings=dict(
    ignore_unknown_options=True,
))
@click.option('-v', '--verbose', is_flag=True, help='Enables verbose mode')
@click.argument('timeit_args', nargs=-1, type=click.UNPROCESSED)
def cli(verbose, timeit_args):
    """A fake wrapper around Python's timeit."""
    cmdline = ['echo', 'python', '-mtimeit'] + list(timeit_args)
    if verbose:
        click.echo(f"Invoking: {' '.join(cmdline)}")
    call(cmdline)
```

And what it looks like:

```console
$ cli --help
Usage: cli [OPTIONS] [TIMEIT_ARGS]...

  A fake wrapper around Python's timeit.

Options:
  -v, --verbose  Enables verbose mode
  --help         Show this message and exit.

$ cli -n 100 'a = 1; b = 2; a * b'
python -mtimeit -n 100 a = 1; b = 2; a * b

$ cli -v 'a = 1; b = 2; a * b'
Invoking: echo python -mtimeit a = 1; b = 2; a * b
python -mtimeit a = 1; b = 2; a * b
```

As you can see the verbosity flag is handled by Click, everything else ends up in the `timeit_args` variable for further
processing which then for instance, allows invoking a subprocess. There are a few things that are important to know
about how this ignoring of unhandled flag happens:

- Unknown long options are generally ignored and not processed at all. So for instance if `--foo=bar` or `--foo bar` are
  passed they generally end up like that. Note that because the parser cannot know if an option will accept an argument
  or not, the `bar` part might be handled as an argument.
- Unknown short options might be partially handled and reassembled if necessary. For instance in the above example there
  is an option called `-v` which enables verbose mode. If the command would be ignored with `-va` then the `-v` part
  would be handled by Click (as it is known) and `-a` would end up in the leftover parameters for further processing.
- Depending on what you plan on doing you might have some success by disabling interspersed arguments
  ({func}`click.Context.allow_interspersed_args`) which instructs the parser to not allow arguments and options to be mixed.
  Depending on your situation this might improve your results.

Generally though the combined handling of options and arguments from your own commands and commands from another
application are discouraged and if you can avoid it, you should. It's a much better idea to have everything below a
subcommand be forwarded to another application than to handle some arguments yourself.

## Managing Resources

It can be useful to open a resource in a group, to be made available to subcommands. Many types of resources need to be
closed or otherwise cleaned up after use. The standard way to do this in Python is by using a context manager with the
`with` statement.

For example, the `Repo` class from {doc}`complex` might actually be defined as a context manager:

```python
class Repo:
    def __init__(self, home=None):
        self.home = os.path.abspath(home or ".")
        self.db = None

    def __enter__(self):
        path = os.path.join(self.home, "repo.db")
        self.db = open_database(path)
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.db.close()
```

Ordinarily, it would be used with the `with` statement:

```python
with Repo() as repo:
    repo.db.query(...)
```


However, a `with` block in a group would exit and close the database before it could be used by a subcommand.

Instead, use the context's {meth}`~click.Context.with_resource` method to enter the context manager and return the
resource. When the group and any subcommands finish, the context's resources are cleaned up.

```python
@click.group()
@click.option("--repo-home", default=".repo")
@click.pass_context
def cli(ctx, repo_home):
    ctx.obj = ctx.with_resource(Repo(repo_home))

@cli.command()
@click.pass_obj
def log(obj):
    # obj is the repo opened in the cli group
    for entry in obj.db.query(...):
        click.echo(entry)
```

If the resource isn't a context manager, usually it can be wrapped in one using something from {mod}`contextlib`. If
that's not possible, use the context's {meth}`~click.Context.call_on_close` method to register a cleanup function.

```python
@click.group()
@click.option("--name", default="repo.db")
@click.pass_context
def cli(ctx, repo_home):
    ctx.obj = db = open_db(repo_home)

    @ctx.call_on_close
    def close_db():
        db.record_use()
        db.save()
        db.close()
```

:::{versionchanged} 8.2 
`Context.call_on_close` and context managers registered via `Context.with_resource` will be
closed when the CLI exits. These were previously not called on exit.
:::
