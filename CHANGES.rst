Click Changelog
===============

This contains all major version changes between Click releases.

Version 7.0
-----------

(upcoming release with new features, release date to be decided)

- Updated test env matrix. (`#1027`_)
- Fixes a ZeroDivisionError in ProgressBar.make_step,
  when the arg passed to the first call of ProgressBar.update is 0. (`#1012`_)(`#447`_)
- Document that options can be required=True. (`#1022`_)(`#514`_)
- Fix path validation bug. (`#1020`_)(`#795`_)
- Document customizing option names. (`#1016`_)(`#725`_)
- Wrap click.Choice's missing message. (`#1000`_)(`#202`_)
- Don't add newlines by default for progressbars. (`#1013`_)
- Document how `auto_envar_prefix` works with command groups. (`#1011`_)
- Fix failing bash completion function test signature.
- Clarify how paramteres are named. (`#1009`_)(`#949`_)
- Document bytestripping behavior of CliRunner. (`#1010`_)(`#334`_)
- Fix Google App Engine ImportError. (`#995`_)
- Document that ANSI color info isn't parsedfrom bytearrays in Python 2. (`#334`_)
- Add note to documentation on how parameters are named.
- Fix formatting for short help. (`#1008`_)
- Extract bar formatting to its own method. (`#414`_)
- Move `fcntl` import. (`#965`_)
- Fixed issues where `fd` was undefined. (`#1007`_)
- Added deprecation flag to commands. (`#1005`_)
- Fix various Sphinx errors. (`#883`_)
- Add `case_sensitive=False` as an option to Choice types. (`#887`_)
- Add details about Python version support. (`#1004`_)
- Clarify documentation on command line options. (`#1003`_)(`#741`_)
- Add `case_sensitive=False` as an option to Choice. (`#569`_)
- Better handling of help text for dynamic default option values. (`#996`_)
- Allow short width to address cmd formatting. (`#1002`_)
- Add test case checking for custom param type. (`#1001`_)
- Make `Argument.make_metavar()` default to type metavar. (`#675`_)
- Show progressbar only if total execution time is visible. (`#487`_)
- Allow setting `prog_name` as extra in `CliRunner.invoke` (`#999`_)(`#616`_)
- Add support for Sphinx 1.7+ (`#991`_)
- Fix `get_winter_size()` so it correctly returns (0,0). (`#997`_)
- Update progress after iteration. (`#706`_)(`#651`_)
- Add `show_envvar` for showing environment variables in help. (`#710`_)
- Add support for bright colors. (`#809`_)
- Add documentation for `ignore_unkown_options`. (`#684`_)
- Allow CliRunner to separate stdout and stderr. (`#868`_)
- Implement streaming pager. (`#889`_)(`#409`_)
- Progress bar now uses stderr by default. (`#863`_)
- Do not set options twice. (`#962`_)
- Add Py2/ unicode / str compatability for doc tools. (`#993`_)(`#719`_)
- Add copy option attrs so that custom classes can be re-used. (`#994`_)(`#926`_)
- `param_hint` in errors now derived from param itself. (`#709`_)(`#704`_)(`#598`_)
- Add a test that ensures that when an Argument is formatted into a usage error,
  its metavar is used, not its name. (`#612`_)
- Fix variable precedence. (`#874`_)(`#873`_)
- Fix ResourceWarning that occurs during some tests. (`#878`_)
- Update README to match flask style and add `long_description` to setup.py. (`#990`_)
- Drop testing for 2.6 3.3 and 3.6.
- Make locale optional (`#880`_)
- Fix invalid escape sequences. (`#877`_)
- Added workaround for jupyter. (`#918`_)
- x and a filemodes now use stdout when file is '-'. (`#929`_)
- _AtomicFile now uses the realpath of the original filename. (`#920`_)
- Fix missing comma in `__all__` list (`#935`_)
- Raw strings added so correct escaping occurs. (`#807`_)
- Fix overzealous completion when
  required options are being completed. (`#806`_)(`#790`_)
- Add bool conversion for t and f. (`#842`_)
- Update doc to match arg name for path_type. (`#801`_)
- Add bright colors support for `click.style`
  and fix the reset option for parameters fg and bg. (`#703`_)
- Add test and documentation for Option naming: functionality. (`#799`_)
- Use deterministic option name; can't rely on list sort. (`#794`_)(`#793`_)
- Added support for bash completions containing spaces. (`#773`_)
- Added support for dynamic bash completion from a user-supplied callback.
  (`#755`_)
- Added support for bash completion of type=click.Choice for Options and
  Arguments. (`#535`_)
