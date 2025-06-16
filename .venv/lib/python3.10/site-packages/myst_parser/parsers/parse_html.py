"""A simple but complete HTML to Abstract Syntax Tree (AST) parser.

The AST can also reproduce the HTML text.

Example::

    >> text = '<div class="note"><p>text</p></div>'
    >> ast = tokenize_html(text)
    >> list(ast.walk(include_self=True))
    [Root(''), Tag('div', {'class': 'note'}), Tag('p'), Data('text')]
    >> str(ast)
    '<div class="note"><p>text</p></div>'
    >> str(ast[0][0])
    '<p>text</p>'

Note: optional tags are not accounted for
(see https://html.spec.whatwg.org/multipage/syntax.html#optional-tags)

"""

from __future__ import annotations

import inspect
import itertools
from collections import abc, deque
from collections.abc import Callable, Iterable, Iterator
from html.parser import HTMLParser
from typing import Any


class Attribute(dict):
    """This class holds the tags's attributes."""

    def __getitem__(self, key: str) -> str:
        """If self doesn't have the key it returns ''."""
        return self.get(key, "")

    @property
    def classes(self) -> list[str]:
        """Return 'class' attribute as list."""
        return self["class"].split()

    def __str__(self) -> str:
        """Return a htmlized representation for attributes."""
        return " ".join(f'{key}="{value}"' for key, value in self.items())


class Element(abc.MutableSequence):
    """An Element of the xml/html document.

    All xml/html entities inherit from this class.
    """

    def __init__(self, name: str = "", attr: dict | None = None) -> None:
        """Initialise the element."""
        self.name = name
        self.attrs: Attribute = Attribute(attr or {})
        self._parent: Element | None = None
        self._children: list[Element] = []

    @property
    def parent(self) -> Element | None:
        """Return parent."""
        return self._parent

    @property
    def children(self) -> list[Element]:
        """Return copy of children."""
        return self._children[:]

    def reset_children(self, children: list[Element], deepcopy: bool = False):
        new_children = []
        for i, item in enumerate(children):
            assert isinstance(item, Element)
            if deepcopy:
                item = item.deepcopy()
            if item._parent is None:
                item._parent = self
            elif item._parent != self:
                raise AssertionError(f"different parent already set for item {i}")
            new_children.append(item)
        self._children = new_children

    def __getitem__(self, index: int) -> Element:  # type: ignore[override]
        return self._children[index]

    def __setitem__(self, index: int, item: Element):  # type: ignore[override]
        assert isinstance(item, Element)
        if item._parent is not None and item._parent != self:
            raise AssertionError(f"different parent already set for: {item!r}")
        item._parent = self
        return self._children.__setitem__(index, item)

    def __delitem__(self, index: int):  # type: ignore[override]
        return self._children.__delitem__(index)

    def __len__(self) -> int:
        return self._children.__len__()

    def __iter__(self) -> Iterator[Element]:
        yield from self._children

    def insert(self, index: int, item: Element):
        assert isinstance(item, Element)
        if item._parent is not None and item._parent != self:
            raise AssertionError(f"different parent already set for: {item!r}")
        item._parent = self
        return self._children.insert(index, item)

    def deepcopy(self) -> Element:
        """Recursively copy and remove parent."""
        _copy = self.__class__(self.name, self.attrs)
        for child in self:
            _copy_child = child.deepcopy()
            _copy.append(_copy_child)
        return _copy

    def __repr__(self) -> str:
        text = f"{self.__class__.__name__}({self.name!r}"
        if self.attrs:
            text += f", {self.attrs!r}"
        text += ")"
        return text

    def render(
        self,
        tag_overrides: dict[str, Callable[[Element, dict], str]] | None = None,
        **kwargs,
    ) -> str:
        """Returns a HTML string representation of the element.

        :param tag_overrides: Provide a dictionary of render function
            for specific tag names, to override the normal render format

        """
        raise NotImplementedError

    def __str__(self) -> str:
        return self.render()

    def __eq__(self, item: Any) -> bool:
        return item is self

    def walk(self, include_self: bool = False) -> Iterator[Element]:
        """Walk through the xml/html AST."""
        if include_self:
            yield self
        for child in self:
            yield child
            yield from child.walk()

    def strip(self, inplace: bool = False, recurse: bool = False) -> Element:
        """Return copy with all `Data` tokens
        that only contain whitespace / newlines removed.
        """
        element = self
        if not inplace:
            element = self.deepcopy()
        element.reset_children(
            [
                e
                for e in element.children
                if not (isinstance(e, Data) and e.data.strip() == "")
            ]
        )
        if recurse:
            for child in element:
                child.strip(inplace=True, recurse=True)
        return element

    def find(
        self,
        identifier: str | type[Element],
        attrs: dict | None = None,
        classes: Iterable[str] | None = None,
        include_self: bool = False,
        recurse: bool = True,
    ) -> Iterator[Element]:
        """Find all elements that match name and specific attributes."""
        iterator = self.walk() if recurse else self
        if include_self:
            iterator = itertools.chain([self], iterator)
        test_func = (
            (lambda c: isinstance(c, identifier))
            if inspect.isclass(identifier)
            else lambda c: c.name == identifier
        )
        classes = set(classes) if classes is not None else classes
        for child in iterator:
            if test_func(child):
                if classes is not None and not classes.issubset(child.attrs.classes):
                    continue
                for key, value in (attrs or {}).items():
                    if child.attrs[key] != value:
                        break
                else:
                    yield child


