.. currentmodule:: click

Version 8.0
-----------

Unreleased

-   Drop support for Python 2 and 3.5.
-   Colorama is always installed on Windows in order to provide style
    and color support. :pr:`1784`
-   Adds a repr to Command, showing the command name for friendlier
    debugging. :issue:`1267`, :pr:`1295`
-   Add support for distinguishing the source of a command line
    parameter. :issue:`1264`, :pr:`1329`
-   Add an optional parameter to ``ProgressBar.update`` to set the
    ``current_item``. :issue:`1226`, :pr:`1332`
-   ``version_option`` uses ``importlib.metadata`` (or the
    ``importlib_metadata`` backport) instead of ``pkg_resources``.
    :issue:`1582`
-   If validation fails for a prompt with ``hide_input=True``, the value
    is not shown in the error message. :issue:`1460`
-   An ``IntRange`` or ``FloatRange`` option shows the accepted range in
    its help text. :issue:`1525`, :pr:`1303`
-   ``IntRange`` and ``FloatRange`` bounds can be open (``<``) instead
    of closed (``<=``) by setting ``min_open`` and ``max_open``. Error
    messages have changed to reflect this. :issue:`1100`
-   An option defined with duplicate flag names (``"--foo/--foo"``)
    raises a ``ValueError``. :issue:`1465`
-   ``echo()`` will not fail when using pytest's ``capsys`` fixture on
    Windows. :issue:`1590`
-   Resolving commands returns the canonical command name instead of the
    matched name. This makes behavior such as help text and
    ``Context.invoked_subcommand`` consistent when using patterns like
    ``AliasedGroup``. :issue:`1422`
-   The ``BOOL`` type accepts the values "on" and "off". :issue:`1629`
-   A ``Group`` with ``invoke_without_command=True`` will always invoke
    its result callback. :issue:`1178`
-   ``nargs == -1`` and ``nargs > 1`` is parsed and validated for
    values from environment variables and defaults. :issue:`729`
-   Detect the program name when executing a module or package with
    ``python -m name``. :issue:`1603`
-   Include required parent arguments in help synopsis of subcommands.
    :issue:`1475`
-   Help for boolean flags with ``show_default=True`` shows the flag
    name instead of ``True`` or ``False``. :issue:`1538`
-   Non-string objects passed to ``style()`` and ``secho()`` will be
    converted to string. :pr:`1146`
-   ``edit(require_save=True)`` will detect saves for editors that exit
    very fast on filesystems with 1 second resolution. :pr:`1050`
-   New class attributes make it easier to use custom core objects
    throughout an entire application. :pr:`938`

    -   ``Command.context_class`` controls the context created when
        running the command.
    -   ``Context.invoke`` creates new contexts of the same type, so a
        custom type will persist to invoked subcommands.
    -   ``Context.formatter_class`` controls the formatter used to
        generate help and usage.
    -   ``Group.command_class`` changes the default type for
        subcommands with ``@group.command()``.
    -   ``Group.group_class`` changes the default type for subgroups
        with ``@group.group()``. Setting it to ``type`` will create
        subgroups of the same type as the group itself.
    -   Core objects use ``super()`` consistently for better support of
        subclassing.

-   Use ``Context.with_resource()`` to manage resources that would
    normally be used in a ``with`` statement, allowing them to be used
    across subcommands and callbacks, then cleaned up when the context
    ends. :pr:`1191`
-   The result object returned by the test runner's ``invoke()`` method
    has a ``return_value`` attribute with the value returned by the
    invoked command. :pr:`1312`
-   Required arguments with the ``Choice`` type show the choices in
    curly braces to indicate that one is required (``{a|b|c}``).
    :issue:`1272`
-   If only a name is passed to ``option()``, Click suggests renaming it
    to ``--name``. :pr:`1355`
-   A context's ``show_default`` parameter defaults to the value from
    the parent context. :issue:`1565`
-   ``click.style()`` can output 256 and RGB color codes. Most modern
    terminals support these codes. :pr:`1429`
-   When using ``CliRunner.invoke()``, the replaced ``stdin`` file has
    ``name`` and ``mode`` attributes. This lets ``File`` options with
    the ``-`` value match non-testing behavior. :issue:`1064`
