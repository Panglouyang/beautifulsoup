# Milestone 2

This work extends the **Beautiful Soup 4.13.0 source supplied in Canvas**.
All source locations below refer to the unmodified archive, preserved in
Git as `canvas-original`, rather than to an independently installed package.

## Setup and commands

The course specifies Python 3.10. From the `beautifulsoup` repository root:

```bash
python -m venv .venv
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -e .
python -m pip install pytest lxml html5lib
python apps/m2/task2.py apps/m2/sample.html
python apps/m2/task3.py apps/m2/sample.html
python apps/m2/task4.py apps/m2/sample.html
python apps/m2/task6.py apps/m2/sample.html --output replaced.html
python -m pytest bs4/tests/test_replacer.py -q
python -m pytest -q
python apps/m2/benchmark.py
```

Each application takes a filename. HTML defaults to `html.parser`; `.xml`
defaults to `xml` (requires lxml). Use `--parser lxml`, `--parser xml`, or
`--parser html.parser` to override this. `_common.py` ensures that direct
script execution imports this repository's modified `bs4`. Output goes to
stdout and timing goes to stderr; task6 saves a file and refuses to overwrite
the input. Its default output is `<input-stem>.task6.blockquote<extension>`.

## Part 1: SoupStrainer applications

| File | Parse-time filter | Output |
| --- | --- | --- |
| `task2.py` | `SoupStrainer("a")` | All anchor tags, including anchors without href |
| `task3.py` | `SoupStrainer(True)` | Every tag in document order |
| `task4.py` | `SoupStrainer(id=True)` | Tags possessing an id, including `id=""` |

The instructions say "two" applications but explicitly request three
filenames; all three are provided. Printing a tag includes its subtree,
as in Milestone 1. A selected parent retains its descendants, even when
those descendants do not match the strainer. The application therefore
uses `soup.find_all(strainer)` to restrict the printed results, too.

Task 3 cannot save tree memory by filtering: every tag is requested, so
every tag must be retained. SoupStrainer is a tree-construction filter,
not a streaming parser. BeautifulSoup still reads the input into memory
and the underlying parser must scan the complete markup. Retaining a
large selected subtree may also eliminate most of the expected savings.
html5lib does not support parse_only, so it is not offered by these apps.

### Large-file experiment

`benchmark.py` reproducibly generates a 12,748,002-byte HTML document
(12.16 MiB), containing 20,000 sections and 60,202 total tags. It includes
200 anchors with ids, spread throughout the document. The temporary file
is removed automatically. All four applications were executed against it;
task6's output was checked for exactly 20,000 blockquotes and no b tags.

Measured on Windows, Python 3.12.14, with `html.parser`:

| Construction | Parse seconds with tracemalloc | Peak traced Python MiB | Retained tags |
| --- | ---: | ---: | ---: |
| Full parse, no filter | 10.082 | 84.62 | 60,202 |
| Anchors only (task2) | 6.453 | 36.40 | 200 |
| All tags (task3) | 10.239 | 84.59 | 60,202 |
| Id-bearing tags (task4) | 7.114 | 36.39 | 200 |

These are traced Python allocations, not total process RSS; native parser
allocations are not measured. Tracing adds substantial timing overhead.
Separate application runs without tracemalloc produced:

| Application | Parse seconds | Total seconds, including output |
| --- | ---: | ---: |
| task2 | 1.100 | 1.107 |
| task3 | 2.504 | 7.556 |
| task4 | 1.208 | 1.215 |
| task6 | 2.326 | 3.457 |

Printing output was redirected to the null device during this test.
Input generation and Python startup are excluded from these times.
Results depend on the machine and runtime. Milestone 2 asks for a large
input; it does not repeat Milestone 1's separate GB-scale requirement.

## Part 2: original API source locations

The inventory is based on the eight actual Milestone 1 programs and the
three Part 1 programs. Line numbers are 1-based definition lines in the
original Canvas archive, **before any changes**. Inherited methods are
listed at their defining class, rather than at `BeautifulSoup`.

| Used API / operation | Original file | Original line | Used by |
| --- | --- | ---: | --- |
| `BeautifulSoup.__init__` | `bs4/__init__.py` | 209 | All M1 and M2 applications |
| `Tag.prettify` | `bs4/element.py` | 2601 | M1 task1 |
| `Tag.find_all` | `bs4/element.py` | 2715 | M1 task2/3/4/6/7; M2 task2/3/4 |
| `Tag.find` | `bs4/element.py` | 2684 | M1 task5 |
| `PageElement.find_parent` | `bs4/element.py` | 992 | M1 task5 |
| `Tag.__setitem__` (`tag["class"] = "test"`) | `bs4/element.py` | 2223 | M1 task7 |
| `Tag.select` | `bs4/element.py` | 2799 | M1 task8 |
| `SoupStrainer.__init__` | `bs4/filter.py` | 345 | M2 task2/3/4 |
| `Tag.__repr__` (also `__str__`) | `bs4/element.py` | 2298 | Printing tags; M1 task6/7 `str(soup)` |
| `Tag.__str__` alias assignment | `bs4/element.py` | 2302 | Same string conversions |
| `Tag.decode` | `bs4/element.py` | 2334 | Tag serialization through print/prettify |
| `BeautifulSoup.decode` override | `bs4/__init__.py` | 1073 | Whole-document serialization |

