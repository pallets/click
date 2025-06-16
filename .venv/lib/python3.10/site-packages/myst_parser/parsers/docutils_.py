"""MyST Markdown parser for docutils."""

from collections.abc import Callable, Iterable, Sequence
from dataclasses import Field
from typing import (
    Any,
    Literal,
    get_args,
    get_origin,
)

import yaml
from docutils import frontend, nodes
from docutils.core import default_description, publish_cmdline, publish_string
from docutils.frontend import filter_settings_spec
from docutils.parsers.rst import Parser as RstParser
from docutils.writers.html5_polyglot import HTMLTranslator, Writer

from myst_parser.config.main import (
    MdParserConfig,
    TopmatterReadError,
    merge_file_level,
    read_topmatter,
)
from myst_parser.mdit_to_docutils.base import DocutilsRenderer
from myst_parser.mdit_to_docutils.transforms import (
    CollectFootnotes,
    ResolveAnchorIds,
    SortFootnotes,
    UnreferencedFootnotesDetector,
)
from myst_parser.parsers.mdit import create_md_parser
from myst_parser.warnings_ import MystWarnings, create_warning


def _validate_int(
    setting, value, option_parser, config_parser=None, config_section=None
) -> int:
    """Validate an integer setting."""
    return int(value)


def _validate_comma_separated_set(
    setting, value, option_parser, config_parser=None, config_section=None
) -> set[str]:
    """Validate an integer setting."""
    value = frontend.validate_comma_separated_list(
        setting, value, option_parser, config_parser, config_section
    )
    return set(value)


def _create_validate_tuple(length: int) -> Callable[..., tuple[str, ...]]:
    """Create a validator for a tuple of length `length`."""

    def _validate(
        setting, value, option_parser, config_parser=None, config_section=None
    ):
        string_list = frontend.validate_comma_separated_list(
            setting, value, option_parser, config_parser, config_section
        )
        if len(string_list) != length:
            raise ValueError(
                f"Expecting {length} items in {setting}, got {len(string_list)}."
            )
        return tuple(string_list)

    return _validate


class Unset:
    """A sentinel class for unset settings."""

    def __repr__(self):
        return "UNSET"

    def __bool__(self):
        # this allows to check if the setting is unset/falsy
        return False


DOCUTILS_UNSET = Unset()
"""Sentinel for arguments not set through docutils.conf."""


def _create_validate_yaml(field: Field):
    """Create a deserializer/validator for a json setting."""

    def _validate_yaml(
        setting, value, option_parser, config_parser=None, config_section=None
    ):
        """Check/normalize a key-value pair setting.

        Items delimited by `,`, and key-value pairs delimited by `=`.
        """
        try:
            output = yaml.safe_load(value)
        except Exception as err:
            raise ValueError("Invalid YAML string") from err
        if not isinstance(output, dict):
            raise ValueError("Expecting a YAML dictionary")
        return output

    return _validate_yaml


def _validate_url_schemes(
    setting, value, option_parser, config_parser=None, config_section=None
):
    """Validate a url_schemes setting.

    This is a tricky one, because it can be either a comma-separated list or a YAML dictionary.
    """
    try:
        output = yaml.safe_load(value)
    except Exception as err:
        raise ValueError("Invalid YAML string") from err
    if isinstance(output, str):
        output = {k: None for k in output.split(",")}
    if not isinstance(output, dict):
        raise ValueError("Expecting a comma-delimited str or YAML dictionary")
    return output


def _attr_to_optparse_option(at: Field, default: Any) -> tuple[dict[str, Any], str]:
    """Convert a field into a Docutils optparse options dict.

    :returns: (option_dict, default)
    """
    if at.name == "url_schemes":
        return {
            "metavar": "<comma-delimited>|<yaml-dict>",
            "validator": _validate_url_schemes,
        }, ",".join(default)
    if at.type is int:
        return {"metavar": "<int>", "validator": _validate_int}, str(default)
    if at.type is bool:
        return {
            "metavar": "<boolean>",
            "validator": frontend.validate_boolean,
        }, str(default)
    if at.type is str or at.name == "heading_slug_func":
        return {
            "metavar": "<str>",
        }, f"(default: '{default}')"
    if get_origin(at.type) is Literal and all(
        isinstance(a, str) for a in get_args(at.type)
    ):
        args = get_args(at.type)
        return {
            "metavar": f"<{'|'.join(repr(a) for a in args)}>",
            "type": "choice",
            "choices": args,
        }, repr(default)
    if at.type in (Iterable[str], Sequence[str]):
        return {
            "metavar": "<comma-delimited>",
            "validator": frontend.validate_comma_separated_list,
        }, ",".join(default)
    if at.type == set[str]:
        return {
            "metavar": "<comma-delimited>",
            "validator": _validate_comma_separated_set,
        }, ",".join(default)
    if at.type == tuple[str, str]:
        return {
            "metavar": "<str,str>",
            "validator": _create_validate_tuple(2),
        }, ",".join(default)
    if at.type == int | type(None):
        return {
            "metavar": "<null|int>",
            "validator": _validate_int,
        }, str(default)
    if at.type == Iterable[str] | type(None):
        return {
            "metavar": "<null|comma-delimited>",
            "validator": frontend.validate_comma_separated_list,
        }, ",".join(default) if default else ""
    if get_origin(at.type) is dict:
        return {
            "metavar": "<yaml-dict>",
            "validator": _create_validate_yaml(at),
        }, str(default) if default else ""
    raise AssertionError(
        f"Configuration option {at.name} not set up for use in docutils.conf."
    )


