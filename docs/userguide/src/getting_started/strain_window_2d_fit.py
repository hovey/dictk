"""2D example fit: the least-squares plane through nine displacements on a
3x3 grid, with its intercept, its two center-line slopes, and residuals.
"""

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d import proj3d

TRUE_U0, TRUE_DUDX, TRUE_DUDY = 0.47, 0.14, 0.07
SIGMA = 0.065
SEED = 107
FLOOR = 0.1

c, r = np.meshgrid([-1, 0, 1], [-1, 0, 1])
c, r = c.ravel(), r.ravel()
rng = np.random.default_rng(SEED)
u = TRUE_U0 + TRUE_DUDX * c + TRUE_DUDY * r + rng.normal(0.0, SIGMA, 9)
design = np.column_stack([np.ones(9), c, r])
intercept, slope_x, slope_y = np.linalg.lstsq(design, u, rcond=None)[0]
fitted = design @ np.array([intercept, slope_x, slope_y])


def plane(x, y):
    return intercept + slope_x * x + slope_y * y


plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

fig = plt.figure(figsize=(7, 5.6), dpi=300)
ax = fig.add_subplot(projection="3d", computed_zorder=False)

edge = 1.3
gx, gy = np.meshgrid([-edge, edge], [-edge, edge])
ax.plot_surface(
    gx, gy, plane(gx, gy), color="royalblue", alpha=0.08, edgecolor="none", zorder=0
)
ax.plot_surface(
    gx,
    gy,
    np.full_like(gx, FLOOR),
    color="gray",
    alpha=0.1,
    edgecolor="none",
    zorder=-1,
)
span = np.array([-edge, edge])
for k in [-1, 0, 1]:
    for x, y in [(span, np.full(2, k)), (np.full(2, k), span)]:
        center = k == 0
        ax.plot(
            x,
            y,
            plane(x, y),
            color="royalblue" if center else "lightsteelblue",
            lw=1.8 if center else 0.6,
            zorder=1,
        )
        ax.plot(
            x,
            y,
            np.full(2, FLOOR),
            color="darkgray" if center else "lightgray",
            lw=1.4 if center else 0.6,
            zorder=-0.5,
        )

for ck, rk, uk, fk in zip(c, r, u, fitted, strict=True):
    ax.plot(
        [ck, ck], [rk, rk], [FLOOR, min(uk, fk)], color="lightgray", lw=0.6, zorder=0
    )
    ax.plot([ck, ck], [rk, rk], [uk, fk], color="firebrick", ls="--", lw=1.2, zorder=2)
ax.scatter(c, r, np.full(9, FLOOR), color="gray", s=10, depthshade=False, zorder=0)
ax.scatter(c, r, u, color="darkorange", s=40, depthshade=False, zorder=3)
ax.scatter(
    [0],
    [0],
    [intercept],
    marker="s",
    facecolor="white",
    edgecolor="royalblue",
    linewidth=1.5,
    s=70,
    depthshade=False,
    zorder=4,
)
ax.text(
    edge + 0.05,
    0,
    plane(edge, 0),
    r"$\dfrac{\partial u}{\partial X}$",
    fontsize=12,
    color="royalblue",
)
ax.text(
    0,
    edge + 0.15,
    plane(0, edge) - 0.04,
    r"$\dfrac{\partial u}{\partial Y}$",
    fontsize=12,
    color="royalblue",
)

ticks = [-1, 0, 1]
tick_labels = ["$-h$", "$0$", "$h$"]
ax.set_xticks(ticks, tick_labels)
ax.set_yticks(ticks, tick_labels)
ax.set_zticks([])
ax.set_xlim(-1.4, 1.4)
ax.set_ylim(1.4, -1.4)
ax.set_zlim(FLOOR, 0.8)
ax.set_xlabel("$x$", fontsize=13)
ax.set_ylabel("$y$", fontsize=13)
ax.set_zlabel("$u$", fontsize=13)
for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
    axis.pane.fill = False
    axis.pane.set_edgecolor("none")
ax.grid(False)
ax.set_box_aspect((1, 1, 0.75))
ax.view_init(elev=30, azim=-125)


def screen_annotate(text, point, offset, **kwargs):
    x, y, _ = proj3d.proj_transform(*point, ax.get_proj())
    ax.annotate(text, (x, y), textcoords="offset points", xytext=offset, **kwargs)


for ck, rk, uk, fk in zip(c, r, u, fitted, strict=True):
    if (ck, rk) == (0, -1):
        offset, ha = (-8, 8), "right"
    elif uk > fk:
        offset, ha = (0, 9), "center"
    else:
        offset, ha = (8, -14), "left"
    screen_annotate(
        f"$u_{{{ck},{rk}}}$",
        (ck, rk, uk),
        offset,
        ha=ha,
        fontsize=12,
        color="darkorange",
    )
screen_annotate(
    r"$\hat{u}_0$",
    (0, 0, intercept),
    (-14, 8),
    ha="right",
    fontsize=14,
    color="royalblue",
)
fig.canvas.draw()
pixels = np.asarray(fig.canvas.buffer_rgba())
rows, columns = np.nonzero((pixels[:, :, :3] < 250).any(axis=2))
margin = 30
crop = pixels[
    max(rows.min() - margin, 0) : rows.max() + margin,
    max(columns.min() - margin, 0) : columns.max() + margin,
]
plt.imsave("strain_window_2d_fit.png", crop, dpi=300)
