import csv
import inspect
import re
from io import StringIO

from docutils import nodes
from docutils.statemachine import StringList
from sphinx.domains import Domain
from sphinx.util import import_object
from sphinx.util.docutils import SphinxDirective


def build_function_directive(name, aliases, func):
    """Build a function directive, with name, signature, docs, and
    aliases.

    .. code-block:: rst

        .. function:: name(signature)

            doc
            doc

            :aliases: ``name2``, ``name3``

    :param name: The name mapped to the function, which may not match
        the real name of the function.
    :param aliases: Other names mapped to the function.
    :param func: The function.
    :return: A list of lines of reStructuredText to be rendered.

    If the function is a Jinja environment, context, or eval context
    filter, the first argument is omitted from the signature since it's
    not seen by template developers.

    If the filter is a Jinja async variant, it is unwrapped to its sync
    variant to get the docs and signature.
    """
    if getattr(func, "jinja_async_variant", False):
        # unwrap async filters to their normal variant
        func = inspect.unwrap(func)

    doc = inspect.getdoc(func).splitlines()

    try:
        sig = inspect.signature(func, follow_wrapped=False)
    except ValueError:
        # some c function that doesn't report its signature (ex. MarkupSafe.escape)
        # try the first line of the docs, fall back to generic value
        sig = "(value)"
        m = re.match(r"[a-zA-Z_]\w*(\(.*?\))", doc[0])

        if m is not None:
            doc = doc[1:]
            sig = m.group(1)
    else:
        if getattr(func, "jinja_pass_arg", None) is not None:
            # remove the internal-only first argument from context filters
            params = list(sig.parameters.values())

            if params[0].kind != inspect.Parameter.VAR_POSITIONAL:
                # only remove it if it's not "*args"
                del params[0]

            sig = sig.replace(parameters=params)

    result = ["", f".. function:: {name}{sig}", ""]
    result.extend([f"    {x}" for x in doc])

    if aliases:
        result.append("")
        alias_str = ", ".join([f"``{x}``" for x in sorted(aliases)])
        result.append(f"    :aliases: {alias_str}")

    return result


class MappedFunctionsDirective(SphinxDirective):
    """Take a dict of names to functions and produce rendered docs.
    Requires one argument, the import name of the dict to process.

    Used for the ``jinja:filters::` and `jinja:tests::` directives.

    Multiple names can point to the same function. In this case the
    shortest name is used as the primary name, and other names are
    displayed as aliases. Comparison operators are special cased to
    prefer their two letter names, like "eq".

    The docs are sorted by primary name. A table is rendered above the
    docs as a compact table of contents linking to each function.
    """

    required_arguments = 1

    def _build_functions(self):
        """Imports the dict and builds the output for the functions.
        This is what determines aliases and performs sorting.

        Calls :func:`build_function_directive` for each function, then
        renders the list of reStructuredText to nodes.

        The list of sorted names is stored for use by
        :meth:`_build_table`.

        :return: A list of rendered nodes.
        """
        map_name = self.arguments[0]
        mapping = import_object(map_name)
        grouped = {}

        # reverse the mapping to get a list of aliases for each function
        for key, value in mapping.items():
            grouped.setdefault(value, []).append(key)

        # store the function names for use by _build_table
        self.funcs = funcs = []
        compare_ops = {"eq", "ge", "gt", "le", "lt", "ne"}

        for func, names in grouped.items():
            # use the longest alias as the canonical name
            names.sort(key=len)
            # adjust for special cases
            names.sort(key=lambda x: x in compare_ops)
            name = names.pop()
            funcs.append((name, names, func))

        funcs.sort()
        result = StringList()

        # generate and collect markup
        for name, aliases, func in funcs:
            for item in build_function_directive(name, aliases, func):
                result.append(item, "<jinja>")

        # parse the generated markup into nodes
        node = nodes.Element()
        self.state.nested_parse(result, self.content_offset, node)
        return node.children

    def _build_table(self):
        """Takes the sorted list of names produced by
        :meth:`_build_functions` and builds the nodes for the table of
        contents.

        The table is hard coded to be 5 columns wide. Names are rendered
        in alphabetical order in columns.

        :return: A list of rendered nodes.
        """
        # the reference markup to link to each name
        names = [f":func:`{name}`" for name, _, _ in self.funcs]
        # total number of rows, the number of names divided by the
        # number of columns, plus one in case of overflow
        row_size = (len(names) // 5) + bool(len(names) % 5)
        # pivot to rows so that names remain alphabetical in columns
        rows = [names[i::row_size] for i in range(row_size)]

        # render the names to CSV for the csv-table directive
        out = StringIO()
        writer = csv.writer(out)
        writer.writerows(rows)

        # generate the markup for the csv-table directive
        result = ["", ".. csv-table::", "    :align: left", ""]
        result.extend([f"    {line}" for line in out.getvalue().splitlines()])

        # parse the generated markup into nodes
        result = StringList(result, "<jinja>")
        node = nodes.Element()
        self.state.nested_parse(result, self.content_offset, node)
        return node.children

    def run(self):
        """Render the table and function docs.

        Build the functions first to calculate the names and order, then
        build the table. Return the table above the functions.

        :return: A list of rendered nodes.
        """
        functions = self._build_functions()
        table = self._build_table()
        return table + functions


class NodesDirective(SphinxDirective):
    """Take a base Jinja ``Node`` class and render docs for it and all
    subclasses, recursively, depth first. Requires one argument, the
    import name of the base class.

    Used for the ``jinja:nodes::` directive.

    Each descendant renders a link back to its parent.
    """

    required_arguments = 1

    def run(self):
        def walk(cls):
            """Render the given class, then recursively render its
            descendants depth first.

            Appends to the outer ``lines`` variable.

            :param cls: The Jinja ``Node`` class to render.
            """
            lines.append(
                ".. autoclass:: {}({})".format(cls.__name__, ", ".join(cls.fields))
            )

            # render member methods for nodes marked abstract
            if cls.abstract:
                members = []

                for key, value in cls.__dict__.items():
                    if (
                        not key.startswith("_")
                        and not hasattr(cls.__base__, key)
                        and callable(value)
                    ):
                        members.append(key)

                if members:
                    members.sort()
                    lines.append("    :members: " + ", ".join(members))

            # reference the parent node, except for the base node
            if cls.__base__ is not object:
                lines.append("")
                lines.append(f"    :Node type: :class:`{cls.__base__.__name__}`")

            lines.append("")
            children = cls.__subclasses__()
            children.sort(key=lambda x: x.__name__.lower())

            # render each child
            for child in children:
                walk(child)

        # generate the markup starting at the base class
        lines = []
        target = import_object(self.arguments[0])
        walk(target)

        # parse the generated markup into nodes
        doc = StringList(lines, "<jinja>")
        node = nodes.Element()
        self.state.nested_parse(doc, self.content_offset, node)
        return node.children


class JinjaDomain(Domain):
    name = "jinja"
    label = "Jinja"
    directives = {
        "filters": MappedFunctionsDirective,
        "tests": MappedFunctionsDirective,
        "nodes": NodesDirective,
    }

    def merge_domaindata(self, docnames, otherdata):
        # Needed to support parallel build.
        # Not using self.data -- nothing to merge.
        pass


def setup(app):
    app.add_domain(JinjaDomain)
