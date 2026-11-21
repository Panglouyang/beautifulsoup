"""Milestone 4: iterating over a BeautifulSoup object visits every node."""

import inspect
import types

import pytest

from bs4 import BeautifulSoup, SoupReplacer, SoupStrainer
from bs4.element import (
    Comment,
    Doctype,
    NavigableString,
    ProcessingInstruction,
    Tag,
)
from . import LXML_PRESENT


def describe(node):
    """A comparable (type, name-or-text) pair for a node."""
    if isinstance(node, Tag):
        return ("tag", node.name)
    return (type(node).__name__, str(node))


def test_iterates_every_tag_and_string_in_document_order():
    markup = "<html><body><p>one <b>two</b></p><p>three</p></body></html>"
    soup = BeautifulSoup(markup, "html.parser")

    assert [describe(n) for n in soup] == [
        ("tag", "html"),
        ("tag", "body"),
        ("tag", "p"),
        ("NavigableString", "one "),
        ("tag", "b"),
        ("NavigableString", "two"),
        ("tag", "p"),
        ("NavigableString", "three"),
    ]
    # Same nodes (by identity) as the existing descendants generator;
    # the soup object itself is not produced.
    nodes = [n for n in soup]
    assert all(a is b for a, b in zip(nodes, soup.descendants))
    assert len(nodes) == len(list(soup.descendants))
    assert soup not in nodes


def test_iterates_special_string_types_in_html():
    markup = "<!DOCTYPE html><html><!-- note --><p>text</p></html>"
    soup = BeautifulSoup(markup, "html.parser")

    types_seen = [type(n) for n in soup]
    assert types_seen == [Doctype, Tag, Comment, Tag, NavigableString]
    assert [str(n) for n in soup if isinstance(n, Comment)] == [" note "]


@pytest.mark.skipif(not LXML_PRESENT, reason="lxml is not installed")
def test_iterates_xml_nodes_including_comments_and_processing_instructions():
    markup = (
        '<?xml version="1.0"?><root><?app run?>'
        "<item><!-- c --></item><item>plain</item></root>"
    )
    soup = BeautifulSoup(markup, "xml")

    kinds = []
    for node in soup:
        if isinstance(node, Tag):
            kinds.append(("tag", node.name))
        elif isinstance(node, ProcessingInstruction):
            kinds.append(("pi", str(node)))
        elif isinstance(node, Comment):
            kinds.append(("comment", str(node)))
        elif isinstance(node, NavigableString):
            kinds.append(("text", str(node)))
    assert kinds == [
        ("tag", "root"),
        ("pi", "app run"),
        ("tag", "item"),
        ("comment", " c "),
        ("tag", "item"),
        ("text", "plain"),
    ]


def test_iteration_is_lazy_and_does_not_collect_nodes():
    depth = 3000
    soup = BeautifulSoup("<div>" * depth + "leaf" + "</div>" * depth, "html.parser")

    it = iter(soup)
    assert isinstance(it, types.GeneratorType)
    first = next(it)
    assert first.name == "div"
    # The suspended generator holds only node references, not a
    # collection of nodes.
    for value in inspect.getgeneratorlocals(it).values():
        assert not isinstance(value, (list, tuple, set, dict))

    # Nodes added after iteration started are still seen, which would
    # not happen if the nodes had been copied into a list up front.
    soup.append(soup.new_tag("footer"))
    rest = list(it)
    assert len(rest) == (depth - 1) + 2  # remaining divs, "leaf", footer
    assert rest[-2] == "leaf"
    assert rest[-1].name == "footer"

    # Each iter() call is independent, so nested loops work, and an
    # empty document produces nothing.
    small = BeautifulSoup("<a>x</a><a>y</a>", "html.parser")
    assert sum(1 for _ in small for _ in small) == 16
    assert list(BeautifulSoup("", "html.parser")) == []


def test_mutation_during_iteration_and_existing_apis():
    # Removing the node just produced skips its subtree and continues.
    soup = BeautifulSoup("<div><b>x</b><i>y</i></div><p>z</p>", "html.parser")
    seen = []
    for node in soup:
        seen.append(describe(node))
        if isinstance(node, Tag) and node.name == "b":
            node.decompose()
    assert seen == [
        ("tag", "div"),
        ("tag", "b"),
        ("tag", "i"),
        ("NavigableString", "y"),
        ("tag", "p"),
        ("NavigableString", "z"),
    ]
    assert str(soup) == "<div><i>y</i></div><p>z</p>"

    # Children added to the node just produced are visited.
    soup = BeautifulSoup("<ul><li></li></ul>", "html.parser")
    names = []
    for node in soup:
        names.append(describe(node))
        if isinstance(node, Tag) and node.name == "li":
            node.append("added")
    assert names[-1] == ("NavigableString", "added")

    # Iterating a plain Tag keeps its original meaning (direct children),
    # and len()/in on the soup still refer to direct children.
    soup = BeautifulSoup("<div><p>a</p><p>b</p></div>", "html.parser")
    assert [c.name for c in soup.div] == ["p", "p"]
    assert len(soup) == 1 and soup.div in soup and soup.p not in soup

    # Parse-time APIs from Milestones 2 and 3 compose with iteration.
    rule = SoupReplacer("b", "blockquote")
    replaced = BeautifulSoup("<p><b>hi</b></p>", "html.parser", replacer=rule)
    assert [describe(n) for n in replaced] == [
        ("tag", "p"),
        ("tag", "blockquote"),
        ("NavigableString", "hi"),
    ]
    strained = BeautifulSoup(
        '<p><a href="/1">one</a></p><a href="/2">two</a>',
        "html.parser",
        parse_only=SoupStrainer("a"),
    )
    assert [n["href"] for n in strained if isinstance(n, Tag)] == ["/1", "/2"]
