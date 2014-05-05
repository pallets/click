Why Click?
==========

There are so many libraries out there for writing command line utilities,
why does click exist?

This question is easy to answer: because there is not a single command
line utility for Python out there which ticks the following boxes:

*   is lazily composable without restrictions
*   fully follows the UNIX command line conventions
*   supports loading values from environment variables out of the box
*   supports for prompting of custom values
*   is fully nestable and composable
*   works the same on Python 2 and 3
*   supports file handling out of the box

There are many alternatives to click and you can have a look at them if
you enjoy them better.  The obvious ones are ``optparse`` and ``argparse``
from the standard library.

click is actually implemented as a wrapper around a mild fork of
``optparse`` and does not implement any parsing itself.  The reason it's
not based on ``argparse`` is that ``argparse`` does not allow proper
nesting of commands by design and has some deficiencies when it comes to
POSIX compliant argument handling.

Click is designed to be fun to work with and at the same time not stand in
your way.  It's not overly flexible at the same time either.  Currently
for instance it does not allow you to customize the help pages too much.
This is intentional because click is designed to allow you to nest command
line utilities.  The idea is that you can have a system that works
together with another system by tacking two click instances together and
they will continue working as they should.

Too much customizability would break this promise.

Click was written to support the `Flask <http://flask.pocoo.org/>`_
microframework ecosystem because no tool could provide it with the
functionality it needed.

To get an understanding of what click is all about I strongly recommend
looking at the :ref:`complex-guide` chapter to see what it's useful for.

Why not Argparse?
-----------------

Click is internally based on optparse instead of argparse.  This however
is an implementation detail that a user does not have to be concerned
with.  The reason however click is not using argparse is that it has some
problematic behaviors that make handling arbitrary command line interfaces
hard:

*   argparse has builtin magic behavior to guess if something is an
    argument or an option.  This becomes a problem when dealing with
    incomplete command lines as it's not possible to know without having a
    full understanding of the command line how the parser is going to
    behave.  This goes against click's ambitions of dispatching to
    subparsers.
*   argparse currently does not support disabling of interspearsed
    arguments.  Without this feature it's not possible to safely implement
    click's nested parsing nature.

Why not Docopt etc.?
--------------------

Docopt and many tools like it are cool in how they work but very few of
these tools deal with nesting of commands and composability in a way like
click.  To the best of the developer's knowledge, click is the first
Python library that tries to aim for composability of applications that
goes beyond what the system itself supports.

Docopt for instance acts by parsing your help pages and then parsing
according to those rules.  The side effect of this is that docopt is quite
rigid in how it handles the command line interface.  The upside of docopt
is that it gives you strong control over your help page, the downside is
that due to that it cannot rewrap your output for the current terminal
width and it makes translations hard.  On top of that docopt is restricted
to basic parsing.  It does not handle argument dispatching and callback
invocation or types.  This means there is a lot of code that needs to be
written in addition to the basic help page to handle the parsing results.

Most of all however it makes composability hard.  While docopt does
support dispatching to subcommands, it for instance does not directly
support any kind of automatic subcommand enumeration based on what's
available or it does not enforce subcommands to work in a consistent way.

This is fine, but it's different from how click wants to work.  Click aims
to support fully composable command line user interfaces by doing this:

-   click does not just parse, it also dispatches to the appropriate code.
-   click has a strong concept of an invocation context that allows
    subcommands to respond to data from the parent command.
-   click has strong information available for all parameters and commands
    so that it can generate unified help pages for the full CLI and to
    assist the user in converting the input data as necessary.
-   click has strong understanding of what types are and can give the user
    consistent error messages if something goes wrong.  A subcommand
    written by a different developer will not suddenly die with a
    different error messsage because it's manually handled.
-   click has enough meta information available for its whole program
    that it can evolve over time to improve the user experience without
    forcing developers to adjust their programs.  For instance if click
    decides to change how help pages are formatted, all click programs
    will automatically benefit from this.

The aim of click is to make composable systems, whereas the aim of docopt
is to build the most beautiful and hand-crafted command line interfaces.
These two goals are conflicting with each other in subtle ways.  Click
actively prevents people from implementing certain patterns in order to
achieve unified command line interfaces.  You have very little input on
reformatting your help pages for instance.


Why Hardcoded Behaviors?
------------------------

The other question is why click goes away from optparse and hardcodes
certain behaviors instead of staying configurable.  There are multiple
reasons for this.  The biggest one is that too much configurability makes
it hard to achieve a consistent command line experience.

The best example for this is optparse's ``callback`` functionality for
accepting arbitrary number of arguments.  Due to syntactical ambiguities
on the command line there is no way to implement fully variadic arguments.
There are always tradeoffs that need to be made and in case of
``argparse`` these tradeoffs have been critical enough, that a system like
click cannot even be implemented on top of it.

In this particular case click attempts to stay with a handful of accepted
paradigms for building command line interfaces that can be well documented
and tested.