-   When creating a ``Group``, allow passing a list of commands instead
    of a dict. :issue:`1339`
-   When a long option name isn't valid, use ``difflib`` to make better
    suggestions for possible corrections. :issue:`1446`
-   Core objects have a ``to_info_dict()`` method. This gathers
    information about the object's structure that could be useful for a
    tool generating user-facing documentation. To get the structure of
    an entire CLI, use ``Context(cli).to_info_dict()``. :issue:`461`
-   Redesign the shell completion system. :issue:`1484`, :pr:`1622`

    -   Support Bash >= 4.4, Zsh, and Fish, with the ability for
        extensions to add support for other shells.
    -   Allow commands, groups, parameters, and types to override their
        completions suggestions.
    -   Groups complete the names commands were registered with, which
        can differ from the name they were created with.
    -   The ``autocompletion`` parameter for options and arguments is
        renamed to ``shell_complete``. The function must take
        ``ctx, param, incomplete``, must do matching rather than return
        all values, and must return a list of strings or a list of
        ``ShellComplete``. The old name and behavior is deprecated and
        will be removed in 8.1.
    -   The env var values used to start completion have changed order.
        The shell now comes first, such as ``{shell}_source`` rather
        than ``source_{shell}``, and is always required.

-   Completion correctly parses command line strings with incomplete
    quoting or escape sequences. :issue:`1708`
-   Extra context settings (``obj=...``, etc.) are passed on to the
    completion system. :issue:`942`
-   Include ``--help`` option in completion. :pr:`1504`
-   ``ParameterSource`` is an ``enum.Enum`` subclass. :issue:`1530`
-   Boolean and UUID types strip surrounding space before converting.
    :issue:`1605`
-   Adjusted error message from parameter type validation to be more
    consistent. Quotes are used to distinguish the invalid value.
    :issue:`1605`
-   The default value for a parameter with ``nargs`` > 1 and
    ``multiple=True`` must be a list of tuples. :issue:`1649`
-   When getting the value for a parameter, the default is tried in the
    same section as other sources to ensure consistent processing.
    :issue:`1649`
-   All parameter types accept a value that is already the correct type.
    :issue:`1649`
-   For shell completion, an argument is considered incomplete if its
    value did not come from the command line args. :issue:`1649`
-   Added ``ParameterSource.PROMPT`` to track parameter values that were
    prompted for. :issue:`1649`
-   Options with ``nargs`` > 1 no longer raise an error if a default is
    not given. Parameters with ``nargs`` > 1 default to ``None``, and
    parameters with ``multiple=True`` or ``nargs=-1`` default to an
    empty tuple. :issue:`472`
-   Handle empty env vars as though the option were not passed. This
    extends the change introduced in 7.1 to be consistent in more cases.
    :issue:`1285`
-   ``Parameter.get_default()`` checks ``Context.default_map`` to
    handle overrides consistently in help text, ``invoke()``, and
    prompts. :issue:`1548`
-   Add ``prompt_required`` param to ``Option``. When set to ``False``,
    the user will only be prompted for an input if no value was passed.
    :issue:`736`
-   Providing the value to an option can be made optional through
    ``is_flag=False``, and the value can instead be prompted for or
    passed in as a default value.
    :issue:`549, 736, 764, 921, 1015, 1618`
-   Fix formatting when ``Command.options_metavar`` is empty. :pr:`1551`
-   The default value passed to ``prompt`` will be cast to the correct
    type like an input value would be. :pr:`1517`
-   Automatically generated short help messages will stop at the first
    ending of a phrase or double linebreak. :issue:`1082`
-   Skip progress bar render steps for efficiency with very fast
    iterators by setting ``update_min_steps``. :issue:`676`
-   Respect ``case_sensitive=False`` when doing shell completion for
    ``Choice`` :issue:`1692`
-   Use ``mkstemp()`` instead of ``mktemp()`` in pager implementation.
    :issue:`1752`
-   If ``Option.show_default`` is a string, it is displayed even if
    ``default`` is ``None``. :issue:`1732`
-   ``click.get_terminal_size()`` is deprecated and will be removed in
    8.1. Use :func:`shutil.get_terminal_size` instead. :issue:`1736`