- The user is now presented with the available choices if prompt=True and
  type=click.Choice in a click.option. The choices are listed within
  parenthesis like 'Choose fruit (apple, orange): '.
- The exception objects now store unicode properly.
- Added the ability to hide commands and options from help.
- Added Float Range in Types.
- `secho`'s first argument can now be `None`, like in `echo`.
- Usage errors now hint at the `--help` option.
- ``launch`` now works properly under Cygwin. (`#650`_)
- `CliRunner.invoke` now may receive `args` as a string representing
  a Unix shell command. See (`#664`_).
- Fix bug that caused bashcompletion to give improper completions on
  chained commands. (`#774`_)
- Add support for bright colors.
- 't' and 'f' are now converted to True and False.
- Fix bug that caused bashcompletion to give improper completions on
  chained commands when a required option/argument was being completed.
  (`#790`_)
- Allow autocompletion function to determine whether or not to return
  completions that start with the incomplete argument.
- Add native ZSH autocompletion support. (`#323`_)(`#865`_)
- Add support for auto-completion documentation. See (`#866`_)(`#869`_)
- Subcommands that are named by the function now automatically have the
  underscore replaced with a dash.  So if you register a function named
  `my_command` it becomes `my-command` in the command line interface.
- Stdout is now automatically set to non blocking.
- Use realpath to convert atomic file internally into its full canonical
  path so that changing working directories does not harm it.
- Force stdout/stderr writable.  This works around issues with badly patched
  standard streams like those from jupyter.

.. _#1027: https://github.com/pallets/click/pull/1027
.. _#1012: https://github.com/pallets/click/pull/1012
.. _#447: https://github.com/pallets/click/issues/447
.. _#1022: https://github.com/pallets/click/pull/1022
.. _#869: https://github.com/pallets/click/pull/869
.. _#866: https://github.com/pallets/click/issues/866
.. _#514: https://github.com/pallets/click/issues/514
.. _#1020: https://github.com/pallets/click/pull/1020
.. _#795: https://github.com/pallets/click/issues/795
.. _#1016: https://github.com/pallets/click/pull/1016
.. _#725: https://github.com/pallets/click/issues/725
.. _#1000: https://github.com/pallets/click/pull/1000
.. _#202: https://github.com/pallets/click/issues/202
.. _#1013: https://github.com/pallets/click/pull/1013
.. _#1011: https://github.com/pallets/click/pull/1011
.. _#865: https://github.com/pallets/click/pull/865
.. _#323: https://github.com/pallets/click/issues/323
.. _#1009: https://github.com/pallets/click/pull/1009
.. _#949: https://github.com/pallets/click/issues/949
.. _#1010: https://github.com/pallets/click/pull/1010
.. _#334: https://github.com/pallets/click/issues/334
.. _#995: https://github.com/pallets/click/pull/995
.. _#1008: https://github.com/pallets/click/pull/1008
.. _#414: https://github.com/pallets/click/pull/414
.. _#965: https://github.com/pallets/click/pull/965
.. _#1005: https://github.com/pallets/click/pull/1005
.. _#883: https://github.com/pallets/click/pull/883
.. _#887: https://github.com/pallets/click/pull/887
.. _#1004: https://github.com/pallets/click/pull/1004
.. _#1003: https://github.com/pallets/click/pull/1003
.. _#741: https://github.com/pallets/click/issues/741
.. _#569: https://github.com/pallets/click/pull/569
.. _#1007: https://github.com/pallets/click/pull/1007
.. _#996: https://github.com/pallets/click/pull/996
.. _#1002: https://github.com/pallets/click/pull/1002
.. _#1001: https://github.com/pallets/click/pull/1001
.. _#675: https://github.com/pallets/click/pull/675
.. _#487: https://github.com/pallets/click/pull/487
.. _#999: https://github.com/pallets/click/pull/999
.. _#616: https://github.com/pallets/click/issues/616
.. _#991: https://github.com/pallets/click/pull/991
.. _#997: https://github.com/pallets/click/pull/997
.. _#706: https://github.com/pallets/click/pull/706
.. _#651: https://github.com/pallets/click/issues/651
.. _#710: https://github.com/pallets/click/pull/710
.. _#809: https://github.com/pallets/click/pull/809
.. _#868: https://github.com/pallets/click/pull/868
.. _#889: https://github.com/pallets/click/pull/889
.. _#409: https://github.com/pallets/click/issues/409
.. _#863: https://github.com/pallets/click/pull/863
.. _#962: https://github.com/pallets/click/pull/962
.. _#993: https://github.com/pallets/click/pull/993
.. _#994: https://github.com/pallets/click/pull/994
.. _#926: https://github.com/pallets/click/issues/926
.. _#709: https://github.com/pallets/click/pull/709
.. _#612: https://github.com/pallets/click/pull/612
.. _#704: https://github.com/pallets/click/issues/704
.. _#598: https://github.com/pallets/click/issues/598
.. _#719: https://github.com/pallets/click/issues/719
.. _#874: https://github.com/pallets/click/pull/874
.. _#873: https://github.com/pallets/click/issues/873
.. _#990: https://github.com/pallets/click/pull/990
.. _#684: https://github.com/pallets/click/pull/684
.. _#878: https://github.com/pallets/click/pull/878
.. _#880: https://github.com/pallets/click/issues/880
.. _#877: https://github.com/pallets/click/pull/877
.. _#918: https://github.com/pallets/click/pull/918
.. _#929: https://github.com/pallets/click/pull/929
.. _#920: https://github.com/pallets/click/pull/920
.. _#935: https://github.com/pallets/click/pull/935
.. _#807: https://github.com/pallets/click/pull/807
.. _#806: https://github.com/pallets/click/pull/806
.. _#842: https://github.com/pallets/click/pull/842
.. _#801: https://github.com/pallets/click/pull/801
.. _#703: https://github.com/pallets/click/issues/703
.. _#799: https://github.com/pallets/click/pull/799
.. _#794: https://github.com/pallets/click/pull/794
.. _#793: https://github.com/pallets/click/issues/793
.. _#773: https://github.com/pallets/click/pull/773
.. _#755: https://github.com/pallets/click/pull/755
.. _#535: https://github.com/pallets/click/pull/535
.. _#650: https://github.com/pallets/click/pull/650
.. _#664: https://github.com/pallets/click/pull/664
.. _#774: https://github.com/pallets/click/pull/774
.. _#790: https://github.com/pallets/click/pull/790