def attr_to_optparse_option(
    attribute: Field, default: Any, prefix: str = "myst_"
) -> tuple[str, list[str], dict[str, Any]]:
    """Convert an ``MdParserConfig`` attribute into a Docutils setting tuple.

    :returns: A tuple of ``(help string, option flags, optparse kwargs)``.
    """
    name = f"{prefix}{attribute.name}"
    flag = "--" + name.replace("_", "-")
    options = {"dest": name, "default": DOCUTILS_UNSET}
    at_options, default_str = _attr_to_optparse_option(attribute, default)
    options.update(at_options)
    help_str = attribute.metadata.get("help", "") if attribute.metadata else ""
    if default_str:
        help_str += f" (default: {default_str})"
    return (help_str, [flag], options)


def create_myst_settings_spec(config_cls=MdParserConfig, prefix: str = "myst_"):
    """Return a list of Docutils setting for the docutils MyST section."""
    defaults = config_cls()
    return tuple(
        attr_to_optparse_option(at, getattr(defaults, at.name), prefix)
        for at in config_cls.get_fields()
        if ("docutils" not in at.metadata.get("omit", []))
    )


def create_myst_config(
    settings: frontend.Values,
    config_cls=MdParserConfig,
    prefix: str = "myst_",
):
    """Create a configuration instance from the given settings."""
    values = {}
    for attribute in config_cls.get_fields():
        if "docutils" in attribute.metadata.get("omit", []):
            continue
        setting = f"{prefix}{attribute.name}"
        val = getattr(settings, setting, DOCUTILS_UNSET)
        if val is not DOCUTILS_UNSET:
            values[attribute.name] = val
    return config_cls(**values)


class Parser(RstParser):
    """Docutils parser for Markedly Structured Text (MyST)."""

    supported: tuple[str, ...] = ("md", "markdown", "myst")
    """Aliases this parser supports."""

    settings_spec = (
        "MyST options",
        None,
        create_myst_settings_spec(),
        *RstParser.settings_spec,
    )
    """Runtime settings specification."""

    config_section = "myst parser"
    config_section_dependencies = ("parsers",)
    translate_section_name = None

    def get_transforms(self):
        return super().get_transforms() + [
            UnreferencedFootnotesDetector,
            SortFootnotes,
            CollectFootnotes,
            ResolveAnchorIds,
        ]

    def parse(self, inputstring: str, document: nodes.document) -> None:
        """Parse source text.

        :param inputstring: The source string to parse
        :param document: The root docutils node to add AST elements to
        """
        from docutils.writers._html_base import HTMLTranslator

        HTMLTranslator.visit_rubric = visit_rubric_html
        HTMLTranslator.depart_rubric = depart_rubric_html
        HTMLTranslator.visit_container = visit_container_html
        HTMLTranslator.depart_container = depart_container_html

        self.setup_parse(inputstring, document)

        # check for exorbitantly long lines
        if hasattr(document.settings, "line_length_limit"):
            for i, line in enumerate(inputstring.split("\n")):
                if len(line) > document.settings.line_length_limit:
                    error = document.reporter.error(
                        f"Line {i+1} exceeds the line-length-limit:"
                        f" {document.settings.line_length_limit}."
                    )
                    document.append(error)
                    return

        # create parsing configuration from the global config
        try:
            config = create_myst_config(document.settings)
        except Exception as exc:
            error = document.reporter.error(f"Global myst configuration invalid: {exc}")
            document.append(error)
            config = MdParserConfig()

        if "attrs_image" in config.enable_extensions:
            create_warning(
                document,
                "The `attrs_image` extension is deprecated, "
                "please use `attrs_inline` instead.",
                MystWarnings.DEPRECATED,
            )

        # update the global config with the file-level config
        try:
            topmatter = read_topmatter(inputstring)
        except TopmatterReadError:
            pass  # this will be reported during the render
        else:
            if topmatter:
                warning = lambda wtype, msg: create_warning(  # noqa: E731
                    document, msg, wtype, line=1, append_to=document
                )
                config = merge_file_level(config, topmatter, warning)

        # parse content
        parser = create_md_parser(config, DocutilsRenderer)
        parser.options["document"] = document
        parser.render(inputstring)

        # post-processing

        # replace raw nodes if raw is not allowed
        if not getattr(document.settings, "raw_enabled", True):
            for node in document.traverse(nodes.raw):
                warning = document.reporter.warning("Raw content disabled.")
                node.parent.replace(node, warning)

        self.finish_parse()