-   Control the location of the temporary directory created by
    ``CLIRunner.isolated_filesystem`` by passing ``temp_dir``. A custom
    directory will not be removed automatically. :issue:`395`
-   ``click.confirm()`` will prompt until input is given if called with
    ``default=None``. :issue:`1381`
-   Option prompts validate the value with the option's callback in
    addition to its type. :issue:`457`
-   ``confirmation_prompt`` can be set to a custom string. :issue:`723`
-   Allow styled output in Jupyter on Windows. :issue:`1271`
-   ``style()`` supports the ``strikethrough`` style. :issue:`805`
-   Multiline marker is removed from short help text. :issue:`1597`
-   Restore progress bar behavior of echoing only the label if the file
    is not a TTY. :issue:`1138`
-   Progress bar output is shown even if execution time is less than 0.5
    seconds. :issue:`1648`
-   Progress bar ``item_show_func`` shows the current item, not the
    previous item. :issue:`1353`
-   The ``Path`` param type can be passed ``path_type=pathlib.Path`` to
    return a path object instead of a string. :issue:`405`
-   ``TypeError`` is raised when parameter with ``multiple=True`` or
    ``nargs > 1`` has non-iterable default. :issue:`1749`


Version 7.1.2
-------------

Released 2020-04-27

-   Revert applying shell quoting to commands for ``echo_with_pager``
    and ``edit``. This was intended to allows spaces in commands, but
    caused issues if the string was actually a command and arguments, or
    on Windows. Instead, the string must be quoted manually as it should
    appear on the command line. :issue:`1514`


Version 7.1.1
-------------

Released 2020-03-09

-   Fix ``ClickException`` output going to stdout instead of stderr.
    :issue:`1495`


Version 7.1
-----------

Released 2020-03-09

-   Fix PyPI package name, "click" is lowercase again.
-   Fix link in ``unicode_literals`` error message. :pr:`1151`
-   Add support for colored output on UNIX Jupyter notebooks.
    :issue:`1185`
-   Operations that strip ANSI controls will strip the cursor hide/show
    sequences. :issue:`1216`
-   Remove unused compat shim for ``bytes``. :pr:`1195`
-   Expand testing around termui, especially getchar on Windows.
    :issue:`1116`
-   Fix output on Windows Python 2.7 built with MSVC 14. :pr:`1342`
-   Fix ``OSError`` when running in MSYS2. :issue:`1338`
-   Fix ``OSError`` when redirecting to ``NUL`` stream on Windows.
    :issue:`1065`
-   Fix memory leak when parsing Unicode arguments on Windows.
    :issue:`1136`
-   Fix error in new AppEngine environments. :issue:`1462`
-   Always return one of the passed choices for ``click.Choice``
    :issue:`1277`, :pr:`1318`
-   Add ``no_args_is_help`` option to ``click.Command``, defaults to
    False :pr:`1167`
-   Add ``show_default`` parameter to ``Context`` to enable showing
    defaults globally. :issue:`1018`
-   Handle ``env MYPATH=''`` as though the option were not passed.
    :issue:`1196`
-   It is once again possible to call ``next(bar)`` on an active
    progress bar instance. :issue:`1125`
-   ``open_file`` with ``atomic=True`` retains permissions of existing
    files and respects the current umask for new files. :issue:`1376`
-   When using the test ``CliRunner`` with ``mix_stderr=False``, if
    ``result.stderr`` is empty it will not raise a ``ValueError``.
    :issue:`1193`
-   Remove the unused ``mix_stderr`` parameter from
    ``CliRunner.invoke``. :issue:`1435`
-   Fix ``TypeError`` raised when using bool flags and specifying
    ``type=bool``. :issue:`1287`
-   Newlines in option help text are replaced with spaces before
    re-wrapping to avoid uneven line breaks. :issue:`834`
-   ``MissingParameter`` exceptions are printable in the Python
    interpreter. :issue:`1139`
-   Fix how default values for file-type options are shown during
    prompts. :issue:`914`
-   Fix environment variable automatic generation for commands
    containing ``-``. :issue:`1253`
-   Option help text replaces newlines with spaces when rewrapping, but
    preserves paragraph breaks, fixing multiline formatting.
    :issue:`834, 1066, 1397`
