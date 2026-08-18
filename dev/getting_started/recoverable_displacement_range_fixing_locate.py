r"""Fixing `locate`: re-runs The First Sweep's exact scenario and dx
values, this time against the real, shipped `dictk.translation.locate`
-- not `locate_uncentered` -- to show the fix directly, before the rest
of this page walks through why it was needed.

Same two reference frames as The First Sweep's own table: `current_image`'s
own absolute frame (what `locate` actually returns), and the local frame
of `search` itself, labeled "Fixed Image, frame $\mathcal{S}$" to match
Seeing the Cliff's quadrant figures above -- those figures aren't
redrawn here (they already show the pre-fix failure; this table shows
the post-fix success, numbers only).

Runs live on every book build, not from a committed snapshot. Raw HTML,
not markdown pipe-table syntax, for the same colspan reason The First
Sweep's own table needs it.
"""

from dictk.image import PixelCoordinate, read, translate
from dictk.translation import locate

if __name__ == "__main__":
    reference_image = read(path="astronaut0.png")
    p0 = PixelCoordinate(x=150, y=150)
    kernel_margin = 30
    search_margin = 150
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
        found = locate(
            reference_image=reference_image,
            current_image=current_image,
            reference_point=p0,
            search_center=p0,
            kernel_margin_width=kernel_margin,
            kernel_margin_height=kernel_margin,
            search_margin_width=search_margin,
            search_margin_height=search_margin,
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
