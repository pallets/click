"""Fenced code blocks are parsed as directives,
if the block starts with ``{directive_name}``,
followed by arguments on the same line.

Directive options are read from a YAML block,
if the first content line starts with ``---``, e.g.

::

    ```{directive_name} arguments
    ---
    option1: name
    option2: |
        Longer text block
    ---
    content...
    ```

Or the option block will be parsed if the first content line starts with ``:``,
as a YAML block consisting of every line that starts with a ``:``, e.g.

::

    ```{directive_name} arguments
    :option1: name
    :option2: other

    content...
    ```

If the first line of a directive's content is blank, this will be stripped
from the content.
This is to allow for separation between the option block and content.

"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from textwrap import dedent
from typing import Any

import yaml
from docutils.parsers.rst import Directive
from docutils.parsers.rst.directives import flag
from docutils.parsers.rst.directives.misc import TestDirective
from docutils.parsers.rst.states import MarkupError

from myst_parser.warnings_ import MystWarnings

from .options import TokenizeError, options_to_items


@dataclass
class ParseWarnings:
    msg: str
    lineno: int | None = None
    type: MystWarnings = MystWarnings.DIRECTIVE_PARSING


@dataclass
class DirectiveParsingResult:
    arguments: list[str]
    """The arguments parsed from the first line."""
    options: dict
    """Options parsed from the YAML block."""
    body: list[str]
    """The lines of body content"""
    body_offset: int
    """The number of lines to the start of the body content."""
    warnings: list[ParseWarnings]
    """List of non-fatal errors encountered during parsing.
    (message, line_number)
    """


def parse_directive_text(
    directive_class: type[Directive],
    first_line: str,
    content: str,
    *,
    line: int | None = None,
    validate_options: bool = True,
    additional_options: dict[str, str] | None = None,
) -> DirectiveParsingResult:
    """Parse (and validate) the full directive text.

    :param first_line: The text on the same line as the directive name.
        May be an argument or body text, dependent on the directive
    :param content: All text after the first line. Can include options.
    :param validate_options: Whether to validate the values of options
        This is actually only here to be used by myst-nb cells,
        which converts options directly to JSON metadata, using the full YAML spec.
    :param additional_options: Additional options to add to the directive,
        above those parsed from the content (content options take priority).

    :raises MarkupError: if there is a fatal parsing/validation error
    """
    parse_warnings: list[ParseWarnings]
    options: dict[str, Any]
    body_lines: list[str]
    content_offset: int
    has_options_block: bool

    if directive_class.option_spec:
        # only look for an option block if there are possible options
        # body, options, option_errors = _parse_directive_options(
        result = _parse_directive_options(
            content,
            directive_class,
            line=line,
            as_yaml=not validate_options,
            additional_options=additional_options,
        )
        parse_warnings = result.warnings
        has_options_block = result.has_options
        options = result.options
        body_lines = result.content.splitlines()
        content_offset = len(content.splitlines()) - len(body_lines)
    else:
        parse_warnings = []
        has_options_block = False
        options = {}
        body_lines = content.splitlines()
        content_offset = 0

    if not (directive_class.required_arguments or directive_class.optional_arguments):
        # If there are no possible arguments, then the body can start on the argument line
        if first_line.strip():
            if has_options_block and any(body_lines):
                parse_warnings.append(
                    ParseWarnings(
                        "Splitting content across first line and body, "
                        "when an options block is present, is not recommended"
                    )
                )
            body_lines.insert(0, first_line)
            content_offset = 0
        arguments = []
    else:
        arguments = parse_directive_arguments(directive_class, first_line)

    # remove first line of body if blank
    # this is to allow space between the options and the content
    if body_lines and not body_lines[0].strip():
        body_lines = body_lines[1:]
        content_offset += 1

    # check for body content
    if body_lines and not directive_class.has_content:
        parse_warnings.append(ParseWarnings("Has content, but none permitted"))

    return DirectiveParsingResult(
        arguments, options, body_lines, content_offset, parse_warnings
    )


@dataclass
class _DirectiveOptions:
    content: str
    options: dict[str, Any]
    warnings: list[ParseWarnings]
    has_options: bool


def _parse_directive_options(
    content: str,
    directive_class: type[Directive],
    as_yaml: bool,
    line: int | None,
    additional_options: dict[str, str] | None = None,
) -> _DirectiveOptions:
    """Parse (and validate) the directive option section.

    :returns: (content, options, validation_errors)
    """
    options_block: None | str = None
    if content.startswith("---"):
        line = None if line is None else line + 1
        content = "\n".join(content.splitlines()[1:])
        match = re.search(r"^-{3,}", content, re.MULTILINE)
        if match:
            options_block = content[: match.start()]
            content = content[match.end() + 1 :]  # TODO advance line number
        else:
            options_block = content
            content = ""
        options_block = dedent(options_block)
    elif content.lstrip().startswith(":"):
        content_lines = content.splitlines()
        yaml_lines = []
        while content_lines:
            if not content_lines[0].lstrip().startswith(":"):
                break
            yaml_lines.append(content_lines.pop(0).lstrip()[1:])
        options_block = "\n".join(yaml_lines)
        content = "\n".join(content_lines)

    has_options_block = options_block is not None

    if as_yaml:
        yaml_errors: list[ParseWarnings] = []
        try:
            yaml_options = yaml.safe_load(options_block or "") or {}
        except (yaml.parser.ParserError, yaml.scanner.ScannerError):
            yaml_options = {}
            yaml_errors.append(
                ParseWarnings(
                    "Invalid options format (bad YAML)",
                    line,
                    MystWarnings.DIRECTIVE_OPTION,
                )
            )
        if not isinstance(yaml_options, dict):
            yaml_options = {}
            yaml_errors.append(
                ParseWarnings(
                    "Invalid options format (not a dict)",
                    line,
                    MystWarnings.DIRECTIVE_OPTION,
                )
            )
        return _DirectiveOptions(content, yaml_options, yaml_errors, has_options_block)

    validation_errors: list[ParseWarnings] = []

    options: dict[str, str] = {}
    if options_block is not None:
        try:
            _options, state = options_to_items(options_block)
            options = dict(_options)
        except TokenizeError as err:
            return _DirectiveOptions(
                content,
                options,
                [
                    ParseWarnings(
                        f"Invalid options format: {err.problem}",
                        line,
                        MystWarnings.DIRECTIVE_OPTION,
                    )
                ],
                has_options_block,
            )
        if state.has_comments:
            validation_errors.append(
                ParseWarnings(
                    "Directive options has # comments, which may not be supported in future versions.",
                    line,
                    MystWarnings.DIRECTIVE_OPTION_COMMENTS,
                )
            )

    if issubclass(directive_class, TestDirective):
        # technically this directive spec only accepts one option ('option')
        # but since its for testing only we accept all options
        return _DirectiveOptions(content, options, [], has_options_block)

    if additional_options:
        # The options block takes priority over additional options
        options = {**additional_options, **options}

    # check options against spec
    options_spec: dict[str, Callable] = directive_class.option_spec
    unknown_options: list[str] = []
    new_options: dict[str, Any] = {}
    value: str | None
    for name, value in options.items():
        try:
            converter = options_spec[name]
        except KeyError:
            unknown_options.append(name)
            continue
        if not value:
            # restructured text parses empty option values as None
            value = None
        if converter is flag:
            # flag will error if value is not empty,
            # but to be more permissive we allow any value
            value = None
        try:
            converted_value = converter(value)
        except (ValueError, TypeError) as error:
            validation_errors.append(
                ParseWarnings(
                    f"Invalid option value for {name!r}: {value}: {error}",
                    line,
                    MystWarnings.DIRECTIVE_OPTION,
                )
            )
        else:
            new_options[name] = converted_value

    if unknown_options:
        validation_errors.append(
            ParseWarnings(
                f"Unknown option keys: {sorted(unknown_options)} "
                f"(allowed: {sorted(options_spec)})",
                line,
                MystWarnings.DIRECTIVE_OPTION,
            )
        )

    return _DirectiveOptions(content, new_options, validation_errors, has_options_block)


def parse_directive_arguments(
    directive_cls: type[Directive], arg_text: str
) -> list[str]:
    """Parse (and validate) the directive argument section."""
    required = directive_cls.required_arguments
    optional = directive_cls.optional_arguments
    arguments = arg_text.split()
    if len(arguments) < required:
        raise MarkupError(f"{required} argument(s) required, {len(arguments)} supplied")
    elif len(arguments) > required + optional:
        if directive_cls.final_argument_whitespace:
            arguments = arg_text.split(None, required + optional - 1)
        else:
            raise MarkupError(
                f"maximum {required + optional} argument(s) allowed, "
                f"{len(arguments)} supplied"
            )
    return arguments
