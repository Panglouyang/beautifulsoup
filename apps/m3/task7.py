"""Set class='test' on every p tag during parsing, then save the tree."""

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bs4 import BeautifulSoup, FeatureNotFound, SoupReplacer


def paragraph_attrs(tag):
    """Preserve other attributes and replace the entire class value on p."""
    if tag.name == "p":
        return dict(tag.attrs, **{"class": "test"})
    return tag.attrs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="HTML or XML file")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--parser", choices=("html.parser", "lxml", "xml"))
    args = parser.parse_args()
    output = args.output or args.input.with_name(args.input.stem + ".task7" + args.input.suffix)
    if output.resolve() == args.input.resolve():
        parser.error("Output path must differ from input path")
    selected = args.parser or ("xml" if args.input.suffix.lower() == ".xml" else "html.parser")
    try:
        with args.input.open("rb") as source:
            soup = BeautifulSoup(source, selected,
                                 replacer=SoupReplacer(attrs_xformer=paragraph_attrs))
        output.write_text(str(soup), encoding="utf-8")
    except (OSError, FeatureNotFound, MemoryError, ValueError) as error:
        print(f"ERROR: {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    print(f"Saved: {output}")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
