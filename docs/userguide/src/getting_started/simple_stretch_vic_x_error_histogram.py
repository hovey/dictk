"""Distribution of VIC-2D's own x error across its valid points: the
tracked x (reference x plus VIC-2D's displacement u) minus the true
x = 1.02 X, with the mean and one standard deviation marked.
"""

import csv

import matplotlib.pyplot as plt
import numpy as np

FACTOR_X = 1.02

with open("../verification/simple_stretch_vic_out.csv") as f:
    rows = [{k.strip(' "'): v for k, v in row.items()} for row in csv.DictReader(f)]
valid = [r for r in rows if float(r["sigma"]) != -1]
error_x = np.array(
    [float(r["x"]) + float(r["u"]) - FACTOR_X * float(r["x"]) for r in valid]
)
mean = error_x.mean()
std = error_x.std()
print(
    f"{len(valid)} points: mean x error {mean:+.4f} px, std {std:.4f} px, "
    f"range [{error_x.min():+.3f}, {error_x.max():+.3f}] px"
)

plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})
fig, ax = plt.subplots(figsize=(7, 4), constrained_layout=True)
ax.hist(
    error_x,
    bins=60,
    color="gray",
    alpha=0.8,
    label=rf"$x$ error at {len(valid)} valid points",
)
ax.axvspan(
    mean - std,
    mean + std,
    color="royalblue",
    alpha=0.15,
    label=rf"$\pm$ 1 standard deviation, {std:.4f} px",
)
ax.axvline(mean, color="black", linewidth=1.5, label=f"mean, {mean:+.4f} px")
ax.axvline(0, color="red", linestyle="--", linewidth=1.5, label="exact tracking, 0 px")
ax.set_xlabel(r"$x$ error (px)")
ax.set_ylabel("frequency")
ax.set_ylim(top=ax.get_ylim()[1] * 1.45)
legend = ax.legend(loc="upper right", framealpha=1.0)
legend.set_zorder(10)
fig.savefig("simple_stretch_vic_x_error_histogram.png", dpi=300)
