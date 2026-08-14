"""Draws the reference point, its kernel (green), and its search window
(red) from The Fix in Recoverable Displacement Range, along with the
two positions one pixel past the search_margin edge where `locate`
wraps and fails.

Runs live on every book build, not from a committed snapshot.
"""

import matplotlib.patches as patches
import matplotlib.pyplot as plt

p0_x, p0_y = 150, 150
kernel_margin = 30
search_margin = 45

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})
fig, ax = plt.subplots(figsize=(7.5, 6.5), constrained_layout=True)

ax.plot(p0_x, p0_y, "o", color="black", markersize=5, zorder=8)
ax.annotate(
    "$P\\ (150, 150)$",
    (p0_x, p0_y),
    textcoords="offset points",
    xytext=(0, 18),
    ha="center",
    fontsize=10,
    zorder=9,
)

# kernel (green) and search window (red), same colors as cross_correlation.md
ax.add_patch(
    patches.Rectangle(
        (p0_x - kernel_margin, p0_y - kernel_margin),
        2 * kernel_margin,
        2 * kernel_margin,
        edgecolor="green",
        facecolor="none",
        linewidth=1.5,
        zorder=3,
    )
)
ax.add_patch(
    patches.Rectangle(
        (p0_x - search_margin, p0_y - search_margin),
        2 * search_margin,
        2 * search_margin,
        edgecolor="red",
        facecolor="none",
        linewidth=1.5,
        zorder=2,
    )
)

# two dx displacement lines, each with arrowheads at both its own ends,
# right at y=150 -- P's own row. Left: P to the dx=-45 marker. Right: P
# to the dx=+46 marker. Labels sit right on the line, in the gap between
# the kernel box and each marker, clear of the kernel box itself.
dx_y = p0_y
for x_start, x_end, label, label_x in [
    (p0_x - 45, p0_x, "dx = -45", 117),
    (p0_x, p0_x + 46, "dx = +46", 184),
]:
    ax.annotate(
        "",
        xy=(x_end, dx_y),
        xytext=(x_start, dx_y),
        arrowprops=dict(
            arrowstyle="<->", color="magenta", linewidth=1.5, shrinkA=0, shrinkB=0
        ),
        zorder=6,
    )
    ax.text(
        label_x,
        dx_y,
        label,
        ha="center",
        va="center",
        fontsize=7.5,
        color="magenta",
        zorder=7,
        bbox=dict(facecolor="white", edgecolor="none", pad=1),
    )

# one pixel past the search_margin edge, both sides -- where locate wraps
ax.plot(
    p0_x + 46, p0_y, "x", color="tab:red", markersize=10, markeredgewidth=2.5, zorder=4
)
ax.plot(
    p0_x - 45, p0_y, "x", color="tab:red", markersize=10, markeredgewidth=2.5, zorder=4
)
ax.annotate(
    "dx=+46\n1 px past the\nsearch_margin edge\n→ wraps, fails",
    (p0_x + 46, p0_y),
    textcoords="offset points",
    xytext=(35, -45),
    fontsize=8,
    ha="left",
    color="tab:red",
    arrowprops=dict(arrowstyle="-", color="gray", linewidth=0.7, shrinkA=3, shrinkB=3),
)
ax.annotate(
    "dx=-45\nright at the\nsearch_margin edge\n→ wraps, fails",
    (p0_x - 45, p0_y),
    textcoords="offset points",
    xytext=(-40, 45),
    fontsize=8,
    ha="right",
    color="tab:red",
    arrowprops=dict(arrowstyle="-", color="gray", linewidth=0.7, shrinkA=3, shrinkB=3),
)

# dimension arrows for both boxes -- kdim_y sits close to the kernel
# box's own top edge; sdim_y stays further out, above the search box
kdim_y, sdim_y = p0_y - kernel_margin - 4, p0_y - search_margin - 8
ax.annotate(
    "",
    xy=(p0_x - kernel_margin, kdim_y),
    xytext=(p0_x + kernel_margin, kdim_y),
    arrowprops=dict(arrowstyle="<->", color="green", shrinkA=0, shrinkB=0),
)
ax.text(
    p0_x,
    kdim_y - 3,
    "60 px (2×kernel_margin)",
    ha="center",
    va="bottom",
    fontsize=8,
    color="green",
)
ax.annotate(
    "",
    xy=(p0_x - search_margin, sdim_y),
    xytext=(p0_x + search_margin, sdim_y),
    arrowprops=dict(arrowstyle="<->", color="red", shrinkA=0, shrinkB=0),
)
ax.text(
    p0_x,
    sdim_y - 3,
    "90 px (2×search_margin)",
    ha="center",
    va="bottom",
    fontsize=8,
    color="red",
)

# guide lines from each search_margin edge down to a caption naming its dx value
caption_y = p0_y + search_margin + 18
for x_edge, sign in [(p0_x - search_margin, "-45"), (p0_x + search_margin, "+45")]:
    ax.plot(
        [x_edge, x_edge],
        [p0_y + search_margin, caption_y - 3],
        color="gray",
        linestyle="--",
        linewidth=0.8,
    )
    ax.text(
        x_edge,
        caption_y,
        f"search_margin edge = dx={sign}",
        ha="center",
        va="top",
        fontsize=7.5,
        color="darkred",
    )

ax.set_xlim(p0_x - search_margin - 55, p0_x + search_margin + 55)
ax.set_ylim(p0_y + search_margin + 35, sdim_y - 12)
ax.set_xlabel("x (pixels)")
ax.set_ylabel("y (pixels)")
ax.set_aspect("equal")

fig.savefig("recoverable_displacement_range_the_fix_cliff.png", dpi=300)
print("Saved: recoverable_displacement_range_the_fix_cliff.png")
