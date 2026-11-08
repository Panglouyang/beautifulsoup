"""Small, reusable parse-time tag replacement rules."""

from collections.abc import Mapping
from typing import Callable, Optional

from .element import Tag


class SoupReplacer:
    """Transform each tag as it closes during parsing.

    Names are compared exactly as normalized by the selected parser. XML
    names are case-sensitive; an XML namespace prefix is preserved.
    The optional M2 name pair runs first, followed by ``name_xformer``,
    ``attrs_xformer``, and ``xformer``. Each callback receives the same Tag.
    Name and attribute callbacks return replacements; the final callback
    mutates the tag and its return value is ignored. Children have already
    been processed, but the parent may still be incomplete.
    """

    def __init__(
        self,
        og_tag: Optional[str] = None,
        alt_tag: Optional[str] = None,
        *,
        name_xformer: Optional[Callable[[Tag], str]] = None,
        attrs_xformer: Optional[Callable[[Tag], Mapping]] = None,
        xformer: Optional[Callable[[Tag], None]] = None,
    ):
        if og_tag is not None or alt_tag is not None:
            self._validate_name(og_tag)
            self._validate_name(alt_tag)
        for callback in (name_xformer, attrs_xformer, xformer):
            if callback is not None and not callable(callback):
                raise TypeError("Transformers must be callable or None.")
        self.og_tag = og_tag
        self.alt_tag = alt_tag
        self.name_xformer = name_xformer
        self.attrs_xformer = attrs_xformer
        self.xformer = xformer

    @staticmethod
    def _validate_name(name: str) -> None:
        if not isinstance(name, str):
            raise TypeError("Tag names must be strings.")
        if not name or any(c.isspace() or c in "<>/=:" for c in name):
            raise ValueError("Use a nonempty local tag name without markup or whitespace.")

    def replace(self, tag: Tag) -> None:
        """Apply this rule to a single node, without traversing its children."""
        if self.og_tag is not None and tag.name == self.og_tag:
            tag.name = self.alt_tag
        if self.name_xformer is not None:
            name = self.name_xformer(tag)
            self._validate_name(name)
            tag.name = name
        if self.attrs_xformer is not None:
            attrs = self.attrs_xformer(tag)
            if not isinstance(attrs, Mapping):
                raise TypeError("attrs_xformer must return an attribute mapping.")
            # Copy so a callback may safely return a reused mapping.
            tag.attrs = type(tag.attrs)(attrs)
        if self.xformer is not None:
            self.xformer(tag)