Version 6.8
-----------

(bugfix release; yet to be released)

- Disabled sys._getframes() on Python interpreters that don't support it. See
  #728.
- Fix bug in test runner when calling ``sys.exit`` with ``None``. See #739.
- Fix crash on Windows console, see #744.
- Fix bashcompletion on chained commands. See #754.
- Fix option naming routine to match documentation.  See #793
- Fixed the behavior of click error messages with regards to unicode on 2.x
  and 3.x respectively.  Message is now always unicode and the str and unicode
  special methods work as you expect on that platform.

Version 6.7
-----------

(bugfix release; released on January 6th 2017)

- Make `click.progressbar` work with `codecs.open` files. See #637.
- Fix bug in bash completion with nested subcommands. See #639.
- Fix test runner not saving caller env correctly. See #644.
- Fix handling of SIGPIPE. See #626
- Deal with broken Windows environments such as Google App Engine's. See #711.

Version 6.6
-----------

(bugfix release; released on April 4th 2016)

- Fix bug in `click.Path` where it would crash when passed a `-`. See #551.

Version 6.4
-----------

(bugfix release; released on March 24th 2016)

- Fix bug in bash completion where click would discard one or more trailing
  arguments. See #471.

Version 6.3
-----------

(bugfix release; released on February 22 2016)

- Fix argument checks for interpreter invoke with `-m` and `-c`
  on Windows.
- Fixed a bug that cased locale detection to error out on Python 3.

Version 6.2
-----------

(bugfix release, released on November 27th 2015)

- Correct fix for hidden progress bars.

Version 6.1
-----------

(bugfix release, released on November 27th 2015)

- Resolved an issue with invisible progress bars no longer rendering.
- Disable chain commands with subcommands as they were inherently broken.
- Fix `MissingParameter` not working without parameters passed.

Version 6.0
-----------

(codename "pow pow", released on November 24th 2015)

- Optimized the progressbar rendering to not render when it did not
  actually change.
- Explicitly disallow nargs=-1 with a set default.
- The context is now closed before it's popped from the stack.
- Added support for short aliases for the false flag on toggles.
- Click will now attempt to aid you with debugging locale errors
  better by listing with the help of the OS what locales are
  available.
- Click used to return byte strings on Python 2 in some unit-testing
  situations.  This has been fixed to correctly return unicode strings
  now.
- For Windows users on Python 2, Click will now handle Unicode more
  correctly handle Unicode coming in from the system.  This also has
  the disappointing side effect that filenames will now be always
  unicode by default in the `Path` type which means that this can
  introduce small bugs for code not aware of this.
