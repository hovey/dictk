import importlib.util
from pathlib import Path

import pytest

_path = Path(__file__).parent.parent / "docs" / "userguide" / "figure_number.py"
_spec = importlib.util.spec_from_file_location("figure_number", _path)
figure_number = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(figure_number)


def test_figures_number_requires_keyword_arguments():
    with pytest.raises(TypeError):
        figure_number.figures_number("", "1", {})  # type: ignore[misc]


def test_figures_number_labels_in_page_order():
    content = (
        "<figure><img/><figcaption>First.</figcaption></figure>\n"
        "text\n"
        "<figure><img/><figcaption>Second.</figcaption></figure>"
    )
    numbered = figure_number.figures_number(content=content, section="9.2", labels={})
    assert '<figure id="figure-9.2-1">' in numbered
    assert "<strong>Figure 9.2-1:</strong> First." in numbered
    assert '<figure id="figure-9.2-2">' in numbered
    assert "<strong>Figure 9.2-2:</strong> Second." in numbered


def test_figures_number_replaces_hand_written_label():
    content = (
        '<figure class="figure-box">\n    <img/>\n    <figcaption>\n'
        "        Figure:  Illustration.\n    </figcaption>\n</figure>"
    )
    numbered = figure_number.figures_number(content=content, section="2.1", labels={})
    assert '<figure class="figure-box" id="figure-2.1-1">' in numbered
    assert "<strong>Figure 2.1-1:</strong> Illustration." in numbered
    assert "Figure:" not in numbered


def test_figures_number_keeps_existing_id():
    content = '<figure id="custom"><figcaption>A.</figcaption></figure>'
    numbered = figure_number.figures_number(content=content, section="3", labels={})
    assert numbered.count("id=") == 1
    assert '<figure id="custom">' in numbered
    assert "<strong>Figure 3-1:</strong> A." in numbered


def test_figures_number_counts_two_image_figure_once():
    content = (
        "<figure><div><img/><img/></div><figcaption>Pair.</figcaption></figure>"
        "<figure><img/><figcaption>Next.</figcaption></figure>"
    )
    numbered = figure_number.figures_number(content=content, section="10", labels={})
    assert "<strong>Figure 10-1:</strong> Pair." in numbered
    assert "<strong>Figure 10-2:</strong> Next." in numbered


def _chapter(*, number, content, sub_items=()):
    return {
        "Chapter": {
            "number": number,
            "content": content,
            "sub_items": list(sub_items),
        }
    }


def test_sections_number_walks_sub_chapters_and_skips_unnumbered():
    figure = "<figure><figcaption>X.</figcaption></figure>"
    sections = [
        _chapter(
            number=[9],
            content=figure,
            sub_items=[_chapter(number=[9, 2], content=figure)],
        ),
        "Separator",
        _chapter(number=None, content=figure),
    ]
    figure_number.sections_number(sections=sections)
    assert "Figure 9-1" in sections[0]["Chapter"]["content"]
    sub = sections[0]["Chapter"]["sub_items"][0]["Chapter"]["content"]
    assert "Figure 9.2-1" in sub
    assert "<strong>" not in sections[2]["Chapter"]["content"]


def test_figures_number_records_labels_by_id():
    content = (
        '<figure id="fig-a"><figcaption>A.</figcaption></figure>'
        "<figure><figcaption>B.</figcaption></figure>"
    )
    labels = {}
    figure_number.figures_number(content=content, section="2", labels=labels)
    assert labels == {"fig-a": "2-1", "figure-2-2": "2-2"}


def test_references_resolve_same_page_and_cross_page():
    labels = {"fig-a": "2-3", "fig-b": "9.3-1"}
    content = "in [Figure](#fig-a) and [Figure](./kernel_warping.md#fig-b)."
    resolved = figure_number.references_resolve(
        content=content, labels=labels, path="p.md"
    )
    assert resolved == (
        "in [Figure 2-3](#fig-a) and [Figure 9.3-1](./kernel_warping.md#fig-b)."
    )


def test_references_resolve_leaves_other_links_alone():
    content = "[figure](#fig-a) [Figures](#fig-a) [Figure 2-3](#fig-a)"
    resolved = figure_number.references_resolve(
        content=content, labels={"fig-a": "2-3"}, path="p.md"
    )
    assert resolved == content


def test_references_resolve_warns_on_unknown_id(capsys):
    content = "see [Figure](#missing)"
    resolved = figure_number.references_resolve(content=content, labels={}, path="p.md")
    assert resolved == content
    assert "p.md" in capsys.readouterr().err


def test_sections_number_resolves_reference_to_a_later_page():
    sections = [
        _chapter(number=[1], content="see [Figure](./two.md#fig-late)."),
        _chapter(
            number=[2],
            content='<figure id="fig-late"><figcaption>L.</figcaption></figure>',
        ),
    ]
    figure_number.sections_number(sections=sections)
    assert "[Figure 2-1](./two.md#fig-late)" in sections[0]["Chapter"]["content"]


def test_references_resolve_html_anchor_inside_caption():
    content = '<figcaption>see <a href="#fig-a">Figure</a>.</figcaption>'
    resolved = figure_number.references_resolve(
        content=content, labels={"fig-a": "8.1-5"}, path="p.md"
    )
    assert resolved == '<figcaption>see <a href="#fig-a">Figure 8.1-5</a>.</figcaption>'
