# BeautifulSoup

HTML/XML parsing library, extended for the course project using the Canvas source.

## Setup and tests

Use Python 3.10. Run from the repository root:

```bash
conda create -n bs4 python=3.10
conda activate bs4
python -m pip install -e .
python -m pip install pytest lxml
python -m pytest
```

## Example

```python
from bs4 import BeautifulSoup, SoupReplacer

soup = BeautifulSoup("<b>Hello</b>", "html.parser",
                     replacer=SoupReplacer("b", "blockquote"))
print(soup.prettify())
```

## Milestone 2

- API implementation: `bs4/`
- New tests: `bs4/tests/test_replacer.py`
- Applications and report: [apps/m2/M2-README.md](apps/m2/M2-README.md)
- Submission: [Milestone 2 release](https://github.com/Panglouyang/beautifulsoup/releases/tag/milestone-2-v2)

## Milestone 3

- Functional API: `bs4/replacer.py`
- Six new test cases: `bs4/tests/test_replacer_functional.py`
- Task 7 application and technical brief: [apps/m3/M3-README.md](apps/m3/M3-README.md)
- Submission: [Milestone 3 release](https://github.com/Panglouyang/beautifulsoup/releases/tag/milestone-3)

Use this same repository for Milestones 2–5, with a new tag/release for each.

[Beautiful Soup documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/).
Original license: [MIT](LICENSE).
