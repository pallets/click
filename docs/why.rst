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

click is actually implemented as a wrapper around ``optparse`` and does
not implement any parsing itself.  The reason it's not based on
``argparse`` is that ``argparse`` does not allow proper nesting of
commands by design and has some deficiencies when it comes to POSIX
compliant argument handling.

In case ``optparse`` ever gets deprecated and removed from Python,
``click`` will ship a version of it.

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
