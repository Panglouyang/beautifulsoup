"""Shared command-line plumbing for the Milestone 2 applications."""

import argparse
from pathlib import Path
import sys
from time import perf_counter

# Direct `python apps/m2/task2.py` must use this repository's modified bs4.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bs4 import BeautifulSoup, FeatureNotFound


def run_task(description, strainer=None, replacer=None, save=False):
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("input", type=Path, help="HTML or XML file")
    parser.add_argument("--parser", choices=("html.parser", "lxml", "xml"))
    if save:
        parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    selected_parser = args.parser or (
        "xml" if args.input.suffix.lower() == ".xml" else "html.parser"
    )
    output = None
    if save:
        output = args.output or args.input.with_name(
            args.input.stem + ".task6.blockquote" + args.input.suffix
        )
        if output.resolve() == args.input.resolve():
            parser.error("Output path must differ from input path")
    started = perf_counter()
    try:
        with args.input.open("rb") as stream:
            soup = BeautifulSoup(
                stream, selected_parser, parse_only=strainer, replacer=replacer
            )
        parsed = perf_counter()
        if save:
            output.write_text(str(soup), encoding="utf-8")
            print(f"Saved: {output}")
        else:
            # A selected parent retains its descendants, so filter results
            # again: e.g. a child of an id-bearing node may have no id.
            matches = soup.find_all(strainer)
            for tag in matches:
                print(tag)
    except (OSError, FeatureNotFound, MemoryError, ValueError) as error:
        print(f"ERROR: {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    print(
        f"Parser: {selected_parser}; parse seconds: {parsed - started:.3f}; "
        f"total seconds: {perf_counter() - started:.3f}", file=sys.stderr,
    )
    return 0


def main(description, **kwargs):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(run_task(description, **kwargs))
