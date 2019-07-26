# Based on: https://gist.github.com/jnothman/3f164a9f8f766009d29a95ab473ff972
# Also see https://github.com/hynek/doc2dash/issues/57

import logging

import doc2dash.parsers
from doc2dash.parsers.intersphinx import (
    InterSphinxParser,
    inv_entry_to_path,
    ParserEntry,
)


log = logging.getLogger(__name__)


class Skip(Exception):
    pass


class ClickParser(InterSphinxParser):
    def __init__(self, *args, **kwargs):
        super(ClickParser, self).__init__(*args, **kwargs)
        self.guides = set()

    def convert_type(self, inv_type):
        if inv_type == "std:doc":  # sphinx type
            return "Guide"  # Dash type
        elif inv_type == "std:label":  # sphinx type
            return "Section"  # Dash type
        else:
            return super(ClickParser, self).convert_type(inv_type)

    def create_entry(self, dash_type, key, inv_entry):
        try:
            if dash_type == "Guide":
                path_str = inv_entry_to_path(inv_entry)
                name = inv_entry[3]

                self.guides.add(key)

                if key == "api":
                    # Dash does API
                    raise Skip()

                return ParserEntry(name=name, type=dash_type, path=path_str)
            elif dash_type == "Section":
                path_str = inv_entry_to_path(inv_entry)
                name = inv_entry[3]

                if key in self.guides:
                    # already a Guide
                    raise Skip("is a guide")

                key_parts = key.split(":")

                if key_parts[0] == "changelog":
                    # don't need versions in here, only list the Changelog Guide.
                    raise Skip()

                if key_parts[0] in {"index", "api"}:
                    # repeated elsewhere
                    raise Skip()

                if key_parts[0] == "search":
                    # Dash does search
                    raise Skip()

                if len(key_parts) == 2 and (key_parts[0] == key_parts[1]):
                    # headings for guides
                    raise Skip()

                if inv_entry[2] in {
                        "advanced.html#aliases",
                        "arguments.html#file-args",
                        "options.html#choice-opts",
                        "options.html#option-prompting",
                        "options.html#ranges",
                        "options.html#tuple-type",
                        "complex.html#complex-guide",
                        "documentation.html#doc-meta-variables",
                        "python3.html#python3-limitations",
                        "python3.html#python3-surrogates",
                        "upgrading.html#upgrade-to-2-0",
                        "upgrading.html#upgrade-to-3-2",
                        }:
                    # FIXME: missing named anchors which end up with repeated entries.
                    raise Skip()

                return ParserEntry(name=name, type=dash_type, path=path_str)

        except Skip:
            log.debug("Skipping %s '%s'", dash_type, key)
            return None

        return super(ClickParser, self).create_entry(dash_type, key, inv_entry)


doc2dash.parsers.DOCTYPES = [ClickParser]

if __name__ == "__main__":
    import doc2dash.__main__

    doc2dash.__main__.main()