-   Option help text that is wrapped adds an extra newline at the end to
    distinguish it from the next option. :issue:`1075`
-   Consider ``sensible-editor`` when determining the editor to use for
    ``click.edit()``. :pr:`1469`
-   Arguments to system calls such as the executable path passed to
    ``click.edit`` can contains spaces. :pr:`1470`
-   Add ZSH completion autoloading and error handling. :issue:`1348`
-   Add a repr to ``Command``, ``Group``, ``Option``, and ``Argument``,
    showing the name for friendlier debugging. :issue:`1267`
-   Completion doesn't consider option names if a value starts with
    ``-`` after the ``--`` separator. :issue:`1247`
-   ZSH completion escapes special characters in values. :pr:`1418`
-   Add completion support for Fish shell. :pr:`1423`
-   Decoding bytes option values falls back to UTF-8 in more cases.
    :pr:`1468`
-   Make the warning about old 2-arg parameter callbacks a deprecation
    warning, to be removed in 8.0. This has been a warning since Click
    2.0. :pr:`1492`
-   Adjust error messages to standardize the types of quotes used so
    they match error messages from Python.


Version 7.0
-----------

Released 2018-09-25

-   Drop support for Python 2.6 and 3.3. :pr:`967, 976`
-   Wrap ``click.Choice``'s missing message. :issue:`202`, :pr:`1000`
-   Add native ZSH autocompletion support. :issue:`323`, :pr:`865`
-   Document that ANSI color info isn't parsed from bytearrays in Python
    2. :issue:`334`
-   Document byte-stripping behavior of ``CliRunner``. :issue:`334`,
    :pr:`1010`
-   Usage errors now hint at the ``--help`` option. :issue:`393`,
    :pr:`557`
-   Implement streaming pager. :issue:`409`, :pr:`889`
-   Extract bar formatting to its own method. :pr:`414`
-   Add ``DateTime`` type for converting input in given date time
    formats. :pr:`423`
-   ``secho``'s first argument can now be ``None``, like in ``echo``.
    :pr:`424`
-   Fixes a ``ZeroDivisionError`` in ``ProgressBar.make_step``, when the
    arg passed to the first call of ``ProgressBar.update`` is 0.
    :issue:`447`, :pr:`1012`
-   Show progressbar only if total execution time is visible. :pr:`487`
-   Added the ability to hide commands and options from help. :pr:`500`
-   Document that options can be ``required=True``. :issue:`514`,
    :pr:`1022`
-   Non-standalone calls to ``Context.exit`` return the exit code,
    rather than calling ``sys.exit``. :issue:`667`, :pr:`533, 1098`
-   ``click.getchar()`` returns Unicode in Python 3 on Windows,
    consistent with other platforms. :issue:`537, 821, 822, 1088`,
    :pr:`1108`
-   Added ``FloatRange`` type. :pr:`538, 553`
-   Added support for bash completion of ``type=click.Choice`` for
    ``Options`` and ``Arguments``. :issue:`535`, :pr:`681`
-   Only allow one positional arg for ``Argument`` parameter
    declaration. :issue:`568, 574`, :pr:`1014`
-   Add ``case_sensitive=False`` as an option to Choice. :issue:`569`
-   ``click.getchar()`` correctly raises ``KeyboardInterrupt`` on "^C"
    and ``EOFError`` on "^D" on Linux. :issue:`583`, :pr:`1115`
-   Fix encoding issue with ``click.getchar(echo=True)`` on Linux.
    :pr:`1115`
-   ``param_hint`` in errors now derived from param itself.
    :issue:`598, 704`, :pr:`709`
-   Add a test that ensures that when an argument is formatted into a
    usage error, its metavar is used, not its name. :pr:`612`
-   Allow setting ``prog_name`` as extra in ``CliRunner.invoke``.
    :issue:`616`, :pr:`999`
-   Help text taken from docstrings truncates at the ``\f`` form feed
    character, useful for hiding Sphinx-style parameter documentation.
    :pr:`629, 1091`
-   ``launch`` now works properly under Cygwin. :pr:`650`
-   Update progress after iteration. :issue:`651`, :pr:`706`
-   ``CliRunner.invoke`` now may receive ``args`` as a string
    representing a Unix shell command. :pr:`664`