- Added a `type` parameter to `Path` to force a specific string type
  on the value.
- For users running Python on Windows the `echo`) and `prompt` functions
  now work with full unicode functionality in the Python windows console
  by emulating an output stream.  This also applies to getting the
  virtual output and input streams via `click.get_text_stream(...)`.
- Unittests now always force a certain virtual terminal width.
- Added support for allowing dashes to indicate standard streams to the
  `Path` type.
- Multi commands in chain mode no longer propagate arguments left over
  from parsing to the callbacks.  It's also now disallowed through an
  exception when optional arguments are attached to multi commands if chain
  mode is enabled.
- Relaxed restriction that disallowed chained commands to have other
  chained commands as child commands.
- Arguments with positive nargs can now have defaults implemented.
  Previously this configuration would often result in slightly unexpected
  values be returned.

Version 5.1
-----------

(bugfix release, released on 17th August 2015)

- Fix a bug in `pass_obj` that would accidentally pass the context too.

Version 5.0
-----------

(codename "tok tok", released on 16th August 2015)

- Removed various deprecated functionality.
- Atomic files now only accept the `w` mode.
- Change the usage part of help output for very long commands to wrap
  their arguments onto the next line, indented by 4 spaces.
- Fix a bug where return code and error messages were incorrect when
  using ``CliRunner``.
- added `get_current_context`.
- added a `meta` dictionary to the context which is shared across the
  linked list of contexts to allow click utilities to place state there.
- introduced `Context.scope`.
- The `echo` function is now threadsafe: It calls the `write` method of the
  underlying object only once.
- `prompt(hide_input=True)` now prints a newline on `^C`.
- Click will now warn if users are using ``unicode_literals``.
- Click will now ignore the ``PAGER`` environment variable if it is empty or
  contains only whitespace.
- The `click-contrib` GitHub organization was created.

Version 4.1
-----------

(bugfix release, released on July 14th 2015)

- Fix a bug where error messages would include a trailing `None` string.
- Fix a bug where Click would crash on docstrings with trailing newlines.
- Support streams with encoding set to `None` on Python 3 by barfing with
  a better error.
- Handle ^C in less-pager properly.
- Handle return value of `None` from `sys.getfilesystemencoding`
- Fix crash when writing to unicode files with `click.echo`.
- Fix type inference with multiple options.

Version 4.0
-----------

(codename "zoom zoom", released on March 31st 2015)

- Added `color` parameters to lots of interfaces that directly or indirectly
  call into echoing.  This previously was always autodetection (with the
  exception of the `echo_via_pager` function).  Now you can forcefully
  enable or disable it, overriding the auto detection of Click.
- Added an `UNPROCESSED` type which does not perform any type changes which
  simplifies text handling on 2.x / 3.x in some special advanced usecases.
- Added `NoSuchOption` and `BadOptionUsage` exceptions for more generic
  handling of errors.
- Added support for handling of unprocessed options which can be useful in
  situations where arguments are forwarded to underlying tools.
- Added `max_content_width` parameter to the context which can be used to
  change the maximum width of help output.  By default Click will not format
  content for more than 80 characters width.
- Added support for writing prompts to stderr.
- Fix a bug when showing the default for multiple arguments.
- Added support for custom subclasses to `option` and `argument`.
- Fix bug in ``clear()`` on Windows when colorama is installed.
- Reject ``nargs=-1`` for options properly.  Options cannot be variadic.
- Fixed an issue with bash completion not working properly for commands with
  non ASCII characters or dashes.
- Added a way to manually update the progressbar.
- Changed the formatting of missing arguments.  Previously the internal
  argument name was shown in error messages, now the metavar is shown if
  passed.  In case an automated metavar is selected, it's stripped of
  extra formatting first.

Version 3.3
-----------

(bugfix release, released on September 8th 2014)

- Fixed an issue with error reporting on Python 3 for invalid forwarding
  of commands.

Version 3.2
-----------

(bugfix release, released on August 22nd 2014)

- Added missing `err` parameter forwarding to the `secho` function.
- Fixed default parameters not being handled properly by the context
  invoke method.  This is a backwards incompatible change if the function
  was used improperly.  See :ref:`upgrade-to-3.2` for more information.
- Removed the `invoked_subcommands` attribute largely.  It is not possible
  to provide it to work error free due to how the parsing works so this
  API has been deprecated.  See :ref:`upgrade-to-3.2` for more information.
- Restored the functionality of `invoked_subcommand` which was broken as
  a regression in 3.1.

Version 3.1
-----------

(bugfix release, released on August 13th 2014)

