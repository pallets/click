# Why Click?

There are so many libraries out there for writing command line utilities; why does Click exist?

This question is easy to answer: because there is not a single command line utility for Python out there which ticks the
following boxes:

- Is lazily composable without restrictions.
- Supports implementation of Unix/POSIX command line conventions.
- Supports loading values from environment variables out of the box.
- Support for prompting of custom values.
- Is fully nestable and composable.
- Supports file handling out of the box.
- Comes with useful common helpers (getting terminal dimensions, ANSI colors, fetching direct keyboard input, screen
  clearing, finding config paths, launching apps and editors, etc.).

There are many alternatives to Click; the obvious ones are `optparse` and `argparse` from the standard library. Have a
look to see if something else resonates with you.

Click actually implements its own parsing of arguments and does not use `optparse` or `argparse` following the
`optparse` parsing behavior. The reason it's not based on `argparse` is that `argparse` does not allow proper nesting of
commands by design and has some deficiencies when it comes to POSIX compliant argument handling.

Click is designed to be fun and customizable but not overly flexible. For instance, the customizability of help pages is
constrained. This constraint is intentional because Click promises multiple Click instances will continue to function as
intended when strung together.

Too much customizability would break this promise.

Click was written to support the [Flask](https://palletsprojects.com/p/flask/) microframework ecosystem because no tool
could provide it with the functionality it needed.

To get an understanding of what Click is all about, I strongly recommend looking at the {ref}`complex-guide` chapter.

## Why not Argparse?

Click is internally based on `optparse` instead of `argparse`. This is an implementation detail that a user does not
have to be concerned with. Click is not based on `argparse` because it has some behaviors that make handling arbitrary
command line interfaces hard:

- `argparse` has built-in behavior to guess if something is an argument or an option. This becomes a problem when
  dealing with incomplete command lines; the behaviour becomes unpredictable without full knowledge of a command line.
  This goes against Click's ambitions of dispatching to subparsers.
- `argparse` does not support disabling interspersed arguments. Without this feature, it's not possible to safely
  implement Click's nested parsing.

## Why not Docopt etc.?

Docopt, and many tools like it, are cool in how they work, but very few of these tools deal with nesting of commands and
composability in a way like Click. To the best of the developer's knowledge, Click is the first Python library that aims
to create a level of composability of applications that goes beyond what the system itself supports.

Docopt, for instance, acts by parsing your help pages and then parsing according to those rules. The side effect of this
is that docopt is quite rigid in how it handles the command line interface. The upside of docopt is that it gives you
strong control over your help page; the downside is that due to this it cannot rewrap your output for the current
terminal width, and it makes translations hard. On top of that, docopt is restricted to basic parsing. It does not
handle argument dispatching and callback invocation or types. This means there is a lot of code that needs to be written
in addition to the basic help page to handle the parsing results.

Most of all, however, it makes composability hard. While docopt does support dispatching to subcommands, it, for
instance, does not directly support any kind of automatic subcommand enumeration based on what's available or it does
not enforce subcommands to work in a consistent way.

This is fine, but it's different from how Click wants to work. Click aims to support fully composable command line user
interfaces by doing the following:

- Click does not just parse, it also dispatches to the appropriate code.
- Click has a strong concept of an invocation context that allows subcommands to respond to data from the parent
  command.
- Click has strong information available for all parameters and commands, so it can generate unified help pages for the
  full CLI and assist the user in converting the input data as necessary.
- Click has a strong understanding of what types are, and it can give the user consistent error messages if something
  goes wrong. A subcommand written by a different developer will not suddenly die with a different error message because
  it's manually handled.
- Click has enough meta information available for its whole program to evolve over time and improve the user experience
  without forcing developers to adjust their programs. For instance, if Click decides to change how help pages are
  formatted, all Click programs will automatically benefit from this.

The aim of Click is to make composable systems. Whereas, the aim of docopt is to build the most beautiful and
hand-crafted command line interfaces. These two goals conflict with one another in subtle ways. Click actively prevents
people from implementing certain patterns in order to achieve unified command line interfaces. For instance, as a
developer, you are given very little choice in formatting your help pages.

## Why Hardcoded Behaviors?

The other question is why Click goes away from optparse and hardcodes certain behaviors instead of staying configurable.
There are multiple reasons for this. The biggest one is that too much configurability makes it hard to achieve a
consistent command line experience.

The best example for this is optparse's `callback` functionality for accepting an arbitrary number of arguments. Due to
syntactical ambiguities on the command line, there is no way to implement fully variadic arguments. There are always
tradeoffs that need to be made and in case of `argparse` these tradeoffs have been critical enough, that a system like
Click cannot even be implemented on top of it.

In this particular case, Click attempts to stay with a handful of accepted paradigms for building command line
interfaces that can be well documented and tested.

## Why No Auto Correction?

The question came up why Click does not auto correct parameters given that even optparse and `argparse` support
automatic expansion of long arguments. The reason for this is that it's a liability for backwards compatibility. If
people start relying on automatically modified parameters and someone adds a new parameter in the future, the script
might stop working. These kinds of problems are hard to find, so Click does not attempt to be magical about this.

This sort of behavior however can be implemented on a higher level to support things such as explicit aliases. For more
information see {ref}`aliases`.