-   Make ``Argument.make_metavar()`` default to type metavar. :pr:`675`
-   Add documentation for ``ignore_unknown_options``. :pr:`684`
-   Add bright colors support for ``click.style`` and fix the reset
    option for parameters ``fg`` and ``bg``. :issue:`703`, :pr:`809`
-   Add ``show_envvar`` for showing environment variables in help.
    :pr:`710`
-   Avoid ``BrokenPipeError`` during interpreter shutdown when stdout or
    stderr is a closed pipe. :issue:`712`, :pr:`1106`
-   Document customizing option names. :issue:`725`, :pr:`1016`
-   Disable ``sys._getframes()`` on Python interpreters that don't
    support it. :pr:`728`
-   Fix bug in test runner when calling ``sys.exit`` with ``None``.
    :pr:`739`
-   Clarify documentation on command line options. :issue:`741`,
    :pr:`1003`
-   Fix crash on Windows console. :issue:`744`
-   Fix bug that caused bash completion to give improper completions on
    chained commands. :issue:`754`, :pr:`774`
-   Added support for dynamic bash completion from a user-supplied
    callback. :pr:`755`
-   Added support for bash completions containing spaces. :pr:`773`
-   Allow autocompletion function to determine whether or not to return
    completions that start with the incomplete argument. :issue:`790`,
    :pr:`806`
-   Fix option naming routine to match documentation and be
    deterministic. :issue:`793`, :pr:`794`
-   Fix path validation bug. :issue:`795`, :pr:`1020`
-   Add test and documentation for ``Option`` naming: functionality.
    :pr:`799`
-   Update doc to match arg name for ``path_type``. :pr:`801`
-   Raw strings added so correct escaping occurs. :pr:`807`
-   Fix 16k character limit of ``click.echo`` on Windows. :issue:`816`,
    :pr:`819`
-   Overcome 64k character limit when writing to binary stream on
    Windows 7. :issue:`825`, :pr:`830`
-   Add bool conversion for "t" and "f". :pr:`842`
-   ``NoSuchOption`` errors take ``ctx`` so that ``--help`` hint gets
    printed in error output. :pr:`860`
-   Fixed the behavior of Click error messages with regards to Unicode
    on 2.x and 3.x. Message is now always Unicode and the str and
    Unicode special methods work as you expect on that platform.
    :issue:`862`
-   Progress bar now uses stderr by default. :pr:`863`
-   Add support for auto-completion documentation. :issue:`866`,
    :pr:`869`
-   Allow ``CliRunner`` to separate stdout and stderr. :pr:`868`
-   Fix variable precedence. :issue:`873`, :pr:`874`
-   Fix invalid escape sequences. :pr:`877`
-   Fix ``ResourceWarning`` that occurs during some tests. :pr:`878`
-   When detecting a misconfigured locale, don't fail if the ``locale``
    command fails. :pr:`880`
-   Add ``case_sensitive=False`` as an option to ``Choice`` types.
    :pr:`887`
-   Force stdout/stderr writable. This works around issues with badly
    patched standard streams like those from Jupyter. :pr:`918`
-   Fix completion of subcommand options after last argument
    :issue:`919`, :pr:`930`
-   ``_AtomicFile`` now uses the ``realpath`` of the original filename
    so that changing the working directory does not affect it. :pr:`920`
-   Fix incorrect completions when defaults are present :issue:`925`,
    :pr:`930`
-   Add copy option attrs so that custom classes can be re-used.
    :issue:`926`, :pr:`994`
-   "x" and "a" file modes now use stdout when file is ``"-"``.
    :pr:`929`
-   Fix missing comma in ``__all__`` list. :pr:`935`
-   Clarify how parameters are named. :issue:`949`, :pr:`1009`
-   Stdout is now automatically set to non blocking. :pr:`954`
-   Do not set options twice. :pr:`962`
-   Move ``fcntl`` import. :pr:`965`
-   Fix Google App Engine ``ImportError``. :pr:`995`
-   Better handling of help text for dynamic default option values.
    :pr:`996`
-   Fix ``get_winter_size()`` so it correctly returns ``(0,0)``.
    :pr:`997`
