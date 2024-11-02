.. _complex-guide:

Complex Applications
====================

.. currentmodule:: click

Click is designed to assist with the creation of complex and simple CLI tools
alike.  However, the power of its design is the ability to arbitrarily nest
systems together.  For instance, if you have ever used Django, you will
have realized that it provides a command line utility, but so does Celery.
When using Celery with Django, there are two tools that need to interact with
each other and be cross-configured.

In a theoretical world of two separate Click command line utilities, they
could solve this problem by nesting one inside the other.  For instance, the
web framework could also load the commands for the message queue framework.

Basic Concepts
--------------

To understand how this works, you need to understand two concepts: contexts
and the calling convention.

Contexts
````````

Whenever a Click command is executed, a :class:`Context` object is created
which holds state for this particular invocation.  It remembers parsed
parameters, what command created it, which resources need to be cleaned up
at the end of the function, and so forth.  It can also optionally hold an
application-defined object.

Context objects build a linked list until they hit the top one.  Each context
is linked to a parent context.  This allows a command to work below
another command and store its own information there without having to be
afraid of altering up the state of the parent command.

Because the parent data is available, however, it is possible to navigate to
it if needed.

Most of the time, you do not see the context object, but when writing more
complex applications it comes in handy.  This brings us to the next point.

Calling Convention
``````````````````

When a Click command callback is executed, it's passed all the non-hidden
parameters as keyword arguments.  Notably absent is the context.  However,
a callback can opt into being passed to the context object by marking itself
with :func:`pass_context`.

So how do you invoke a command callback if you don't know if it should
receive the context or not?  The answer is that the context itself
provides a helper function (:meth:`Context.invoke`) which can do this for
you.  It accepts the callback as first argument and then invokes the
function correctly.

Building a Git Clone
--------------------

In this example, we want to build a command line tool that resembles a
version control system.  Systems like Git usually provide one
over-arching command that already accepts some parameters and
configuration, and then have extra subcommands that do other things.

The Root Command
````````````````

At the top level, we need a group that can hold all our commands.  In this
case, we use the basic :func:`click.group` which allows us to register
other Click commands below it.

For this command, we also want to accept some parameters that configure the
state of our tool:

.. click:example::

    import os
    import click


    class Repo(object):
        def __init__(self, home=None, debug=False):
            self.home = os.path.abspath(home or '.')
            self.debug = debug


    @click.group()
    @click.option('--repo-home', envvar='REPO_HOME', default='.repo')
    @click.option('--debug/--no-debug', default=False,
                  envvar='REPO_DEBUG')
    @click.pass_context
    def cli(ctx, repo_home, debug):
        ctx.obj = Repo(repo_home, debug)


Let's understand what this does.  We create a group command which can
have subcommands.  When it is invoked, it will create an instance of a
``Repo`` class.  This holds the state for our command line tool.  In this
case, it just remembers some parameters, but at this point it could also
start loading configuration files and so on.

This state object is then remembered by the context as :attr:`~Context.obj`.
This is a special attribute where commands are supposed to remember what
they need to pass on to their children.

In order for this to work, we need to mark our function with
:func:`pass_context`, because otherwise, the context object would be
entirely hidden from us.

The First Child Command
```````````````````````

Let's add our first child command to it, the clone command:

.. click:example::

    @cli.command()
    @click.argument('src')
    @click.argument('dest', required=False)
    def clone(src, dest):
        pass

So now we have a clone command, but how do we get access to the repo?  As
you can imagine, one way is to use the :func:`pass_context` function which
again will make our callback also get the context passed on which we
memorized the repo.  However, there is a second version of this decorator
called :func:`pass_obj` which will just pass the stored object, (in our case
the repo):

.. click:example::

    @cli.command()
    @click.argument('src')
    @click.argument('dest', required=False)
    @click.pass_obj
    def clone(repo, src, dest):
        pass

Interleaved Commands
````````````````````

While not relevant for the particular program we want to build, there is
also quite good support for interleaving systems.  Imagine for instance that
there was a super cool plugin for our version control system that needed a
lot of configuration and wanted to store its own configuration as
:attr:`~Context.obj`.  If we would then attach another command below that,
we would all of a sudden get the plugin configuration instead of our repo
object.

One obvious way to remedy this is to store a reference to the repo in the
plugin, but then a command needs to be aware that it's attached below such a
plugin.

There is a much better system that can be built by taking advantage of the
linked nature of contexts.  We know that the plugin context is linked to the
context that created our repo.  Because of that, we can start a search for
the last level where the object stored by the context was a repo.

Built-in support for this is provided by the :func:`make_pass_decorator`
factory, which will create decorators for us that find objects (it
internally calls into :meth:`Context.find_object`).  In our case, we
know that we want to find the closest ``Repo`` object, so let's make a
decorator for this:

.. click:example::

    pass_repo = click.make_pass_decorator(Repo)

If we now use ``pass_repo`` instead of ``pass_obj``, we will always get a
repo instead of something else:

.. click:example::

    @cli.command()
    @click.argument('src')
    @click.argument('dest', required=False)
    @pass_repo
    def clone(repo, src, dest):
        pass

Ensuring Object Creation
````````````````````````

The above example only works if there was an outer command that created a
``Repo`` object and stored it in the context.  For some more advanced use
cases, this might become a problem.  The default behavior of
:func:`make_pass_decorator` is to call :meth:`Context.find_object`
which will find the object.  If it can't find the object,
:meth:`make_pass_decorator` will raise an error.
The alternative behavior is to use :meth:`Context.ensure_object`
which will find the object, and if it cannot find it, will create one and
store it in the innermost context.  This behavior can also be enabled for
:func:`make_pass_decorator` by passing ``ensure=True``:

.. click:example::

    pass_repo = click.make_pass_decorator(Repo, ensure=True)

In this case, the innermost context gets an object created if it is
missing.  This might replace objects being placed there earlier.  In this
case, the command stays executable, even if the outer command does not run.
For this to work, the object type needs to have a constructor that accepts
no arguments.

As such it runs standalone:

.. click:example::

    @click.command()
    @pass_repo
    def cp(repo):
        click.echo(isinstance(repo, Repo))

As you can see:

.. click:run::

    invoke(cp, [])

Lazily Loading Subcommands
--------------------------

Large CLIs and CLIs with slow imports may benefit from deferring the loading of
subcommands. The interfaces which support this mode of use are
:meth:`Group.list_commands` and :meth:`Group.get_command`. A custom
:class:`Group` subclass can implement a lazy loader by storing extra data such
that :meth:`Group.get_command` is responsible for running imports.

Since the primary case for this is a :class:`Group` which loads its subcommands lazily,
the following example shows a lazy-group implementation.

.. warning::

   Lazy loading of python code can result in hard to track down bugs, circular imports
   in order-dependent codebases, and other surprising behaviors. It is recommended that
   this technique only be used in concert with testing which will at least run the
   ``--help`` on each subcommand. That will guarantee that each subcommand can be loaded
   successfully.

Defining the Lazy Group
```````````````````````

