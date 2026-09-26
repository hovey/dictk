"""The six steepest-descent images of IC-GN's update, for the reference
kernel at the point Kernel Warping's panel figure tracks. Each image is
one component of s(xi), in the same order as p = (u, u_x, u_y, v, v_x,
v_y). The Hessian H is built from these six images alone.
"""

import matplotlib.pyplot as plt
import numpy as np

from dictk.image import read

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

X0, Y0 = 150, 150
MARGIN = 13

reference_image = read(path="astronaut0.png").astype(np.float64)
gradient_y, gradient_x = np.gradient(reference_image)
rows = slice(Y0 - MARGIN, Y0 + MARGIN + 1)
columns = slice(X0 - MARGIN, X0 + MARGIN + 1)
fx = gradient_x[rows, columns]
fy = gradient_y[rows, columns]
dy, dx = np.mgrid[-MARGIN : MARGIN + 1, -MARGIN : MARGIN + 1].astype(np.float64)

components = [
    (r"$u$:  $f_x$", fx),
    (r"$u_x$:  $f_x\,\Delta x$", fx * dx),
    (r"$u_y$:  $f_x\,\Delta y$", fx * dy),
    (r"$v$:  $f_y$", fy),
    (r"$v_x$:  $f_y\,\Delta x$", fy * dx),
    (r"$v_y$:  $f_y\,\Delta y$", fy * dy),
]
extent = (-MARGIN - 0.5, MARGIN + 0.5, MARGIN + 0.5, -MARGIN - 0.5)
fig, axes = plt.subplots(2, 3, figsize=(10, 6.4), constrained_layout=True)
for ax, (title, values) in zip(axes.flat, components):
    limit = np.abs(values).max()
    shown = ax.imshow(values, cmap="RdBu_r", vmin=-limit, vmax=limit, extent=extent)
    ax.set_title(title)
    ax.set_xlabel(r"$\Delta x$ (px)")
    ax.set_ylabel(r"$\Delta y$ (px)")
    fig.colorbar(shown, ax=ax, shrink=0.8)
fig.savefig("kernel_warping_steepest.png", dpi=200)
