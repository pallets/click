# Unicode Support

Click has to take extra care to support Unicode text in different environments.

- The command line in Unix is traditionally bytes, not Unicode. While there are encoding hints, there are some
  situations where this can break. The most common one is SSH connections to machines with different locales.

  Misconfigured environments can cause a wide range of Unicode problems due to the lack of support for roundtripping
  surrogate escapes. This will not be fixed in Click itself!

- Standard input and output is opened in text mode by default. Click has to reopen the stream in binary mode in certain
  situations. Because there is no standard way to do this, it might not always work. Primarily this can become a problem
  when testing command-line applications.

  This is not supported:

  ```python
  sys.stdin = io.StringIO('Input here')
  sys.stdout = io.StringIO()
  ```

  Instead you need to do this:

  ```python
  input = 'Input here'
  in_stream = io.BytesIO(input.encode('utf-8'))
  sys.stdin = io.TextIOWrapper(in_stream, encoding='utf-8')
  out_stream = io.BytesIO()
  sys.stdout = io.TextIOWrapper(out_stream, encoding='utf-8')
  ```

  Remember in that case, you need to use `out_stream.getvalue()` and not `sys.stdout.getvalue()` if you want to access
  the buffer contents as the wrapper will not forward that method.

- `sys.stdin`, `sys.stdout` and `sys.stderr` are by default text-based. When Click needs a binary stream, it attempts to
  discover the underlying binary stream.

- `sys.argv` is always text. This means that the native type for input values to the types in Click is Unicode, not
  bytes.

  This causes problems if the terminal is incorrectly set and Python does not figure out the encoding. In that case, the
  Unicode string will contain error bytes encoded as surrogate escapes.

- When dealing with files, Click will always use the Unicode file system API by using the operating system's reported or
  guessed filesystem encoding. Surrogates are supported for filenames, so it should be possible to open files through
  the {func}`click.File` type even if the environment is misconfigured.

## Surrogate Handling

Click does all the Unicode handling in the standard library and is subject to its behavior. Unicode requires extra care.
The reason for this is that the encoding detection is done in the interpreter, and on Linux and certain other operating
systems, its encoding handling is problematic.

The biggest source of frustration is that Click scripts invoked by init systems, deployment tools, or cron jobs will
refuse to work unless a Unicode locale is exported.

If Click encounters such an environment it will prevent further execution to force you to set a locale. This is done
because Click cannot know about the state of the system once it's invoked and restore the values before Python's Unicode
handling kicked in.

If you see something like this error:

```console
Traceback (most recent call last):
  ...
RuntimeError: Click will abort further execution because Python was
  configured to use ASCII as encoding for the environment. Consult
  https://click.palletsprojects.com/unicode-support/ for mitigation
  steps.
```

You are dealing with an environment where Python thinks you are restricted to ASCII data. The solution to these problems
is different depending on which locale your computer is running in.

For instance, if you have a German Linux machine, you can fix the problem by exporting the locale to `de_DE.utf-8`:

```console
export LC_ALL=de_DE.utf-8
export LANG=de_DE.utf-8
```

If you are on a US machine, `en_US.utf-8` is the encoding of choice. On some newer Linux systems, you could also try
`C.UTF-8` as the locale:

```console
export LC_ALL=C.UTF-8
export LANG=C.UTF-8
```

On some systems it was reported that `UTF-8` has to be written as `UTF8` and vice versa. To see which locales are
supported you can invoke `locale -a`.

You need to export the values before you invoke your Python script.

In Python 3.7 and later you will no longer get a `RuntimeError` in many cases thanks to {pep}`538` and {pep}`540`, which
changed the default assumption in unconfigured environments. This doesn't change the general issue that your locale may
be misconfigured.