-   Add test case checking for custom param type. :pr:`1001`
-   Allow short width to address cmd formatting. :pr:`1002`
-   Add details about Python version support. :pr:`1004`
-   Added deprecation flag to commands. :pr:`1005`
-   Fixed issues where ``fd`` was undefined. :pr:`1007`
-   Fix formatting for short help. :pr:`1008`
-   Document how ``auto_envvar_prefix`` works with command groups.
    :pr:`1011`
-   Don't add newlines by default for progress bars. :pr:`1013`
-   Use Python sorting order for ZSH completions. :issue:`1047`,
    :pr:`1059`
-   Document that parameter names are converted to lowercase by default.
    :pr:`1055`
-   Subcommands that are named by the function now automatically have
    the underscore replaced with a dash. If you register a function
    named ``my_command`` it becomes ``my-command`` in the command line
    interface.
-   Hide hidden commands and options from completion. :issue:`1058`,
    :pr:`1061`
-   Fix absolute import blocking Click from being vendored into a
    project on Windows. :issue:`1068`, :pr:`1069`
-   Fix issue where a lowercase ``auto_envvar_prefix`` would not be
    converted to uppercase. :pr:`1105`


Version 6.7
-----------

Released 2017-01-06

-   Make ``click.progressbar`` work with ``codecs.open`` files.
    :pr:`637`
-   Fix bug in bash completion with nested subcommands. :pr:`639`
-   Fix test runner not saving caller env correctly. :pr:`644`
-   Fix handling of SIGPIPE. :pr:`62`
-   Deal with broken Windows environments such as Google App Engine's.
    :issue:`711`


Version 6.6
-----------

Released 2016-04-04

-   Fix bug in ``click.Path`` where it would crash when passed a ``-``.
    :issue:`551`


Version 6.4
-----------

Released 2016-03-24

-   Fix bug in bash completion where click would discard one or more
    trailing arguments. :issue:`471`


Version 6.3
-----------

Released 2016-02-22

-   Fix argument checks for interpreter invoke with ``-m`` and ``-c`` on
    Windows.
-   Fixed a bug that cased locale detection to error out on Python 3.


Version 6.2
-----------

Released 2015-11-27

-   Correct fix for hidden progress bars.


Version 6.1
-----------

Released 2015-11-27

-   Resolved an issue with invisible progress bars no longer rendering.
-   Disable chain commands with subcommands as they were inherently
    broken.
-   Fix ``MissingParameter`` not working without parameters passed.


Version 6.0
-----------

Released 2015-11-24, codename "pow pow"

-   Optimized the progressbar rendering to not render when it did not
    actually change.
-   Explicitly disallow ``nargs=-1`` with a set default.
-   The context is now closed before it's popped from the stack.
-   Added support for short aliases for the false flag on toggles.
-   Click will now attempt to aid you with debugging locale errors
    better by listing with the help of the OS what locales are
    available.
-   Click used to return byte strings on Python 2 in some unit-testing
    situations. This has been fixed to correctly return unicode strings
    now.
-   For Windows users on Python 2, Click will now handle Unicode more
    correctly handle Unicode coming in from the system. This also has
    the disappointing side effect that filenames will now be always
    unicode by default in the ``Path`` type which means that this can
    introduce small bugs for code not aware of this.
-   Added a ``type`` parameter to ``Path`` to force a specific string
    type on the value.
-   For users running Python on Windows the ``echo`` and ``prompt``
    functions now work with full unicode functionality in the Python
    windows console by emulating an output stream. This also applies to
    getting the virtual output and input streams via
    ``click.get_text_stream(...)``.
-   Unittests now always force a certain virtual terminal width.
-   Added support for allowing dashes to indicate standard streams to
    the ``Path`` type.
-   Multi commands in chain mode no longer propagate arguments left over
    from parsing to the callbacks. It's also now disallowed through an
    exception when optional arguments are attached to multi commands if
    chain mode is enabled.
-   Relaxed restriction that disallowed chained commands to have other
    chained commands as child commands.
-   Arguments with positive nargs can now have defaults implemented.
    Previously this configuration would often result in slightly
    unexpected values be returned.


Version 5.1
-----------

Released 2015-08-17

-   Fix a bug in ``pass_obj`` that would accidentally pass the context
    too.