class Root(Element):
    """The root of the AST tree."""

    def render(self, **kwargs) -> str:  # type: ignore[override]
        """Returns a string HTML representation of the structure."""
        return "".join(child.render(**kwargs) for child in self)


class Tag(Element):
    """Represent xml/html tags under the form: <name key="value" ...> ... </name>."""

    def render(
        self,
        tag_overrides: dict[str, Callable[[Element, dict], str]] | None = None,
        **kwargs,
    ) -> str:
        if tag_overrides and self.name in tag_overrides:
            return tag_overrides[self.name](self, tag_overrides)
        return (
            f"<{self.name}{' ' if self.attrs else ''}{self.attrs}>"
            + "".join(
                child.render(tag_overrides=tag_overrides, **kwargs) for child in self
            )
            + f"</{self.name}>"
        )


class XTag(Element):
    """Represent XHTML style tags with no children, like `<img src="t.gif" />`"""

    def render(
        self,
        tag_overrides: dict[str, Callable[[Element, dict], str]] | None = None,
        **kwargs,
    ) -> str:
        if tag_overrides is not None and self.name in tag_overrides:
            return tag_overrides[self.name](self, tag_overrides)
        return f"<{self.name}{' ' if self.attrs else ''}{self.attrs}/>"


class VoidTag(Element):
    """Represent tags with no children, only start tag, like `<img src="t.gif" >`"""

    def render(self, **kwargs) -> str:  # type: ignore[override]
        return f"<{self.name}{' ' if self.attrs else ''}{self.attrs}>"


class TerminalElement(Element):
    def __init__(self, data: str):
        super().__init__("")
        self.data: str = data

    def __repr__(self) -> str:
        text = self.data
        if len(text) > 20:
            text = text[:17] + "..."
        return f"{self.__class__.__name__}({text!r})"

    def deepcopy(self) -> TerminalElement:
        """Copy and remove parent."""
        _copy = self.__class__(self.data)
        return _copy


class Data(TerminalElement):
    """Represent data inside xml/html documents, like raw text."""

    def render(self, **kwargs) -> str:  # type: ignore[override]
        return self.data


class Declaration(TerminalElement):
    """Represent declarations, like `<!DOCTYPE html>`"""

    def render(self, **kwargs) -> str:  # type: ignore[override]
        return f"<!{self.data}>"


class Comment(TerminalElement):
    """Represent HTML comments"""

    def render(self, **kwargs) -> str:  # type: ignore[override]
        return f"<!--{self.data}-->"


class Pi(TerminalElement):
    """Represent processing instructions like `<?xml-stylesheet ?>`"""

    def render(self, **kwargs) -> str:  # type: ignore[override]
        return f"<?{self.data}>"