`tag.name = "blockquote"` in M1 task6 sets an ordinary instance attribute;
there is no `Tag.name` setter function. Its original initialization is in
`Tag.__init__` at `bs4/element.py:1618`, with `self.name = name` at line 1648.
The `name` property elsewhere in that file belongs to `NavigableString`,
not Tag. M1 also imports/catches `FeatureNotFound`, an exception class at
`bs4/exceptions.py:11`, not an API function. File I/O, argparse, pathlib,
timers, and print are Python APIs and have no definitions in bs4.

`Tag.select` delegates to `CSS.select`, defined at `bs4/css.py:161`;
the latter delegates selector matching to the external SoupSieve package.

To inspect an original definition without confusing it with modified lines:

```bash
git show canvas-original:bs4/__init__.py
git show canvas-original:bs4/element.py
git show canvas-original:bs4/filter.py
```

## Part 3: SoupReplacer

```python
from bs4 import BeautifulSoup, SoupReplacer

rule = SoupReplacer("b", "blockquote")
soup = BeautifulSoup("<p><b>Hello</b>!</p>", "html.parser", replacer=rule)
print(soup.prettify())
```

`SoupReplacer(og_tag, alt_tag)` is implemented in `bs4/replacer.py` and
exported from `bs4`. Both names must be nonempty strings without whitespace
or markup delimiters. XML rules use local names and preserve namespace
prefixes. Comparison uses the parser-normalized name: HTML names are
lowercased by the parser; XML names are case-sensitive. A rule can be reused.

The optional constructor argument is appended after the existing explicit
parameters so their positional meanings remain unchanged. Existing calls
without a replacer retain their behavior.

Replacement occurs in `BeautifulSoup.popTag`, after the parser has matched
the original closing name and updated its original-name counters and stacks.
This preserves correct nesting for `<b>outer<b>inner</b>tail</b><p>after</p>`.
Renaming immediately at a start tag without preserving its original name
would prevent the corresponding `</b>` from matching the open tag.
Unclosed tags are renamed when `_feed` closes them at end of input.

Each closed node gets one constant-time rule check. The new work is O(T)
for T constructed tags, with O(1) extra per-rule storage and no extra
full-tree traversal or collection of nodes. It changes the existing node's
name and preserves its attributes, contents, and identity. This is a
structural rename, equivalent to M1's rename loop; it does not reparse the
document under the destination tag's HTML content model.

`parse_only` filters original names before replacement. Supported builders
are `html.parser`, `lxml`, and `xml`/`lxml-xml`. html5lib bypasses the tag
stack callback; using it with a replacer raises `NotImplementedError`
explicitly. Supporting its different construction API is outside this change.

The Part 3 introduction mentions tasks 5 and 7, but the required constructor,
example, and final application requirement specify renaming tags (M1 task6).
This submission implements that specified API; the attribute-transformer API
belongs to Milestone 3 and is not introduced early.

### Two new test cases

`bs4/tests/test_replacer.py` contains two test functions:

1. `test_replacement_preserves_tree`: compares the new result to the M1
   post-parse rename loop, checking nested tags, attributes, text, following
   siblings, and unfinished input. Parameterization covers html.parser,
   lxml HTML, and XML (six executions).
2. `test_replacement_happens_before_builder_finishes`: a custom builder
   checks the renamed node before its `feed()` returns, proving that the
   rule executes during parsing. Also checks original-name SoupStrainer
   filtering and reuse of a rule (one execution).

All **7 new test executions passed**. Full-suite result on the available
Python 3.12.14 runtime: **833 passed, 7 skipped, 3 failed**. The three failures
also occur in the unmodified Canvas source under the same runtime:

- `test_htmlparser.py::TestHTMLParserTreeBuilder::test_rejected_input`
- Both parameters of `test_fuzz.py::TestFuzz::test_rejected_markup`

Those tests expect the standard-library HTML parser to reject particular
malformed inputs; this runtime accepts them. The untouched source was
extracted separately and its relevant test modules rerun: 87 passed,
7 skipped, and the same 3 failures. No upstream tests were altered or
disabled. Python 3.10 (the course-required runtime) was unavailable locally,
so this report does not claim a Python 3.10 run.

## Local delivery and later GitHub submission

The repository has an original-source commit/tag (`canvas-original`) and
a separate Milestone 2 implementation commit/tag (`milestone-2`). GitHub
publication is deferred at the user's request. The local ZIP is a convenient
copy, but Canvas ultimately requires a repository tag/release link.
When ready, create a GitHub repository named **beautifulsoup**, add its URL
as origin, and publish:

```bash
git remote add origin https://github.com/YOUR-USERNAME/beautifulsoup.git
git push -u origin main
git push origin canvas-original milestone-2
```

Then submit `https://github.com/YOUR-USERNAME/beautifulsoup/releases/tag/milestone-2`
after creating the release, or the tag link
`https://github.com/YOUR-USERNAME/beautifulsoup/tree/milestone-2`.
The root README's old example using `beautiful.git` is a typo; the required
repository name is `beautifulsoup`.
