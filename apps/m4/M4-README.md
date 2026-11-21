# Milestone 4: iterable BeautifulSoup

## What changed

`BeautifulSoup` objects are now iterable over **every node in the tree**:

```python
from bs4 import BeautifulSoup

soup = BeautifulSoup(html_doc, "html.parser")
for node in soup:
    print(node)
```

`soup` is still the ordinary object returned by the `BeautifulSoup`
constructor. The only library change is a new `BeautifulSoup.__iter__`
generator in `bs4/__init__.py`. It is roughly 20 lines, plus a docstring.

## Iteration contract

- **Order:** document order, as a pre-order depth-first walk. A `Tag` comes
  before its children, and its children come before its next sibling. This
  is the same order as `soup.descendants`, `find_all()` and the parser's
  `next_element` chain.
- **What is produced:** every `PageElement` under the soup. That covers
  `Tag` objects and every `NavigableString` subclass: text, `Comment`,
  `Doctype`, `CData`, `ProcessingInstruction` and so on. The
  `BeautifulSoup` object itself is not produced, because it is the
  container, not a document node.
- **Laziness:** each `iter(soup)` returns a fresh generator. Nodes are
  produced one at a time, and nested loops or several concurrent
  iterators do not interfere with each other.
- **Unchanged semantics:** `Tag.__iter__` still yields only direct
  children. The new behaviour applies only to the soup (the document).
  `len(soup)` and `x in soup` keep their `Tag` meaning, which is direct
  children. `soup.contents` and `soup.children` remain available for
  top-level access.

## Implementation: no list, no stack

The project rule is not to collect the nodes into a list. The generator
also avoids an explicit stack and avoids recursion. It moves through
pointers that every node already stores:

```
start at soup.contents[0]
loop:
    remember node.parent and node.next_sibling
    yield node
    if node is still in place and is a Tag with children: go to contents[0]
    else go to the next sibling; if there is none, climb through the
         remembered parents until one has a next sibling, stopping at the soup
```

- **Memory:** O(1) beyond the generator frame, which holds a handful of
  node references. The usage stays the same for a 10-node file or a
  10-million-node file, and for a flat file or one nested 3,000 levels
  deep. A recursive generator would need O(depth) frames and would hit
  Python's recursion limit on deeply nested documents. An explicit stack
  would need O(depth) memory.
- **Time:** O(1) amortized per node. Each parent-to-child edge is
  descended once and climbed once.
- **Reuse:** the walk uses only links that the tree builder already keeps
  (`contents`, `next_sibling`, `parent`). The parser and the node classes
  needed no changes.

### Why not `return self.descendants`?

`Tag.descendants` is also lazy, and it was my first implementation, but it
follows the `next_element` chain. It reads the successor *before* yielding
the current node. As a result, the most common pattern of editing while
iterating breaks:

```python
for node in soup:
    if isinstance(node, Tag) and node.name == "script":
        node.decompose()
```

With `descendants`, the remembered successor is the script's first child,
which `decompose()` has just destroyed. The loop then crashes with
`AttributeError`. With `extract()` it stops early instead, because the
extracted subtree's chain ends in `None`. The new walker chooses its next
step only *after* the loop body returns. The guarantees are:

- If the node just produced is extracted, decomposed or moved, its subtree
  is skipped and the walk continues from the node's old position.
- If children are added to the node just produced, they are visited.
- If nodes are added later in the document, they are visited, because no
  snapshot was taken.
- If a node is replaced with `replace_with`, the replacement is **not**
  visited, since the walk continues after the old position. Other large
  restructurings during iteration, such as editing ancestors or nodes
  already visited, are not supported. This matches the usual Python rule
  for changing a container while iterating over it.

The price is speed. The extra checks make a full walk about 2× slower than
`descendants`, though still fast in absolute terms (see below). I think
editing during a walk is common enough in BeautifulSoup code that being
safe is worth that cost.

## Tests

`bs4/tests/test_soup_iteration.py` has 5 new unit tests. All 5 fail on the
`milestone-3` code and pass with this change:

1. **Document order:** tags and strings appear in pre-order. The nodes are
   the same objects as `soup.descendants`, and the soup is not included.
2. **HTML special strings:** `Doctype`, `Comment`, `Tag` and
   `NavigableString` are all produced, each with its correct type.
3. **XML nodes (lxml-xml):** tags, `ProcessingInstruction`, `Comment` and
   text appear in order.
4. **Laziness and no collection:** `iter(soup)` is a generator, and its
   suspended frame holds no list, tuple, set or dict. A document nested
   3,000 levels deep is walked without recursion. A node appended after
   iteration started is still visited, which proves there was no up-front
   snapshot. Nested and independent iterators work, and an empty document
   produces nothing.
5. **Editing while iterating, plus compatibility:** decomposing the
   current node skips its subtree, and a child added to the current node
   is visited. Plain `Tag` iteration, `len(soup)` and `in` are unchanged.
   Iteration also works on trees built with M2/M3 `SoupReplacer` and with
   `SoupStrainer`.

## Application

```bash
python apps/m4/node_stats.py apps/m4/sample.html --print
python apps/m4/node_stats.py big.xml --parser xml
```

`node_stats.py` parses a file, walks it with `for node in soup`, and
reports node counts by type and the most common tags. With `--print` it
also shows one line per node.

## Validation

- Python 3.10 full suite: **846 passed, 7 skipped, 3 failed**. Before
  this change it was 841 passed, with the same 3 failures. The +5 are the
  new tests. The 3 failures (`TestFuzz.test_rejected_markup` ×2 and
  `TestHTMLParserTreeBuilder.test_rejected_input`) come from the newer
  CPython 3.10.x `html.parser` and reproduce on unchanged `milestone-3`.
  M4 adds no failures.
- Benchmark on a generated 9.9 MB HTML file (800,003 nodes, lxml), with
  extra memory measured by `tracemalloc` during the walk:

  | Walk                | Time   | Peak extra memory |
  |---------------------|--------|-------------------|
  | `for node in soup`  | 0.19 s | 1.9 KiB           |
  | `soup.descendants`  | 0.09 s | 1.8 KiB           |
  | `list(descendants)` | 0.10 s | 6.5 MB            |

  Iterating the soup uses constant memory. Collecting the nodes into a
  list costs memory that grows with document size.
