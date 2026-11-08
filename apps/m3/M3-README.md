# Milestone 3: functional SoupReplacer

## Recommendation to the team

Keep M2's `SoupReplacer("b", "blockquote")` as a convenient shorthand and
extend the same class with optional, keyword-only transformation functions.
M2 is easy to learn and validate, but expresses only one unconditional name
replacement. M3 lets callers express conditional renaming, attribute changes,
and custom mutations without adding a separate library method for every rule.
It is a higher-order API: users supply behavior as functions and the library
controls when that behavior runs.

Prefer `name_xformer` and `attrs_xformer` for ordinary transformations: their
return values make intent clear and are straightforward to test. Reserve
`xformer` for mutations that need the full Tag API. That flexibility also
creates risks: callbacks can raise exceptions, perform expensive work, or
depend on partially built ancestors. Document these constraints rather than
silently swallowing errors. Avoid allowing callbacks to detach, reparent, or
rename still-open ancestor nodes; doing so can invalidate parser state.

## Interface and execution contract

```python
from bs4 import BeautifulSoup, SoupReplacer

rule = SoupReplacer(
    name_xformer=lambda t: "blockquote" if t.name == "b" else t.name,
    attrs_xformer=lambda t: {k: v for k, v in t.attrs.items() if k != "class"},
)
soup = BeautifulSoup('<p class="old"><b>Hello</b></p>',
                     "html.parser", replacer=rule)
print(soup)  # <p><blockquote>Hello</blockquote></p>

def remove_class_attr(tag):
    tag.attrs.pop("class", None)

class_deleter = SoupReplacer(xformer=remove_class_attr)
```

- The original positional name pair remains compatible. If used, both names
  must be supplied. All three new callback arguments are optional keywords;
  `SoupReplacer()` does nothing.
- Each retained tag receives the original name-pair rule, then
  `name_xformer`, then `attrs_xformer`, then `xformer`, in that order.
  Later callbacks see earlier changes on the same Tag object.
- `name_xformer(tag)` returns a nonempty local name without whitespace or
  markup delimiters. XML namespace prefixes are preserved.
- `attrs_xformer(tag)` returns a mapping replacing the entire attribute
  dictionary. Return `tag.attrs` to retain it, or merge it to preserve other
  attributes. The dictionary is shallow-copied using its existing type;
  values follow ordinary programmatic attribute assignment (a class string
  is not reparsed into a list). Nested mutable values are not deep-copied.
- `xformer(tag)` mutates the tag and normally returns `None`; its return
  value is ignored. Callback exceptions propagate to the caller. Noncallable
  arguments and invalid name/attribute return values raise explicit errors.

The existing `BeautifulSoup.popTag` hook invokes `replace` after matching
the original closing name and updating parser stacks. Each node is processed
once as it closes, including unfinished tags closed at end of input.
Children are already transformed; ancestors may be incomplete. The document
root itself is excluded. There is no second traversal of the completed tree.
`parse_only` filters original names before transformations and callbacks run
only on retained nodes. Supported builders remain `html.parser`, `lxml`, and
`xml`/`lxml-xml`; `html5lib` remains explicitly unsupported, as in M2.

Renaming changes the existing node; it does not reparse its contents under a
different HTML content model. A rule can be reused, although stateful
callbacks are responsible for managing their own state. Library overhead is
O(T + A), for T retained tags and A copied attribute entries, plus the cost
of user callbacks. Copying a returned mapping requires space proportional to
that mapping; no additional collection of tree nodes is built.

## Application: M1 task 7 during parsing

From the repository root, using Python 3.10 with the setup in the root README:

```bash
python apps/m3/task7.py apps/m3/sample.html --output result.html
python apps/m3/task7.py input.xml --parser xml --output result.xml
python -m pytest -q bs4/tests/test_replacer_functional.py
python -m pytest -q
```

`task7.py` adds or replaces `class="test"` on every `p` using
`attrs_xformer`, preserves other attributes and non-p tags, and writes UTF-8
output. It defaults to `html.parser` for HTML and `xml` for `.xml` files.
The default output is `<input-stem>.task7<suffix>`; input/output paths must
differ. The application does not traverse the tree to perform the change.

## Validation

Six new test functions in `bs4/tests/test_replacer_functional.py` cover name
replacement across three builders, attribute additions/replacements and
mapping independence, side-effect deletion, combined callback ordering and M2
compatibility, execution during parsing (including `parse_only`, rule reuse,
and unfinished tags), and argument/result validation plus exception behavior.
Parameterization produces eight new test executions.

- Python 3.10: **844 passed, 7 skipped** for the full suite.
- Existing M2 and new M3 replacer tests: **15 passed**.
- HTML/XML task7 command-line output matches the original M1 post-parse
  assignment, including Unicode, existing/missing classes, and other attrs.
- Python 3.12: 841 passed, 7 skipped, 3 failed. The same three failures in
  `TestFuzz.test_rejected_markup` (two inputs) and
  `TestHTMLParserTreeBuilder.test_rejected_input` reproduce on unchanged
  `milestone-2-v2` (833 passed, 7 skipped, 3 failed). Both versions pass these
  tests under the course's Python 3.10; M3 introduces no additional failures.

Submission tag: `milestone-3`, in the same repository used for M2.
