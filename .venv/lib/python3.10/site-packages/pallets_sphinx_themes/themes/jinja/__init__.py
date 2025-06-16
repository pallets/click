from pygments.style import Style
from pygments.token import Comment
from pygments.token import Error
from pygments.token import Generic
from pygments.token import Keyword
from pygments.token import Name
from pygments.token import Number
from pygments.token import Operator
from pygments.token import String


class JinjaStyle(Style):
    background_color = "#f8f8f8"
    default_style = ""
    styles = {
        Comment: "italic #aaaaaa",
        Comment.Preproc: "noitalic #b11414",
        Comment.Special: "italic #505050",
        Keyword: "bold #b80000",
        Keyword.Type: "#808080",
        Operator.Word: "bold #b80000",
        Name.Builtin: "#333333",
        Name.Function: "#333333",
        Name.Class: "bold #333333",
        Name.Namespace: "bold #333333",
        Name.Entity: "bold #363636",
        Name.Attribute: "#686868",
        Name.Tag: "bold #686868",
        Name.Decorator: "#686868",
        String: "#aa891c",
        Number: "#444444",
        Generic.Heading: "bold #000080",
        Generic.Subheading: "bold #800080",
        Generic.Deleted: "#aa0000",
        Generic.Inserted: "#00aa00",
        Generic.Error: "#aa0000",
        Generic.Emph: "italic",
        Generic.Strong: "bold",
        Generic.Prompt: "#555555",
        Generic.Output: "#888888",
        Generic.Traceback: "#aa0000",
        Error: "#f00 bg:#faa",
    }


def setup(app):
    """Load the Jinja extension if Jinja is installed."""
    try:
        from . import domain
    except ImportError:
        return

    domain.setup(app)
