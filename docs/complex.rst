.. _complex-guide:

Complex Applications
====================

.. currentmodule:: click

Click is designed to write complex and simple CLI tools alike.  However
the power of its design is the ability to arbitrarily nest systems
together.  For instance in case you have ever used Django you will have
realized that it provides a command line utility.  But so does Celery for
instance.  So when using Celery with Django there are two tools that need
to interact with each other and be cross configured.

In a theoretical world of two separate Click command line utilities they
can solve this problem by nesting one inside the other.  For instance the
web framework could also load the commands for the message queue
framework.

Basic Concepts
--------------

To understand how this works you need to understand two concepts: contexts
and the calling convention.

Contexts
````````

Whenever a Click command is executed a :class:`Context` object is created
which holds state for this particular invocation.  For instance it
remembers parsed parameters, what command created it, which resources need
to be cleaned up at the end of the function and so forth.  It also holds
an application defined object optionally.

Context objects build a linked list until they hit top one.  Each context
is linked to the parent context.  This allows a command to work below
another command and store its own information there without having to be
afraid of messing up the state of the parent command.

Because the parent data is however available it's possible to navigate to
it if needed.

Most of the time you don't see the context object, but when writing more
complex applications it comes in handy.  This brings us to the next point.

Calling Convention
``````````````````

When a Click command callback is executed it's passed all the non hidden
parameters as keyword arguments.  Notably absent is the context.  However
a callback can opt-into being passed the context object by marking itself
with :func:`pass_context`.

So how do you invoke a command callback if you don't know if it should
receive the context or not?  The answer is that the context itself
provides a helper function (:meth:`Context.invoke`) which can do this for
you.  It accepts the callback as first argument and then invokes the
function correctly.

Building a Git
--------------

In this example we want to build a command line tool that resembles a
version control system a bit.  Systems like git usually provide one
over-arching command that already accepts some parameters and
configuration, and then has extra subcommands that do other things.

The Root Command
````````````````

At the top level we need a group that can hold all our commands.  In this
case we use the basic :func:`click.group` which allows us to register
other click commands below it.

For this command we also want to accept some parameters that configure the
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


So let's understand what this does.  We create a group command which can
have subcommands.  When it is invoked it will create an instance of a
``Repo`` class.  This holds the state for our command line tool.  In this
case it just remembers some parameters but at this point it could also
start loading config files and so on.

This state object is then remembered as :attr:`~Context.obj` on the
context.  This is a special attribute where commands are supposed to
remember what they need to pass on to their children.

In order for this to work we need to mark our function with
:func:`pass_context` because otherwise the context object would be
entirely hidden from us.

The First Child Command
```````````````````````

So let's add our first child command to it.  Let's go with the clone
command:

.. click:example::

    @cli.command()
    @click.argument('src')
    @click.argument('dest', required=False)
    def clone(src, dest):
        pass

So now we have a clone command, but how do we get access to the repo?  As
you can imagine one way is to use the :func:`pass_context` function which
again will make our callback also get the context passed on which we
memorized the repo.  Even better there is a second version of this
decorator called :func:`pass_obj` which will just pass the stored object,
in our case the repo:

.. click:example::

    @cli.command()
    @click.argument('src')
    @click.argument('dest', required=False)
    @click.pass_obj
    def clone(repo, src, dest):
        pass

Interleaved Commands
````````````````````

While not relevant for this particular program we want to build there is
also quite good support for interleaving systems.  Imagine for instance
there would be this super cool plugin for our version control system that
needs a lot of configuration and wants to store its own configuration as
:attr:`~Context.obj`.  If we would then attach another command below that,
all the sudden we would get the plugin config instead of our repo object.

One obvious way is to store a reference to the repo on the plugin but then
a command needs to be aware that it's attached below such a plugin.

There is a much better system by taking advantage of the linked nature of
contexts.  We know that the plugin context is linked to the context that
created our repo.  Because of that we can start a search for the last
level where the object stored on the context was a repo.

Built-in support for this is provided by the :func:`make_pass_decorator`
factory which will create decorators for us that find objects (it
internally calls into :meth:`Context.find_object`).  So in our case we
know that we want to find the closest ``Repo`` object.  So let's make a
decorator for this:

.. click:example::

    pass_repo = click.make_pass_decorator(Repo)

If we now use ``pass_repo`` instead of ``pass_obj`` we will always get a
repo instead of something else:

.. click:example::

    @cli.command()
    @click.argument('src')
    @click.argument('dest', required=False)
    @pass_repo
    def clone(repo, src, dest):
        pass

Ensuring Objects
````````````````

The above example only works if there was an outer command that created a
``Repo`` object and stored it on the context.  For some more advanced use
cases this might be a problem for you.  The default behavior of
:func:`make_pass_decorator` is to call into :meth:`Context.find_object`
which will find the object.  If it can't find the object it will raise an
error.  The alternative behavior is to use :meth:`Context.ensure_object`
which will find the object, or if it cannot find it, will create one and
store it on the innermost context.  This behavior can also be enabled for
:func:`make_pass_decorator` by passing ``ensure=True``:

.. click:example::

    pass_repo = click.make_pass_decorator(Repo, ensure=True)

In this case the innermost context gets such an object created if it's
missing.  This might replace objects being placed there earlier.  In this
case the command stays executable, even if the outer command does not run.
For this to work the object type needs to have a constructor that accepts
no arguments.

As such it runs standalone:

.. click:example::

    @click.command()
    @pass_repo
    def cp(repo):
        click.utils.echo(repo)

As you can see:

.. click:run::

    invoke(cp, [])
