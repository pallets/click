"""Conversion of Markdown-it tokens to docutils AST.

These renderers take the markdown-it parsed token stream
and convert it to the docutils AST.
The sphinx renderer is a subclass of the docutils one,
with some additional methods only available
*via* sphinx e.g. multi-document cross-referencing.
"""
