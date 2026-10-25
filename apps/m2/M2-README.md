# Milestone 2

Based on the original Canvas Beautiful Soup 4.13.0 source.

## Run

Use Python 3.10 as required by the course. From the repository root:

```bash
python -m pip install -e .
python -m pip install pytest lxml
python apps/m2/task2.py apps/m2/sample.html
python apps/m2/task3.py apps/m2/sample.html
python apps/m2/task4.py apps/m2/sample.html
python apps/m2/task6.py apps/m2/sample.html --output replaced.html
python -m pytest bs4/tests/test_replacer.py -q
python apps/m2/benchmark.py
```

Replace the sample path with any HTML/XML file. HTML uses `html.parser`;
XML uses `xml` (lxml). Task6 saves the modified document.

## Part 1: SoupStrainer

- `task2.py`: print anchors using `SoupStrainer("a")`.
- `task3.py`: print all tags using `SoupStrainer(True)`.
- `task4.py`: print tags with an id using `SoupStrainer(id=True)`.

Task3 cannot reduce tree memory because it must retain every tag.
Selected parents retain their descendants, so results are filtered again
before printing.

All applications passed on a generated 12,748,002-byte HTML file.
Measurements on Windows, Python 3.12.14, using `html.parser`:

| Application | Parse seconds | Total seconds |
| --- | ---: | ---: |
| task2 | 1.100 | 1.107 |
| task3 | 2.504 | 7.556 |
| task4 | 1.208 | 1.215 |
| task6 | 2.326 | 3.457 |

The full document has 60,202 tags; task2 and task4 each retain 200.
`benchmark.py` generates the input and runs all four applications.

## Part 2: Original API locations

These are 1-based line numbers in the **unmodified Canvas source**.

| API / operation | Original file | Line |
| --- | --- | ---: |
| `BeautifulSoup.__init__` | `bs4/__init__.py` | 209 |
| `Tag.prettify` | `bs4/element.py` | 2601 |
| `Tag.find_all` | `bs4/element.py` | 2715 |
| `Tag.find` | `bs4/element.py` | 2684 |
| `PageElement.find_parent` | `bs4/element.py` | 992 |
| `Tag.__setitem__` (`tag["class"] = "test"`) | `bs4/element.py` | 2223 |
| `Tag.select` | `bs4/element.py` | 2799 |
| `SoupStrainer.__init__` | `bs4/filter.py` | 345 |
| `Tag.__repr__` (printing / string conversion) | `bs4/element.py` | 2298 |
| `Tag.__str__` alias | `bs4/element.py` | 2302 |
| `Tag.decode` | `bs4/element.py` | 2334 |
| `BeautifulSoup.decode` | `bs4/__init__.py` | 1073 |

`tag.name` is an ordinary attribute, initialized at `bs4/element.py:1648`
inside `Tag.__init__` (line 1618); it has no setter method.
`FeatureNotFound` is an exception class at `bs4/exceptions.py:11`.
`Tag.select` delegates to `CSS.select` at `bs4/css.py:161`.

## Part 3: SoupReplacer

`bs4/replacer.py` adds `SoupReplacer(og_tag, alt_tag)`.
`bs4/__init__.py` exports it and accepts an optional `replacer` argument:

```python
from bs4 import BeautifulSoup, SoupReplacer
soup = BeautifulSoup("<b>Hello</b>", "html.parser",
                     replacer=SoupReplacer("b", "blockquote"))
print(soup.prettify())
```

Tags are renamed in `popTag()` during parsing, after the original closing
name is matched. This preserves nesting without a second tree traversal.
Attributes and contents are preserved. `parse_only` matches original names.
Supported parsers: html.parser and lxml (HTML/XML); html5lib is unsupported.

`bs4/tests/test_replacer.py` adds two test functions: tree preservation
(across three parsers and two inputs) and replacement before parsing
finishes. All 7 executions passed. Full suite on Python 3.12.14:
833 passed, 7 skipped, 3 failed. The same 3 malformed-input tests fail in
the untouched Canvas source. Python 3.10 was unavailable for local testing.
