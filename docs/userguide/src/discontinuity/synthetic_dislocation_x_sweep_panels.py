"""Show the ZNCC Correlation Surface panel itself, side by side, at five
kernel window center x positions straddling the crack -- the single
peak at x=130 splitting into two, crossing near the crack, and merging
back into a single peak at x=170.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

import dictk
from dictk.image import combine, crack_dislocation, subimage, PixelCoordinate
from dictk.correlation import zncc
from dictk.plot import _correlation_surface_ticks

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

WIDTH = HEIGHT = 300
OFFSET = 4.0
KERNEL_MARGIN = 25
SEARCH_MARGIN = 45
Y = 150
VICINITY_MARGIN = 4
XS_PANELS = [130, 140, 150, 160, 170]

speckle = dictk.rosta(width=WIDTH, height=HEIGHT, density=0.5)
photo = dictk.astronaut(width=WIDTH, height=HEIGHT)
reference_image = combine(a=speckle, b=photo)
current_image = crack_dislocation(arr=reference_image, offset=OFFSET)

fig, axes = plt.subplots(
    1, len(XS_PANELS), figsize=(15.0, 3.4), constrained_layout=True
)
for ax, x in zip(axes, XS_PANELS):
    p0 = PixelCoordinate(x=x, y=Y)
    kernel = subimage(
        image=reference_image,
        origin=PixelCoordinate(x=p0.x - KERNEL_MARGIN, y=p0.y - KERNEL_MARGIN),
        width=2 * KERNEL_MARGIN,
        height=2 * KERNEL_MARGIN,
    )
    search = subimage(
        image=current_image,
        origin=PixelCoordinate(x=p0.x - SEARCH_MARGIN, y=p0.y - SEARCH_MARGIN),
        width=2 * SEARCH_MARGIN,
        height=2 * SEARCH_MARGIN,
    )
    surf = zncc(kernel=kernel, search=search)
    peak_y, peak_x = np.unravel_index(np.argmax(surf), surf.shape)

    im = ax.imshow(surf, cmap="viridis", vmin=0, vmax=1, origin="upper")
    ax.add_patch(
        patches.Circle(
            (peak_x, peak_y),
            radius=VICINITY_MARGIN,
            edgecolor="red",
            facecolor="none",
            linewidth=1.5,
        )
    )
    ax.set_title(f"x={x}")
    ax.set_xlabel(r"$\Delta x$ offset (pixels)")
    surface_height, surface_width = surf.shape
    ax.set_xticks(_correlation_surface_ticks(surface_width))
    ax.set_yticks(_correlation_surface_ticks(surface_height))

axes[0].set_ylabel(r"$\Delta y$ offset (pixels)")
for ax in axes[1:]:
    ax.set_yticklabels([])

fig.colorbar(im, ax=axes, shrink=0.8, label="ZNCC value")
fig.savefig("synthetic_dislocation_x_sweep_panels.png", dpi=300)
print("Saved: synthetic_dislocation_x_sweep_panels.png")
