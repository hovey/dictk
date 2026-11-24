"""Check every relative link in the user guide and in dictk's docstrings.

mdbook does not fail on a broken link, so a page moved without its
links updated still builds. This script resolves each relative link the
way the published site does: the book's pages sit at the site root, and
pdoc's API pages sit under `api/dictk/`. A link passes when its target
exists:

- A `.md` or `.html` page passes when its `.md` source exists.
- An `api/dictk/<module>.html` page passes when `src/dictk/<module>.py`
  exists.
- Any other file passes when it exists, or when a script or `cmdrun`
  line in the target's directory names it, since the build generates
  most figures and data files.

Links inside fenced code blocks and HTML comments are skipped, along
with absolute URLs and same-page `#` anchors. Anchors are not checked.

Most figures exist only after `mdbook build` runs the `cmdrun`
scripts, and their names are often built at run time. So the full check
belongs after a build. `--pages-only` checks just the page and API
links, which need no build.

Run from the repo root: `python docs/userguide/link_check.py`. Exits 1
and lists each broken link if any target is missing.
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[2]
SITE: Final = ROOT / "docs" / "userguide" / "src"
PACKAGE: Final = ROOT / "src" / "dictk"
LINK: Final = re.compile(r"\]\(([^)\s]+)\)|(?:src|href)=\"([^\"]+)\"")
FENCE: Final = re.compile(r"^```.*?^```", re.MULTILINE | re.DOTALL)
COMMENT: Final = re.compile(r"<!--.*?-->", re.DOTALL)
CMDRUN: Final = re.compile(r"<!--\s*cmdrun.*?-->", re.DOTALL)
FILE_NAME: Final = re.compile(r"[\w{}./-]+\.(?:png|tiff?|csv|zip|json|npz|npy|svg|jpg)")


def targets(*, text: str) -> list[str]:
    """Every relative link target in `text`, outside code fences and
    HTML comments, without its `#` anchor."""
    text = COMMENT.sub("", FENCE.sub("", text))
    found = []
    for match in LINK.finditer(text):
        target = (match[1] or match[2]).split("#")[0].split("?")[0]
        if target and not re.match(r"^[a-z]+:", target):
            found.append(target)
    return found


def generated(*, path: Path, referrer: Path) -> bool:
    """Whether a script or `cmdrun` line in `path`'s directory names
    `path`, other than in `referrer` itself. A name built by an
    f-string, such as `f"{name}_preview.png"`, matches with each `{...}`
    standing for any text."""
    texts = [script.read_text() for script in path.parent.glob("*.py")]
    texts += [
        block
        for page in path.parent.glob("*.md")
        if page != referrer
        for block in CMDRUN.findall(page.read_text())
    ]
    for text in texts:
        if path.name in text:
            return True
        for literal in FILE_NAME.findall(text):
            name = literal.rsplit("/", 1)[-1]
            parts = re.split(r"\{[^{}]*\}", name)
            stem = "".join(parts).rsplit(".", 1)[0]
            # `f"{name}.tif"` would match any .tif; require real text.
            if len(re.sub(r"\W", "", stem)) >= 3 and re.fullmatch(
                ".+".join(map(re.escape, parts)), path.name
            ):
                return True
    return False


def exists(*, site_path: Path, referrer: Path) -> bool:
    """Whether the site path `site_path`, under `SITE`, has a source."""
    parts = site_path.relative_to(SITE).parts
    if parts[:2] == ("api", "dictk") and site_path.suffix == ".html":
        module = "__init__" if len(parts) == 2 else Path(*parts[2:]).stem
        return (PACKAGE / f"{module}.py").exists()
    if parts == ("api", "dictk.html"):
        return (PACKAGE / "__init__.py").exists()
    if site_path.suffix in (".md", ".html"):
        return site_path.with_suffix(".md").exists()
    return site_path.exists() or generated(path=site_path, referrer=referrer)


def broken_links(*, pages_only: bool) -> list[str]:
    """Each broken link, as `file: target`. With `pages_only`, only
    links to `.md`, `.html`, and API pages are checked."""
    broken = []
    sources = [(page, page.parent) for page in sorted(SITE.rglob("*.md"))]
    # A docstring link resolves from the module's own API page.
    sources += [
        (module, SITE / "api" / "dictk") for module in sorted(PACKAGE.glob("*.py"))
    ]
    for source, base in sources:
        for target in targets(text=source.read_text()):
            site_path = Path(*(base / target).resolve(strict=False).parts).resolve(
                strict=False
            )
            try:
                site_path.relative_to(SITE)
            except ValueError:
                broken.append(f"{source.relative_to(ROOT)}: {target} (leaves the site)")
                continue
            if pages_only and site_path.suffix not in (".md", ".html"):
                continue
            if not exists(site_path=site_path, referrer=source):
                broken.append(f"{source.relative_to(ROOT)}: {target}")
    return broken


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--pages-only",
        action="store_true",
        help=(
            "Check only links to .md, .html, and API pages, skipping figures "
            "and data files, which exist only after `mdbook build` runs every "
            "cmdrun script (type: flag; default: off, checking every link)."
        ),
    )
    args = parser.parse_args()
    broken = broken_links(pages_only=args.pages_only)
    for line in broken:
        print(line)
    print(f"{len(broken)} broken link(s)")
    sys.exit(1 if broken else 0)


if __name__ == "__main__":
    main()