class Char(TerminalElement):
    """Represent character codes like: `&#0`"""

    def render(self, **kwargs) -> str:  # type: ignore[override]
        return f"&#{self.data};"


class Entity(TerminalElement):
    """Represent entities like `&amp`"""

    def render(self, **kwargs) -> str:  # type: ignore[override]
        return f"&{self.data};"


class Tree:
    """The engine class to generate the AST tree."""

    def __init__(self, name: str = ""):
        """Initialise Tree"""
        self.name = name
        self.outmost = Root(name)
        self.stack: deque = deque()
        self.stack.append(self.outmost)

    def clear(self):
        """Clear the outmost and stack for a new parsing."""
        self.outmost = Root(self.name)
        self.stack.clear()
        self.stack.append(self.outmost)

    def last(self) -> Element:
        """Return the last pointer which point to the actual tag scope."""
        return self.stack[-1]

    def nest_tag(self, name: str, attrs: dict):
        """Nest a given tag at the bottom of the tree using
        the last stack's pointer.
        """
        pointer = self.stack.pop()
        item = Tag(name, attrs)
        pointer.append(item)
        self.stack.append(pointer)
        self.stack.append(item)

    def nest_xtag(self, name: str, attrs: dict):
        """Nest an XTag onto the tree."""
        top = self.last()
        item = XTag(name, attrs)
        top.append(item)

    def nest_vtag(self, name: str, attrs: dict):
        """Nest a VoidTag onto the tree."""
        top = self.last()
        item = VoidTag(name, attrs)
        top.append(item)

    def nest_terminal(self, klass: type[TerminalElement], data: str):
        """Nest the data onto the tree."""
        top = self.last()
        item = klass(data)
        top.append(item)

    def enclose(self, name: str):
        """When a closing tag is found, pop the pointer's scope from the stack,
        to then point to the earlier scope's tag.
        """
        count = 0
        for ind in reversed(self.stack):
            count = count + 1
            if ind.name == name:
                break
        else:
            count = 0

        # It pops all the items which do not match with the closing tag.
        for _ in range(count):
            self.stack.pop()


class HtmlToAst(HTMLParser):
    """The tokenizer class."""

    # see https://html.spec.whatwg.org/multipage/syntax.html#void-elements
    void_elements = {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "param",
        "source",
        "track",
        "wbr",
    }

    def __init__(self, name: str = "", convert_charrefs: bool = False):
        super().__init__(convert_charrefs=convert_charrefs)
        self.struct = Tree(name)

    def feed(self, source: str) -> Root:  # type: ignore[override]
        """Parse the source string."""
        self.struct.clear()
        super().feed(source)
        return self.struct.outmost

    def handle_starttag(self, name: str, attr):
        """When found an opening tag then nest it onto the tree."""
        if name in self.void_elements:
            self.struct.nest_vtag(name, attr)
        else:
            self.struct.nest_tag(name, attr)

    def handle_startendtag(self, name: str, attr):
        """When found a XHTML tag style then nest it up to the tree."""
        self.struct.nest_xtag(name, attr)

    def handle_endtag(self, name: str):
        """When found a closing tag then makes it point to the right scope."""
        if name not in self.void_elements:
            self.struct.enclose(name)

    def handle_data(self, data: str):
        """Nest data onto the tree."""
        self.struct.nest_terminal(Data, data)

    def handle_decl(self, decl: str):
        self.struct.nest_terminal(Declaration, decl)

    def unknown_decl(self, decl: str):
        self.struct.nest_terminal(Declaration, decl)

    def handle_charref(self, data: str):
        self.struct.nest_terminal(Char, data)

    def handle_entityref(self, data: str):
        self.struct.nest_terminal(Entity, data)

    def handle_pi(self, data: str):
        self.struct.nest_terminal(Pi, data)

    def handle_comment(self, data: str):
        self.struct.nest_terminal(Comment, data)


def tokenize_html(text: str, name: str = "", convert_charrefs: bool = False) -> Root:
    parser = HtmlToAst(name, convert_charrefs=convert_charrefs)
    return parser.feed(text)