The following :class:`Group` subclass adds an attribute, ``lazy_subcommands``, which
stores a mapping from subcommand names to the information for importing them.

.. code-block:: python

    # in lazy_group.py
    import importlib
    import click

    class LazyGroup(click.Group):
        def __init__(self, *args, lazy_subcommands=None, **kwargs):
            super().__init__(*args, **kwargs)
            # lazy_subcommands is a map of the form:
            #
            #   {command-name} -> {module-name}.{command-object-name}
            #
            self.lazy_subcommands = lazy_subcommands or {}

        def list_commands(self, ctx):
            base = super().list_commands(ctx)
            lazy = sorted(self.lazy_subcommands.keys())
            return base + lazy

        def get_command(self, ctx, cmd_name):
            if cmd_name in self.lazy_subcommands:
                return self._lazy_load(cmd_name)
            return super().get_command(ctx, cmd_name)

        def _lazy_load(self, cmd_name):
            # lazily loading a command, first get the module name and attribute name
            import_path = self.lazy_subcommands[cmd_name]
            modname, cmd_object_name = import_path.rsplit(".", 1)
            # do the import
            mod = importlib.import_module(modname)
            # get the Command object from that module
            cmd_object = getattr(mod, cmd_object_name)
            # check the result to make debugging easier
            if not isinstance(cmd_object, click.Command):
                raise ValueError(
                    f"Lazy loading of {import_path} failed by returning "
                    "a non-command object"
                )
            return cmd_object

Using LazyGroup To Define a CLI
```````````````````````````````

With ``LazyGroup`` defined, it's now possible to write a group which lazily loads its
subcommands like so:

.. code-block:: python

    # in main.py
    import click
    from lazy_group import LazyGroup

    @click.group(
        cls=LazyGroup,
        lazy_subcommands={"foo": "foo.cli", "bar": "bar.cli"},
        help="main CLI command for lazy example",
    )
    def cli():
        pass

.. code-block:: python

    # in foo.py
    import click

    @click.group(help="foo command for lazy example")
    def cli():
        pass

.. code-block:: python

    # in bar.py
    import click
    from lazy_group import LazyGroup

    @click.group(
        cls=LazyGroup,
        lazy_subcommands={"baz": "baz.cli"},
        help="bar command for lazy example",
    )
    def cli():
        pass

.. code-block:: python

    # in baz.py
    import click

    @click.group(help="baz command for lazy example")
    def cli():
        pass


What triggers Lazy Loading?
```````````````````````````

There are several events which may trigger lazy loading by running the
:meth:`Group.get_command` function.
Some are intuititve, and some are less so.

All cases are described with respect to the above example, assuming the main program
name is ``cli``.

1. Command resolution. If a user runs ``cli bar baz``, this must first resolve ``bar``,
   and then resolve ``baz``. Each subcommand resolution step does a lazy load.
2. Helptext rendering. In order to get the short help description of subcommands,
   ``cli --help`` will load ``foo`` and ``bar``. Note that it will still not load
   ``baz``.
3. Shell completion. In order to get the subcommands of a lazy command, ``cli <TAB>``
   will need to resolve the subcommands of ``cli``. This process will trigger the lazy
   loads.

Further Deferring Imports
`````````````````````````

It is possible to make the process even lazier, but it is generally more difficult the
more you want to defer work.

For example, subcommands could be represented as a custom :class:`Command` subclass
which defers importing the command until it is invoked, but which provides
:meth:`Command.get_short_help_str` in order to support completions and helptext.
More simply, commands can be constructed whose callback functions defer any actual work
until after an import.

This command definition provides ``foo``, but any of the work associated with importing
the "real" callback function is deferred until invocation time:

.. click:example::

    @click.command()
    @click.option("-n", type=int)
    @click.option("-w", type=str)
    def foo(n, w):
        from mylibrary import foo_concrete

        foo_concrete(n, w)

Because Click builds helptext and usage info from options, arguments, and command
attributes, it has no awareness that the underlying function is in any way handling a
deferred import. Therefore, all Click-provided utilities and functionality will work
as normal on such a command.
