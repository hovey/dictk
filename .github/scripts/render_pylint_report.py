"""Wrap a raw pylint text report in a minimal HTML page for GitHub Pages.

Used by the `docs` job in ci.yml: pylint --output-format=text --reports=yes
output has no HTML mode of its own, so this just escapes and <pre>-wraps it.
"""

import argparse
import html
from pathlib import Path

PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>dictk pylint report</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 2rem; max-width: 60rem; }}
  pre {{ background: #f6f8fa; padding: 1rem; overflow-x: auto; white-space: pre-wrap; }}
</style>
</head>
<body>
<h1>dictk &mdash; pylint report</h1>
<p>Informational only: pylint runs alongside ruff (which gates CI) purely to
produce this report and the README's pylint score badge. See
<a href="https://github.com/hovey/dictk/blob/main/CONTRIBUTING.md#running-pylint-informational">CONTRIBUTING.md</a>.</p>
<pre>{report}</pre>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    report = html.escape(args.input.read_text())
    args.output.write_text(PAGE_TEMPLATE.format(report=report))


if __name__ == "__main__":
    main()
