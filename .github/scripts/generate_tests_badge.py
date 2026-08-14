"""Generate a "tests: N pass M fail" README badge SVG from a pytest JUnit
XML report, via shields.io's static badge API -- the same approach ci.yml
already uses for the pylint score badge (see the "Run pylint
(informational) and generate lint badge/report" step), just moved into a
real script since JUnit XML parsing is more than a one-line grep/awk
extraction.

Used by the `docs` job in ci.yml, fed `pytest --junitxml=...`'s output
(a builtin pytest flag -- no extra plugin or dependency needed).
"""

import argparse
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="JUnit XML report (pytest --junitxml=...)",
    )
    parser.add_argument(
        "--output", required=True, type=Path, help="Output SVG badge path"
    )
    args = parser.parse_args()

    root = ET.parse(args.input).getroot()
    # pytest's --junitxml wraps a single <testsuite> in a <testsuites>
    # root; find it either way so this doesn't depend on which one is the
    # actual root element.
    suite = root if root.tag == "testsuite" else root.find("testsuite")

    total = int(suite.get("tests", 0))
    failed = int(suite.get("failures", 0)) + int(suite.get("errors", 0))
    skipped = int(suite.get("skipped", 0))
    passed = total - failed - skipped

    message = f"{passed} pass {failed} fail"
    if skipped:
        message += f" {skipped} skip"
    color = "brightgreen" if failed == 0 else "red"

    url = (
        "https://img.shields.io/badge/"
        f"{urllib.parse.quote('tests')}-{urllib.parse.quote(message)}-{color}?style=flat"
    )
    # shields.io returns 403 Forbidden for urllib's default User-Agent
    # (Python-urllib/x.y) -- curl (used by the lint badge's own shields.io
    # fetch in ci.yml) isn't blocked, so match that by setting an explicit
    # User-Agent here instead of shelling out to curl.
    request = urllib.request.Request(
        url, headers={"User-Agent": "dictk-ci/generate_tests_badge"}
    )
    with urllib.request.urlopen(request) as response:
        args.output.write_bytes(response.read())
    print(f"tests badge: {message} ({color}) -> {args.output}")


if __name__ == "__main__":
    main()