Version 5.0
-----------

Released 2015-08-16, codename "tok tok"

-   Removed various deprecated functionality.
-   Atomic files now only accept the ``w`` mode.
-   Change the usage part of help output for very long commands to wrap
    their arguments onto the next line, indented by 4 spaces.
-   Fix a bug where return code and error messages were incorrect when
    using ``CliRunner``.
-   Added ``get_current_context``.
-   Added a ``meta`` dictionary to the context which is shared across
    the linked list of contexts to allow click utilities to place state
    there.
-   Introduced ``Context.scope``.
-   The ``echo`` function is now threadsafe: It calls the ``write``
    method of the underlying object only once.
-   ``prompt(hide_input=True)`` now prints a newline on ``^C``.
-   Click will now warn if users are using ``unicode_literals``.
-   Click will now ignore the ``PAGER`` environment variable if it is
    empty or contains only whitespace.
-   The ``click-contrib`` GitHub organization was created.


Version 4.1
-----------

Released 2015-07-14

-   Fix a bug where error messages would include a trailing ``None``
    string.
-   Fix a bug where Click would crash on docstrings with trailing
    newlines.
-   Support streams with encoding set to ``None`` on Python 3 by barfing
    with a better error.
-   Handle ^C in less-pager properly.
-   Handle return value of ``None`` from ``sys.getfilesystemencoding``
-   Fix crash when writing to unicode files with ``click.echo``.
-   Fix type inference with multiple options.


Version 4.0
-----------

Released 2015-03-31, codename "zoom zoom"

-   Added ``color`` parameters to lots of interfaces that directly or
    indirectly call into echoing. This previously was always
    autodetection (with the exception of the ``echo_via_pager``
    function). Now you can forcefully enable or disable it, overriding
    the auto detection of Click.
-   Added an ``UNPROCESSED`` type which does not perform any type
    changes which simplifies text handling on 2.x / 3.x in some special
    advanced usecases.
-   Added ``NoSuchOption`` and ``BadOptionUsage`` exceptions for more
    generic handling of errors.
-   Added support for handling of unprocessed options which can be
    useful in situations where arguments are forwarded to underlying
    tools.
-   Added ``max_content_width`` parameter to the context which can be
    used to change the maximum width of help output. By default Click
    will not format content for more than 80 characters width.
-   Added support for writing prompts to stderr.
-   Fix a bug when showing the default for multiple arguments.
-   Added support for custom subclasses to ``option`` and ``argument``.
-   Fix bug in ``clear()`` on Windows when colorama is installed.
-   Reject ``nargs=-1`` for options properly. Options cannot be
    variadic.
-   Fixed an issue with bash completion not working properly for
    commands with non ASCII characters or dashes.
-   Added a way to manually update the progressbar.
-   Changed the formatting of missing arguments. Previously the internal
    argument name was shown in error messages, now the metavar is shown
    if passed. In case an automated metavar is selected, it's stripped
    of extra formatting first.


Version 3.3
-----------

Released 2014-09-08

-   Fixed an issue with error reporting on Python 3 for invalid
    forwarding of commands.


Version 3.2
-----------

Released 2014-08-22

-   Added missing ``err`` parameter forwarding to the ``secho``
    function.
-   Fixed default parameters not being handled properly by the context
    invoke method. This is a backwards incompatible change if the
    function was used improperly. See :ref:`upgrade-to-3.2` for more
    information.
-   Removed the ``invoked_subcommands`` attribute largely. It is not
    possible to provide it to work error free due to how the parsing
    works so this API has been deprecated. See :ref:`upgrade-to-3.2` for
    more information.
-   Restored the functionality of ``invoked_subcommand`` which was
    broken as a regression in 3.1.


Version 3.1
-----------

Released 2014-08-13

-   Fixed a regression that caused contexts of subcommands to be created
    before the parent command was invoked which was a regression from
    earlier Click versions.


Version 3.0
-----------

Released 2014-08-12, codename "clonk clonk"

-   Formatter now no longer attempts to accommodate for terminals
    smaller than 50 characters. If that happens it just assumes a
    minimal width.
-   Added a way to not swallow exceptions in the test system.
-   Added better support for colors with pagers and ways to override the
    autodetection.
