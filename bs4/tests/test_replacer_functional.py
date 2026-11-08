"""Milestone 3: six functional SoupReplacer test cases."""

import pytest

from bs4 import BeautifulSoup, SoupReplacer, SoupStrainer
from bs4.builder._htmlparser import HTMLParserTreeBuilder
from . import LXML_PRESENT


@pytest.mark.parametrize("parser", ["html.parser", "lxml", "xml"])
def test_name_transformer_preserves_nesting(parser):
    if parser != "html.parser" and not LXML_PRESENT:
        pytest.skip("lxml is not installed")
    markup = '<root><b id="a">one<b>two</b>tail</b><p>end</p></root>'
    expected = BeautifulSoup(markup, parser)
    for tag in expected.find_all("b"):
        tag.name = "blockquote"
    rule = SoupReplacer(name_xformer=lambda t: "blockquote" if t.name == "b" else t.name)
    assert str(BeautifulSoup(markup, parser, replacer=rule)) == str(expected)


def test_attrs_transformer_adds_and_replaces_class():
    rule = SoupReplacer(attrs_xformer=lambda t: dict(t.attrs, **{"class": "test"})
                        if t.name == "p" else t.attrs)
    soup = BeautifulSoup('<div class="keep"><p id="x" class="old">a</p><p>b</p></div>',
                         "html.parser", replacer=rule)
    assert [p["class"] for p in soup.find_all("p")] == ["test", "test"]
    assert soup.p["id"] == "x"
    assert soup.div["class"] == ["keep"]
    shared = {"id": "shared"}
    soup = BeautifulSoup('<p>a</p><p>b</p>', "html.parser",
                         replacer=SoupReplacer(attrs_xformer=lambda t: shared))
    soup.p["id"] = "changed"
    assert soup.find_all("p")[1]["id"] == shared["id"] == "shared"


def test_side_effect_transformer_removes_class():
    def remove_class(tag):
        tag.attrs.pop("class", None)

    soup = BeautifulSoup('<div class="a"><p class="b" id="x">text</p><br/></div>',
                         "html.parser", replacer=SoupReplacer(xformer=remove_class))
    assert all("class" not in t.attrs for t in soup.find_all(True))
    assert soup.p["id"] == "x"
    assert soup.p.string == "text"


def test_combined_transformers_and_m2_compatibility():
    seen = []

    def finish(tag):
        seen.append((tag.name, dict(tag.attrs)))
        tag["done"] = "yes"

    rule = SoupReplacer("b", "blockquote", name_xformer=lambda t: t.name.upper(),
                        attrs_xformer=lambda t: {"name": t.name}, xformer=finish)
    soup = BeautifulSoup('<b>x</b>', "html.parser", replacer=rule)
    assert str(soup) == '<BLOCKQUOTE done="yes" name="BLOCKQUOTE">x</BLOCKQUOTE>'
    assert seen == [("BLOCKQUOTE", {"name": "BLOCKQUOTE"})]
    assert str(BeautifulSoup('<b>x</b>', "html.parser", replacer=SoupReplacer())) == '<b>x</b>'


def test_callbacks_run_during_parsing_once_per_retained_tag():
    seen = []

    class ObservingBuilder(HTMLParserTreeBuilder):
        def feed(self, markup):
            super().feed(markup)
            assert seen == ["i", "b"]
            assert self.soup.b["visited"] == "yes"

    def visit(tag):
        seen.append(tag.name)
        tag["visited"] = "yes"

    rule = SoupReplacer(xformer=visit)
    soup = BeautifulSoup('<p>skip</p><b><i>x</i></b>', builder=ObservingBuilder(),
                         parse_only=SoupStrainer("b"), replacer=rule)
    assert soup.p is None
    seen.clear()
    soup = BeautifulSoup('<b><i>x', "html.parser", replacer=rule)
    assert seen == ["i", "b"]  # Includes tags closed at end of input.
    assert soup.i["visited"] == "yes"


def test_invalid_callbacks_results_and_exceptions():
    for keyword in ("name_xformer", "attrs_xformer", "xformer"):
        with pytest.raises(TypeError):
            SoupReplacer(**{keyword: 42})
    for name, error in ((None, TypeError), ("", ValueError), ("a b", ValueError)):
        with pytest.raises(error):
            BeautifulSoup('<p>x</p>', "html.parser",
                          replacer=SoupReplacer(name_xformer=lambda t: name))
    with pytest.raises(TypeError):
        BeautifulSoup('<p>x</p>', "html.parser",
                      replacer=SoupReplacer(attrs_xformer=lambda t: None))

    def fail(tag):
        raise RuntimeError("callback failed")

    with pytest.raises(RuntimeError, match="callback failed"):
        BeautifulSoup('<p>x</p>', "html.parser", replacer=SoupReplacer(xformer=fail))
