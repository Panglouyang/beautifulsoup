"""Small, reusable parse-time tag replacement rules."""

from .element import Tag


class SoupReplacer:
    """Rename every parsed ``og_tag`` to ``alt_tag``.

    Names are compared exactly as normalized by the selected parser. XML
    names are case-sensitive; an XML namespace prefix is preserved.
    Attributes, contents, and node identity are preserved.
    """

    def __init__(self, og_tag: str, alt_tag: str):
        for name in (og_tag, alt_tag):
            if not isinstance(name, str):
                raise TypeError("Tag names must be strings.")
            if not name or any(c.isspace() or c in "<>/=:" for c in name):
                raise ValueError("Use a nonempty local tag name without markup or whitespace.")
        self.og_tag = og_tag
        self.alt_tag = alt_tag

    def replace(self, tag: Tag) -> None:
        """Apply this rule to a single node, without traversing its children."""
        if tag.name == self.og_tag:
            tag.name = self.alt_tag