- Fixed a regression that caused contexts of subcommands to be
  created before the parent command was invoked which was a
  regression from earlier Click versions.

Version 3.0
-----------

(codename "clonk clonk", released on August 12th 2014)

- formatter now no longer attempts to accomodate for terminals
  smaller than 50 characters.  If that happens it just assumes
  a minimal width.
- added a way to not swallow exceptions in the test system.
- added better support for colors with pagers and ways to
  override the autodetection.
- the CLI runner's result object now has a traceback attached.
- improved automatic short help detection to work better with
  dots that do not terminate sentences.
- when definining options without actual valid option strings
  now, Click will give an error message instead of silently
  passing.  This should catch situations where users wanted to
  created arguments instead of options.
- Restructured Click internally to support vendoring.
- Added support for multi command chaining.
- Added support for defaults on options with `multiple` and
  options and arguments with `nargs != 1`.
- label passed to `progressbar` is no longer rendered with
  whitespace stripped.
- added a way to disable the standalone mode of the `main`
  method on a Click command to be able to handle errors better.
- added support for returning values from command callbacks.
- added simplifications for printing to stderr from `echo`.
- added result callbacks for groups.
- entering a context multiple times defers the cleanup until
  the last exit occurs.
- added `open_file`.

Version 2.6
-----------

(bugfix release, released on August 11th 2014)

- Fixed an issue where the wrapped streams on Python 3 would be reporting
  incorrect values for seekable.

Version 2.5
-----------

(bugfix release, released on July 28th 2014)

- Fixed a bug with text wrapping on Python 3.

Version 2.4
-----------

(bugfix release, released on July 4th 2014)

- Corrected a bug in the change of the help option in 2.3.

Version 2.3
-----------

(bugfix release, released on July 3rd 2014)

- Fixed an incorrectly formatted help record for count options.'
- Add support for ansi code stripping on Windows if colorama
  is not available.
- restored the Click 1.0 handling of the help parameter for certain
  edge cases.

Version 2.2
-----------

(bugfix release, released on June 26th 2014)

- fixed tty detection on PyPy.
- fixed an issue that progress bars were not rendered when the
  context manager was entered.

Version 2.1
-----------

(bugfix release, released on June 14th 2014)

- fixed the :func:`launch` function on windows.
- improved the colorama support on windows to try hard to not
  screw up the console if the application is interrupted.
- fixed windows terminals incorrectly being reported to be 80
  characters wide instead of 79
- use colorama win32 bindings if available to get the correct
  dimensions of a windows terminal.
- fixed an issue with custom function types on Python 3.
- fixed an issue with unknown options being incorrectly reported
  in error messages.

Version 2.0
-----------

(codename "tap tap tap", released on June 6th 2014)

- added support for opening stdin/stdout on Windows in
  binary mode correctly.
- added support for atomic writes to files by going through
  a temporary file.
- introduced :exc:`BadParameter` which can be used to easily perform
  custom validation with the same error messages as in the type system.
- added :func:`progressbar`; a function to show progress bars.
- added :func:`get_app_dir`; a function to calculate the home folder
  for configs.
- Added transparent handling for ANSI codes into the :func:`echo`
  function through `colorama`.
- Added :func:`clear` function.
- Breaking change: parameter callbacks now get the parameter object
  passed as second argument.  There is legacy support for old callbacks
  which will warn but still execute the script.
- Added :func:`style`, :func:`unstyle` and :func:`secho` for ANSI
  styles.
- Added an :func:`edit` function that invokes the default editor.
- Added an :func:`launch` function that launches browsers and applications.
- nargs of -1 for arguments can now be forced to be a single item through
  the required flag.  It defaults to not required.
- setting a default for arguments now implicitly makes it non required.
- changed "yN" / "Yn" to "y/N" and "Y/n" in confirmation prompts.
- added basic support for bash completion.
- added :func:`getchar` to fetch a single character from the terminal.
- errors now go to stderr as intended.
- fixed various issues with more exotic parameter formats like DOS/Windows
  style arguments.
- added :func:`pause` which works similar to the Windows ``pause`` cmd
  built-in but becomes an automatic noop if the application is not run
  through a terminal.
- added a bit of extra information about missing choice parameters.
- changed how the help function is implemented to allow global overriding
  of the help option.
- added support for token normalization to implement case insensitive handling.
- added support for providing defaults for context settings.

Version 1.1
-----------

(bugfix release, released on May 23rd 2014)

- fixed a bug that caused text files in Python 2 to not accept
  native strings.

Version 1.0
-----------

(no codename, released on May 21st 2014)

- Initial release.
