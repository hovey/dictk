"""The First Sweep: directly triggers the asymmetric-padding bug that
motivates the rest of Recoverable Displacement Range, using
`recoverable_displacement_range_uncentered_demo.py`'s `locate_uncentered`
-- the real, shipped `locate` has already been fixed and would not
reproduce this collapse.

Reports `expected`/`found` in two reference frames side by side:
`current_image`'s own absolute frame (what `locate_uncentered` actually
returns), and the local frame of `search` itself -- labeled "Fixed
Image, frame $\\mathcal{S}$" in Seeing the Cliff's quadrant figures below,
matching that panel's own boxes exactly: `expected` here always equals
the correlation surface's own true peak, `found` always equals the
figures' magenta box.

Runs live on every book build, not from a committed snapshot. Raw HTML,
not markdown pipe-table syntax, since the spanning reference-frame
header needs colspan -- markdown tables can't express that (same reason
Multi-Point Motion's own Point Grid table uses raw HTML).
"""

from dictk.image import PixelCoordinate, read, translate
from recoverable_displacement_range_uncentered_demo import locate_uncentered

if __name__ == "__main__":
    reference_image = read(path="astronaut0.png")
    p0 = PixelCoordinate(x=150, y=150)
    kernel_margin = 30
    search_margin = 150  # generous -- per Root Cause, size won't help here --
    # and exactly half of astronaut0's 300px canvas, so Seeing the Cliff's
    # figures below read the whole image with no extraction margin of
    # their own
    search_origin = PixelCoordinate(x=p0.x - search_margin, y=p0.y - search_margin)

    print("<table>")
    print("<thead>")
    print(
        '<tr><th rowspan="2">dx</th>'
        '<th colspan="2">current_image (absolute)</th>'
        '<th colspan="2">Fixed Image, frame $\\mathcal{S}$</th>'
        '<th rowspan="2">match</th></tr>'
    )
    print("<tr><th>expected</th><th>found</th><th>expected</th><th>found</th></tr>")
    print("</thead>")
    print("<tbody>")
    for dx in [0, 10, 20, 25, 29, 30, 31, 35, 40, 50]:
        current_image = translate(arr=reference_image, dx=dx, dy=0)
        expected = PixelCoordinate(x=p0.x + dx, y=p0.y)
        found = locate_uncentered(
            reference_image, current_image, p0, p0, kernel_margin, search_margin
        )
        expected_s = PixelCoordinate(
            x=(expected.x - kernel_margin) - search_origin.x,
            y=(expected.y - kernel_margin) - search_origin.y,
        )
        found_s = PixelCoordinate(
            x=(found.x - kernel_margin) - search_origin.x,
            y=(found.y - kernel_margin) - search_origin.y,
        )
        print(
            f"<tr><td>{dx}</td>"
            f"<td>({expected.x},{expected.y})</td><td>({found.x},{found.y})</td>"
            f"<td>({expected_s.x},{expected_s.y})</td><td>({found_s.x},{found_s.y})</td>"
            f"<td>{found == expected}</td></tr>"
        )
    print("</tbody>")
    print("</table>")
