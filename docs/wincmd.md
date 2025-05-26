# Windows Console Notes

:::{versionadded} 6.0
:::

Click emulates output streams on Windows to support unicode to the Windows console through separate APIs and we perform
different decoding of parameters.

Here is a brief overview of how this works and what it means to you.

## Unicode Arguments

Click internally is generally based on the concept that any argument can come in as either byte string or unicode string
and conversion is performed to the type expected value as late as possible. This has some advantages as it allows us to
accept the data in the most appropriate form for the operating system and Python version.

This caused some problems on Windows where initially the wrong encoding was used and garbage ended up in your input
data. We not only fixed the encoding part, but we also now extract unicode parameters from `sys.argv`.

There is also another limitation with this: if `sys.argv` was modified prior to invoking a click handler, we have to
fall back to the regular byte input in which case not all unicode values are available but only a subset of the codepage
used for parameters.

## Unicode Output and Input

Unicode output and input on Windows is implemented through the concept of a dispatching text stream. What this means is
that when click first needs a text output (or input) stream on windows it goes through a few checks to figure out of a
windows console is connected or not. If no Windows console is present then the text output stream is returned as such
and the encoding for that stream is set to `utf-8` like on all platforms.

However if a console is connected the stream will instead be emulated and use the cmd.exe unicode APIs to output text
information. In this case the stream will also use `utf-16-le` as internal encoding. However there is some hackery going
on that the underlying raw IO buffer is still bypassing the unicode APIs and byte output through an indirection is still
possible.

- This unicode support is limited to `click.echo`, `click.prompt` as well as `click.get_text_stream`.
- Depending on if unicode values or byte strings are passed the control flow goes completely different places internally
  which can have some odd artifacts if data partially ends up being buffered. Click attempts to protect against that by
  manually always flushing but if you are mixing and matching different string types to `stdout` or `stderr` you will
  need to manually flush.
- The raw output stream is set to binary mode, which is a global operation on Windows, so `print` calls will be
  affected. Prefer `click.echo` over `print`.
- On Windows 7 and below, there is a limitation where at most 64k characters can be written in one call in binary mode.
  In this situation, `sys.stdout` and `sys.stderr` are replaced with wrappers that work around the limitation.

Another important thing to note is that the Windows console's default fonts do not support a lot of characters which
means that you are mostly limited to international letters but no emojis or special characters.