-   The CLI runner's result object now has a traceback attached.
-   Improved automatic short help detection to work better with dots
    that do not terminate sentences.
-   When defining options without actual valid option strings now,
    Click will give an error message instead of silently passing. This
    should catch situations where users wanted to created arguments
    instead of options.
-   Restructured Click internally to support vendoring.
-   Added support for multi command chaining.
-   Added support for defaults on options with ``multiple`` and options
    and arguments with ``nargs != 1``.
-   Label passed to ``progressbar`` is no longer rendered with
    whitespace stripped.
-   Added a way to disable the standalone mode of the ``main`` method on
    a Click command to be able to handle errors better.
-   Added support for returning values from command callbacks.
-   Added simplifications for printing to stderr from ``echo``.
-   Added result callbacks for groups.
-   Entering a context multiple times defers the cleanup until the last
    exit occurs.
-   Added ``open_file``.


Version 2.6
-----------

Released 2014-08-11

-   Fixed an issue where the wrapped streams on Python 3 would be
    reporting incorrect values for seekable.


Version 2.5
-----------

Released 2014-07-28

-   Fixed a bug with text wrapping on Python 3.


Version 2.4
-----------

Released 2014-07-04

-   Corrected a bug in the change of the help option in 2.3.


Version 2.3
-----------

Released 2014-07-03

-   Fixed an incorrectly formatted help record for count options.
-   Add support for ansi code stripping on Windows if colorama is not
    available.
-   Restored the Click 1.0 handling of the help parameter for certain
    edge cases.


Version 2.2
-----------

Released 2014-06-26

-   Fixed tty detection on PyPy.
-   Fixed an issue that progress bars were not rendered when the context
    manager was entered.


Version 2.1
-----------

Released 2014-06-14

-   Fixed the :func:`launch` function on windows.
-   Improved the colorama support on windows to try hard to not screw up
    the console if the application is interrupted.
-   Fixed windows terminals incorrectly being reported to be 80
    characters wide instead of 79
-   Use colorama win32 bindings if available to get the correct
    dimensions of a windows terminal.
-   Fixed an issue with custom function types on Python 3.
-   Fixed an issue with unknown options being incorrectly reported in
    error messages.


Version 2.0
-----------

Released 2014-06-06, codename "tap tap tap"

-   Added support for opening stdin/stdout on Windows in binary mode
    correctly.
-   Added support for atomic writes to files by going through a
    temporary file.
-   Introduced :exc:`BadParameter` which can be used to easily perform
    custom validation with the same error messages as in the type
    system.
-   Added :func:`progressbar`; a function to show progress bars.
-   Added :func:`get_app_dir`; a function to calculate the home folder
    for configs.
-   Added transparent handling for ANSI codes into the :func:`echo`
    function through ``colorama``.
-   Added :func:`clear` function.
-   Breaking change: parameter callbacks now get the parameter object
    passed as second argument. There is legacy support for old callbacks
    which will warn but still execute the script.
-   Added :func:`style`, :func:`unstyle` and :func:`secho` for ANSI
    styles.
-   Added an :func:`edit` function that invokes the default editor.
-   Added an :func:`launch` function that launches browsers and
    applications.
-   Nargs of -1 for arguments can now be forced to be a single item
    through the required flag. It defaults to not required.
-   Setting a default for arguments now implicitly makes it non
    required.
-   Changed "yN" / "Yn" to "y/N" and "Y/n" in confirmation prompts.
-   Added basic support for bash completion.
-   Added :func:`getchar` to fetch a single character from the terminal.
-   Errors now go to stderr as intended.
-   Fixed various issues with more exotic parameter formats like
    DOS/Windows style arguments.
-   Added :func:`pause` which works similar to the Windows ``pause`` cmd
    built-in but becomes an automatic noop if the application is not run
    through a terminal.
-   Added a bit of extra information about missing choice parameters.
-   Changed how the help function is implemented to allow global
    overriding of the help option.
-   Added support for token normalization to implement case insensitive
    handling.
-   Added support for providing defaults for context settings.


Version 1.1
-----------

Released 2014-05-23

-   Fixed a bug that caused text files in Python 2 to not accept native
    strings.


Version 1.0
-----------

Released 2014-05-21

-   Initial release.
