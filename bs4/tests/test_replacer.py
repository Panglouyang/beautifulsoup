"""Milestone 2: parse-time replacement and parser-stack regressions."""

import pytest

from bs4 import BeautifulSoup, SoupReplacer, SoupStrainer
from bs4.builder._htmlparser import HTMLParserTreeBuilder
from . import LXML_PRESENT


@pytest.mark.parametrize("parser", ["html.parser", "lxml", "xml"])
@pytest.mark.parametrize("markup", [
    '<root><b id="outer">one<b class="x">two</b>three</b><p>end</p></root>',
    '<root><b id="outer">one<b class="x">two</b>three<p>end</p>',
])
def test_replacement_preserves_tree(parser, markup):
    """Compare with a normal parse followed by the old M1 rename loop."""
    if parser != "html.parser" and not LXML_PRESENT:
        pytest.skip("lxml is not installed")
    expected = BeautifulSoup(markup, parser)
    for tag in expected.find_all("b"):
        tag.name = "blockquote"
    actual = BeautifulSoup(markup, parser, replacer=SoupReplacer("b", "blockquote"))
    assert str(actual) == str(expected)
    assert actual.find("b") is None
    assert actual.find("blockquote")["id"] == "outer"
    assert actual.find("p").string == "end"


def test_replacement_happens_before_builder_finishes():
    """Prove replacement occurs in feed(), including parse_only interaction."""
    class ObservingBuilder(HTMLParserTreeBuilder):
        def feed(self, markup):
            super().feed(markup)
            # This runs before BeautifulSoup._feed returns, ruling out a
            # constructor-level postprocessing traversal.
            assert self.soup.find("blockquote").string == "keep"
            assert self.soup.find("b") is None

    rule = SoupReplacer("b", "blockquote")
    soup = BeautifulSoup(
        '<div>discard</div><b id="kept">keep</b><p>discard</p>',
        builder=ObservingBuilder(),
        parse_only=SoupStrainer("b"),
        replacer=rule,
    )
    assert str(soup) == '<blockquote id="kept">keep</blockquote>'
    assert str(BeautifulSoup("<b>again</b>", "html.parser", replacer=rule)) == (
        "<blockquote>again</blockquote>"
    )
