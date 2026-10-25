"""Generate a large input and verify/time every application.

Run from the repository root: python apps/m2/benchmark.py
Generated input and result files stay in an automatically cleaned temp folder.
"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from time import perf_counter
import tracemalloc

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from bs4 import BeautifulSoup, SoupStrainer


def main():
    apps = Path(__file__).resolve().parent
    results = {}
    with tempfile.TemporaryDirectory(prefix="bs4-m2-") as folder:
        source = Path(folder) / "large.html"
        # 20,000 sibling sections, sparse anchors/ids, about 12 MiB.
        with source.open("w", encoding="utf-8") as out:
            out.write("<html><body>")
            for index in range(20000):
                out.write('<section><p>' + "x" * 600 + '</p><b>bold</b>')
                if index % 100 == 0:
                    out.write(f'<a id="link-{index}" href="/{index}">link</a>')
                out.write("</section>")
            out.write("</body></html>")
        results["input_bytes"] = source.stat().st_size
        for label, strainer, count in (
            ("full", None, 60202),
            ("anchors", SoupStrainer("a"), 200),
            ("all_tags", SoupStrainer(True), 60202),
            ("ids", SoupStrainer(id=True), 200),
        ):
            tracemalloc.start()
            started = perf_counter()
            with source.open("rb") as stream:
                soup = BeautifulSoup(stream, "html.parser", parse_only=strainer)
            elapsed = perf_counter() - started
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            retained = len(soup.find_all(True))
            assert retained == count, (label, retained)
            results[label] = {"parse_seconds": round(elapsed, 3),
                              "peak_python_MiB": round(peak / 1024**2, 2),
                              "retained_tags": retained}
            del soup
        for task in (2, 3, 4, 6):
            command = [sys.executable, str(apps / f"task{task}.py"), str(source)]
            output = Path(folder) / "replaced.html"
            if task == 6:
                command.extend(["--output", str(output)])
            completed = subprocess.run(command, stdout=subprocess.DEVNULL,
                                       stderr=subprocess.PIPE, text=True, check=True)
            results[f"task{task}"] = completed.stderr.strip()
            if task == 6:
                transformed = output.read_text(encoding="utf-8")
                assert transformed.count("<blockquote>") == 20000
                assert "<b>" not in transformed
        results["python"] = sys.version
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
