"""mdbook preprocessor: number every `<figure>`, and every labeled display
equation, by section and page order.

Each figure's caption gains a label such as "Figure 9.2-1:": the page's
section number from `SUMMARY.md`, then the figure's order on that page.
A caption that already starts with a hand-written "Figure:" has that
text replaced by the label. Each figure without an `id` also gains one,
such as `figure-9.2-1`. Pages without a section number are left
unchanged.

Cross-references: a Markdown link whose text is exactly `Figure` and
whose target ends in a figure's `id`, such as `[Figure](#fig-polar)` or
`[Figure](./kernel_warping.md#fig-panels)`, has its text replaced by
that figure's label, such as "Figure 2-3". Inside HTML, such as a
`<figcaption>`, where Markdown links don't render, write
`<a href="#fig-polar">Figure</a>` instead. Give a cited figure its own
descriptive `id`, so the reference survives reordering. A link to an
unknown `id` stays as written and prints a warning.

Equations: a `$$...$$` display block that holds `\\label{eq-name}` has
that label replaced by `\\tag{9.2-1}`, which KaTeX prints beside the
equation, and gains an anchor with `id="eq-name"`. Equations count
separately from figures. `[Equation](#eq-name)` and `<a
href="#eq-name">Equation</a>` resolve the same way figure references do,
to "Equation 9.2-1". A display block without a label stays unnumbered.
This preprocessor must run before `katex`, so KaTeX sees `\\tag`.

mdbook calls this script twice: once as `figure_number.py supports
<renderer>`, which exits 0 for every renderer, and once with the
`[context, book]` JSON on stdin, expecting the edited book on stdout.
"""

import json
import re
import sys
from collections.abc import Iterator

FIGURE = re.compile(r"<figure(?P<attributes>[^>]*)>(?P<body>.*?)</figure>", re.S)
CAPTION = re.compile(r"<figcaption>(?P<space>\s*)(?:Figure:\s*)?")
IDENTIFIER = re.compile(r'\bid="(?P<id>[^"]+)"')
REFERENCE = re.compile(
    r"\[(?P<kind>Figure|Equation)\]\((?P<target>[^)#\s]*#(?P<id>[^)\s]+))\)"
)
REFERENCE_HTML = re.compile(
    r'<a href="(?P<target>[^"#\s]*#(?P<id>[^"\s]+))">(?P<kind>Figure|Equation)</a>'
)
DISPLAY = re.compile(r"\$\$(?P<body>.*?)\$\$", re.S)
EQUATION_LABEL = re.compile(r"\\label\{(?P<id>[^}]+)\}")


def figures_number(*, content: str, section: str, labels: dict[str, str]) -> str:
    """`content` with every figure's caption labeled "Figure
    {section}-{n}:", counting from 1 in page order. Records each
    figure's `id` and label, such as "9.2-1", in `labels`."""
    count = 0

    def label(match: re.Match) -> str:
        nonlocal count
        count += 1
        name = f"{section}-{count}"
        attributes = match["attributes"]
        identifier = IDENTIFIER.search(attributes)
        if identifier:
            labels[identifier["id"]] = name
        else:
            attributes += f' id="figure-{name}"'
            labels[f"figure-{name}"] = name
        body = CAPTION.sub(
            lambda caption: (
                f"<figcaption>{caption['space']}<strong>Figure {name}:</strong> "
            ),
            match["body"],
            count=1,
        )
        return f"<figure{attributes}>{body}</figure>"

    return FIGURE.sub(label, content)


def equations_number(*, content: str, section: str, labels: dict[str, str]) -> str:
    """`content` with every `\\label{id}` in a `$$...$$` block replaced
    by `\\tag{{section}-{n}}`, counting from 1 in page order, and an
    anchor with that `id` placed before the block. Records each
    equation's `id` and label, such as "9.2-1", in `labels`."""
    count = 0

    def tag(match: re.Match) -> str:
        nonlocal count
        label = EQUATION_LABEL.search(match["body"])
        if label is None:
            return match[0]
        count += 1
        name = f"{section}-{count}"
        labels[label["id"]] = name
        body = EQUATION_LABEL.sub(lambda _: f"\\tag{{{name}}}", match["body"], count=1)
        return f'<span id="{label["id"]}"></span>\n\n$${body}$$'

    return DISPLAY.sub(tag, content)


def references_resolve(*, content: str, labels: dict[str, str], path: str) -> str:
    """`content` with every `[Figure](...#id)` or `[Equation](...#id)`
    link's text, and every `<a href="...#id">Figure</a>` or
    `<a href="...#id">Equation</a>` link's text, replaced by that
    figure's or equation's label. `path` names the page in any
    warning."""

    def name(match: re.Match) -> str | None:
        found = labels.get(match["id"])
        if found is None:
            print(
                f"figure_number: {path}: no {match['kind'].lower()} with id "
                f"{match['id']!r}",
                file=sys.stderr,
            )
        return found

    def markdown(match: re.Match) -> str:
        found = name(match)
        return (
            match[0]
            if found is None
            else f"[{match['kind']} {found}]({match['target']})"
        )

    def html(match: re.Match) -> str:
        found = name(match)
        return (
            match[0]
            if found is None
            else f'<a href="{match["target"]}">{match["kind"]} {found}</a>'
        )

    return REFERENCE_HTML.sub(html, REFERENCE.sub(markdown, content))


def chapters_walk(*, sections: list) -> Iterator[dict]:
    """Every chapter in `sections`, and in their sub-chapters, in book
    order."""
    for item in sections:
        if isinstance(item, dict) and "Chapter" in item:
            yield item["Chapter"]
            yield from chapters_walk(sections=item["Chapter"]["sub_items"])


def sections_number(*, sections: list) -> None:
    """Number every figure and labeled equation in `sections`, then
    resolve every reference, in place. Two passes, so a page can cite a
    figure or equation on a later page."""
    labels: dict[str, str] = {}
    for chapter in chapters_walk(sections=sections):
        if chapter["number"]:
            section = ".".join(str(part) for part in chapter["number"])
            chapter["content"] = figures_number(
                content=chapter["content"], section=section, labels=labels
            )
            chapter["content"] = equations_number(
                content=chapter["content"], section=section, labels=labels
            )
    for chapter in chapters_walk(sections=sections):
        chapter["content"] = references_resolve(
            content=chapter["content"],
            labels=labels,
            path=chapter.get("path") or chapter.get("name", "?"),
        )


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "supports":
        sys.exit(0)
    _context, book = json.load(sys.stdin)
    sections_number(sections=book["sections"])
    json.dump(book, sys.stdout)
