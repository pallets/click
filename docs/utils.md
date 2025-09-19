# Utilities

```{currentmodule} click
```

Besides the functionality that Click provides to interface with argument parsing and handling, it also provides a bunch
of addon functionality that is useful for writing command line utilities.

## Printing to Stdout

The most obvious helper is the {func}`echo` function, which in many ways works like the Python `print` statement or
function. The main difference is that it works the same in many different terminal environments.

Example:

```python
import click

click.echo('Hello World!')
```

It can output both text and binary data. It will emit a trailing newline by default, which needs to be suppressed by
passing `nl=False`:

```python
click.echo(b'\xe2\x98\x83', nl=False)
```

Last but not least {func}`echo` uses click's intelligent internal output streams to stdout and stderr which support
unicode output on the Windows console. This means for as long as you are using `click.echo` you can output unicode
characters (there are some limitations on the default font with regards to which characters can be displayed).

```{versionadded} 6.0
```

Click emulates output streams on Windows to support unicode to the Windows console through separate APIs. For more
information see {doc}`wincmd`.

```{versionadded} 3.0
```

You can also easily print to standard error by passing `err=True`:

```python
click.echo('Hello World!', err=True)
```

(ansi-colors)=

## ANSI Colors

```{versionadded} 2.0
```

The {func}`echo` function supports ANSI colors and styles. On Windows this uses [colorama](https://pypi.org/project/colorama/).

Primarily this means that:

- Click's {func}`echo` function will automatically strip ANSI color codes if the stream is not connected to a terminal.
- the {func}`echo` function will transparently connect to the terminal on Windows and translate ANSI codes to terminal
  API calls. This means that colors will work on Windows the same way they do on other operating systems.

On Windows, Click uses colorama without calling `colorama.init()`. You can still call that in your code, but it's not
required for Click.

For styling a string, the {func}`style` function can be used:

```python
import click

click.echo(click.style('Hello World!', fg='green'))
click.echo(click.style('Some more text', bg='blue', fg='white'))
click.echo(click.style('ATTENTION', blink=True, bold=True))
```

The combination of {func}`echo` and {func}`style` is also available in a single function called {func}`secho`:

```python
click.secho('Hello World!', fg='green')
click.secho('Some more text', bg='blue', fg='white')
click.secho('ATTENTION', blink=True, bold=True)
```

## Pager Support

In some situations, you might want to show long texts on the terminal and let a user scroll through it. This can be
achieved by using the {func}`echo_via_pager` function which works similarly to the {func}`echo` function, but always
writes to stdout and, if possible, through a pager.

Example:

```{eval-rst}
.. click:example::
    @click.command()
    def less():
        click.echo_via_pager("\n".join(f"Line {idx}" for idx in range(200)))
```

If you want to use the pager for a lot of text, especially if generating everything in advance would take a lot of time,
you can pass a generator (or generator function) instead of a string:

```{eval-rst}
.. click:example::
    def _generate_output():
        for idx in range(50000):
            yield f"Line {idx}\n"

    @click.command()
    def less():
        click.echo_via_pager(_generate_output())
```

## Screen Clearing

```{versionadded} 2.0
```

To clear the terminal screen, you can use the {func}`clear` function that is provided starting with Click 2.0. It does
what the name suggests: it clears the entire visible screen in a platform-agnostic way:

```python
import click
click.clear()
```

## Getting Characters from Terminal

```{versionadded} 2.0
```

Normally, when reading input from the terminal, you would read from standard input. However, this is buffered input and
will not show up until the line has been terminated. In certain circumstances, you might not want to do that and instead
read individual characters as they are being written.

For this, Click provides the {func}`getchar` function which reads a single character from the terminal buffer and
returns it as a Unicode character.

Note that this function will always read from the terminal, even if stdin is instead a pipe.

Example:

```python
import click

click.echo('Continue? [yn] ', nl=False)
c = click.getchar()
click.echo()
if c == 'y':
    click.echo('We will go on')
elif c == 'n':
    click.echo('Abort!')
else:
    click.echo('Invalid input :(')
```

Note that this reads raw input, which means that things like arrow keys will show up in the platform's native escape
format. The only characters translated are `^C` and `^D` which are converted into keyboard interrupts and end of file
exceptions respectively. This is done because otherwise, it's too easy to forget about that and to create scripts that
cannot be properly exited.

## Waiting for Key Press

```{versionadded} 2.0
```

Sometimes, it's useful to pause until the user presses any key on the keyboard. This is especially useful on Windows
where `cmd.exe` will close the window at the end of the command execution by default, instead of waiting.

In click, this can be accomplished with the {func}`pause` function. This function will print a quick message to the
terminal (which can be customized) and wait for the user to press a key. In addition to that, it will also become a NOP
(no operation instruction) if the script is not run interactively.

Example:

```python
import click
click.pause()
```

## Launching Editors

```{versionadded} 2.0
```

Click supports launching editors automatically through {func}`edit`. This is very useful for asking users for multi-line
input. It will automatically open the user's defined editor or fall back to a sensible default. If the user closes the
editor without saving, the return value will be `None`, otherwise the entered text.

Example usage:

```python
import click

def get_commit_message():
    MARKER = '# Everything below is ignored\n'
    message = click.edit('\n\n' + MARKER)
    if message is not None:
        return message.split(MARKER, 1)[0].rstrip('\n')
```

Alternatively, the function can also be used to launch editors for files by a specific filename. In this case, the
return value is always `None`.

Example usage:

```python
import click
click.edit(filename='/etc/passwd')
```

## Launching Applications

```{versionadded} 2.0
```

Click supports launching applications through {func}`launch`. This can be used to open the default application
associated with a URL or filetype. This can be used to launch web browsers or picture viewers, for instance. In addition
to this, it can also launch the file manager and automatically select the provided file.

Example usage:

```python
click.launch("https://click.palletsprojects.com/")
click.launch("/my/downloaded/file.txt", locate=True)
```

## Printing Filenames

Because filenames might not be Unicode, formatting them can be a bit tricky.

The way this works with click is through the {func}`format_filename` function. It does a best-effort conversion of the
filename to Unicode and will never fail. This makes it possible to use these filenames in the context of a full Unicode
string.

Example:

```python
click.echo(f"Path: {click.format_filename(b'foo.txt')}")
```

## Standard Streams

For command line utilities, it's very important to get access to input and output streams reliably. Python generally
provides access to these streams through `sys.stdout` and friends, but unfortunately, there are API differences between
2.x and 3.x, especially with regards to how these streams respond to Unicode and binary data.

Because of this, click provides the {func}`get_binary_stream` and {func}`get_text_stream` functions, which produce
consistent results with different Python versions and for a wide variety of terminal configurations.

The end result is that these functions will always return a functional stream object (except in very odd cases; see
{doc}`/unicode-support`).

Example:

```python
import click

stdin_text = click.get_text_stream('stdin')
stdout_binary = click.get_binary_stream('stdout')
```

```{versionadded} 6.0
```

Click now emulates output streams on Windows to support unicode to the Windows console through separate APIs. For more
information see {doc}`wincmd`.

## Intelligent File Opening

```{versionadded} 3.0
```

Starting with Click 3.0 the logic for opening files from the {func}`File` type is exposed through the {func}`open_file`
function. It can intelligently open stdin/stdout as well as any other file.

Example:

```python
import click

stdout = click.open_file('-', 'w')
test_file = click.open_file('test.txt', 'w')
```

If stdin or stdout are returned, the return value is wrapped in a special file where the context manager will prevent
the closing of the file. This makes the handling of standard streams transparent and you can always use it like this:

```python
with click.open_file(filename, 'w') as f:
    f.write('Hello World!\n')
```

## Finding Application Folders

```{versionadded} 2.0
```

Very often, you want to open a configuration file that belongs to your application. However, different operating systems
store these configuration files in different locations depending on their standards. Click provides a
{func}`get_app_dir` function which returns the most appropriate location for per-user config files for your application
depending on the OS.

Example usage:

```python
import os
import click
import ConfigParser

APP_NAME = 'My Application'
def read_config():
cfg = os.path.join(click.get_app_dir(APP_NAME), 'config.ini')
parser = ConfigParser.RawConfigParser()
parser.read([cfg])
rv = {}
for section in parser.sections():
    for key, value in parser.items(section):
        rv[f"{section}.{key}"] = value
return rv
```

## Showing Progress Bars

Sometimes, you have command line scripts that need to process a lot of data, but you want to quickly show the user some
progress about how long that will take. Click supports simple progress bar rendering for that through the
{func}`progressbar` function.

```{note} If you find that you have requirements beyond what Click's progress bar supports, try using [tqdm](https://tqdm.github.io/).
```

The basic usage is very simple: the idea is that you have an iterable that you want to operate on. For each item in the
iterable it might take some time to do processing. So say you have a loop like this:

```python
for user in all_the_users_to_process:
    modify_the_user(user)
```

To hook this up with an automatically updating progress bar, all you need to do is to change the code to this:

```python
import click

with click.progressbar(all_the_users_to_process) as bar:
    for user in bar:
        modify_the_user(user)
```

Click will then automatically print a progress bar to the terminal and calculate the remaining time for you. The
calculation of remaining time requires that the iterable has a length. If it does not have a length but you know the
length, you can explicitly provide it:

```python
with click.progressbar(all_the_users_to_process,
                       length=number_of_users) as bar:
    for user in bar:
        modify_the_user(user)
```

Note that {func}`progressbar` updates the bar *after* each iteration of the loop. So code like this will render
correctly:

```python
import time

with click.progressbar([1, 2, 3]) as bar:
    for x in bar:
        print(f"sleep({x})...")
        time.sleep(x)
```

Another useful feature is to associate a label with the progress bar which will be shown preceding the progress bar:

```python
with click.progressbar(all_the_users_to_process,
                       label='Modifying user accounts',
                       length=number_of_users) as bar:
    for user in bar:
        modify_the_user(user)
```

Sometimes, one may need to iterate over an external iterator, and advance the progress bar irregularly. To do so, you
need to specify the length (and no iterable), and use the update method on the context return value instead of iterating
directly over it:

```python
with click.progressbar(length=total_size,
                       label='Unzipping archive') as bar:
    for archive in zip_file:
        archive.extract()
        bar.update(archive.size)
```