class SimpleTranslator(HTMLTranslator):
    def stylesheet_call(self, *args, **kwargs):
        return ""


class SimpleWriter(Writer):
    settings_spec = filter_settings_spec(
        Writer.settings_spec,
        "template",
    )

    def apply_template(self):
        subs = self.interpolation_dict()
        return "{body}\n".format(**subs)

    def __init__(self):
        self.parts = {}
        self.translator_class = SimpleTranslator


def _run_cli(writer_name: str, writer_description: str, argv: list[str] | None):
    """Run the command line interface for a particular writer."""
    publish_cmdline(
        parser=Parser(),
        writer_name=writer_name,
        description=(
            f"Generates {writer_description} from standalone MyST sources.\n{default_description}"
        ),
        argv=argv,
    )


def cli_html(argv: list[str] | None = None) -> None:
    """Cmdline entrypoint for converting MyST to HTML."""
    _run_cli("html", "(X)HTML documents", argv)


def cli_html5(argv: list[str] | None = None):
    """Cmdline entrypoint for converting MyST to HTML5."""
    _run_cli("html5", "HTML5 documents", argv)


def cli_html5_demo(argv: list[str] | None = None):
    """Cmdline entrypoint for converting MyST to simple HTML5 demonstrations.

    This is a special case of the HTML5 writer,
    that only outputs the body of the document.
    """
    publish_cmdline(
        parser=Parser(),
        writer=SimpleWriter(),
        description=(
            f"Generates body HTML5 from standalone MyST sources.\n{default_description}"
        ),
        settings_overrides={
            "doctitle_xform": False,
            "sectsubtitle_xform": False,
            "initial_header_level": 1,
        },
        argv=argv,
    )


def to_html5_demo(inputstring: str, **kwargs) -> str:
    """Convert a MyST string to HTML5."""
    overrides = {
        "doctitle_xform": False,
        "sectsubtitle_xform": False,
        "initial_header_level": 1,
        "output_encoding": "unicode",
    }
    overrides.update(kwargs)
    return publish_string(
        inputstring,
        parser=Parser(),
        writer=SimpleWriter(),
        settings_overrides=overrides,
    )


def cli_latex(argv: list[str] | None = None):
    """Cmdline entrypoint for converting MyST to LaTeX."""
    _run_cli("latex", "LaTeX documents", argv)


def cli_xml(argv: list[str] | None = None):
    """Cmdline entrypoint for converting MyST to XML."""
    _run_cli("xml", "Docutils-native XML", argv)


def cli_pseudoxml(argv: list[str] | None = None):
    """Cmdline entrypoint for converting MyST to pseudo-XML."""
    _run_cli("pseudoxml", "pseudo-XML", argv)


def visit_rubric_html(self, node):
    """Override the default HTML visit method for rubric nodes.

    docutils structures a document, based on the headings, into nested sections::

        # h1
        ## h2
        ### h3

        <section>
            <title>
                h1
            <section>
                <title>
                    h2
                <section>
                    <title>
                        h3

    This means that it is not possible to have "standard" headings nested inside
    other components, such as blockquotes, because it would break the structure::

        # h1
        > ## h2
        ### h3

        <section>
            <title>
                h1
            <blockquote>
                <section>
                    <title>
                        h2
            <section>
                <title>
                    h3

    we work around this shortcoming, in `DocutilsRenderer.render_heading`,
    by identifying if a heading is inside another component
    and instead outputting it as a "non-structural" rubric node, and capture the level::

        <section>
            <title>
                h1
            <blockquote>
                <rubric level=2>
                    h2
            <section>
                <title>
                    h3

    However, docutils natively just outputs rubrics as <p> tags,
    and does not "honor" the heading level.
    So here we override the visit/depart methods to output the correct <h> element
    """
    if "level" in node:
        self.body.append(self.starttag(node, f'h{node["level"]}', "", CLASS="rubric"))
    else:
        self.body.append(self.starttag(node, "p", "", CLASS="rubric"))


def depart_rubric_html(self, node):
    """Override the default HTML visit method for rubric nodes.

    See explanation in `visit_rubric_html`
    """
    if "level" in node:
        self.body.append(f'</h{node["level"]}>\n')
    else:
        self.body.append("</p>\n")


def visit_container_html(self, node: nodes.Node):
    """Override the default HTML visit method for container nodes.

    to remove the "container" class for divs
    this avoids CSS clashes with the bootstrap theme
    """
    classes = "docutils container"
    attrs = {}
    if node.get("is_div", False):
        # we don't want the CSS for container for these nodes
        classes = "docutils"
    if "style" in node:
        attrs["style"] = node["style"]
    self.body.append(self.starttag(node, "div", CLASS=classes, **attrs))


def depart_container_html(self, node: nodes.Node):
    """Override the default HTML depart method for container nodes.

    See explanation in `visit_container_html`
    """
    self.body.append("</div>\n")
