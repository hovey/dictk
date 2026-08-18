"""The Fix's dx sweep table, from Recoverable Displacement Range,
rendered as raw HTML instead of markdown pipe-table syntax so the two
failing (wraparound) rows can carry a `match-false` class -- markdown
tables have no way to style an individual row.

Runs live on every book build, not from a committed snapshot.
"""

from dictk.image import PixelCoordinate, read, translate
from dictk.translation import locate

if __name__ == "__main__":
    reference_image = read(path="astronaut0.png")
    p0 = PixelCoordinate(x=150, y=150)
    kernel_margin = 30
    search_margin = 45

    print(
        "<table><thead><tr><th>dx</th><th>expected</th><th>found</th><th>match</th></tr></thead><tbody>"
    )
    for dx in [30, 40, 44, 45, 46, -44, -45]:
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
        match = found == expected
        row_class = ' class="match-false"' if not match else ""
        print(
            f"<tr{row_class}><td>{dx}</td><td>({expected.x},{expected.y})</td>"
            f"<td>({found.x},{found.y})</td><td>{match}</td></tr>"
        )
    print("</tbody></table>")
