"""Walk every node of an HTML/XML file with `for node in soup` and report counts."""

import argparse
from collections import Counter
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bs4 import BeautifulSoup, FeatureNotFound
from bs4.element import Tag


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="HTML or XML file")
    parser.add_argument("--parser", choices=("html.parser", "lxml", "xml"))
    parser.add_argument("--print", dest="show", action="store_true",
                        help="also print one line per node")
    args = parser.parse_args()
    selected = args.parser or ("xml" if args.input.suffix.lower() == ".xml" else "html.parser")
    try:
        with args.input.open("rb") as source:
            soup = BeautifulSoup(source, selected)
    except (OSError, FeatureNotFound, MemoryError, ValueError) as error:
        print(f"ERROR: {type(error).__name__}: {error}", file=sys.stderr)
        return 1

    kinds, tags = Counter(), Counter()
    start = time.perf_counter()
    for node in soup:  # Milestone 4: the soup itself is iterable.
        kinds[type(node).__name__] += 1
        if isinstance(node, Tag):
            tags[node.name] += 1
        if args.show:
            label = f"<{node.name}>" if isinstance(node, Tag) else repr(str(node)[:60])
            print(f"{type(node).__name__:24s} {label}")
    elapsed = time.perf_counter() - start

    print(f"Visited {sum(kinds.values())} nodes in {elapsed:.3f}s")
    for name, count in kinds.most_common():
        print(f"  {name:24s} {count}")
    print("Most common tags:", ", ".join(f"{n}={c}" for n, c in tags.most_common(10)))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
