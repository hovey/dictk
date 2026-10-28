"""Q4 baseline: frequency response of a 15x15 window against a Q4 element
with the same footprint and a Q4 element with the same half-power period.
"""

import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import brentq

H = 5.0
M = 7
N = 2 * M + 1
COLUMNS = np.arange(-M, M + 1)
Q4_STD = np.sqrt(4 / 3)
WINDOW_STD = np.sqrt(3 / (M * (M + 1))) / N


def window_response(*, period):
    """Fitted slope over true slope at the window center, discrete fit."""
    k = 2 * np.pi / period
    slope = (COLUMNS * np.sin(k * COLUMNS * H)).sum() / ((COLUMNS**2).sum() * H)
    return slope / k


def q4_response(*, period, side):
    """Q4 slope over true slope at the element center, for u = sin(kX)."""
    z = np.pi * side / period
    return np.sin(z) / z


footprint = 2 * M * H
half_window = brentq(lambda p: window_response(period=p) - 0.5, 60, 200)
half_footprint = brentq(lambda p: q4_response(period=p, side=footprint) - 0.5, 60, 300)
matched = brentq(lambda s: q4_response(period=half_window, side=s) - 0.5, 10, 200)
matched_std = Q4_STD * H / matched

print(
    f"The window keeps half the slope of a {half_window:.0f} px wave. "
    f"The equal-footprint Q4 element, {footprint:.0f} px on a side, needs a "
    f"{half_footprint:.0f} px wave for the same. A Q4 element matches the "
    f"window's {half_window:.0f} px at {matched:.1f} px on a side. Its standard "
    f"deviation is then {matched_std:.3f} $\\sigma / h$, "
    f"{matched_std / WINDOW_STD:.1f} times the window's {WINDOW_STD:.4f}."
)

periods = np.linspace(20, 400, 800)
plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})

fig, ax = plt.subplots(figsize=(7, 4), constrained_layout=True)
ax.axhline(0, color="gray", linewidth=0.8)
ax.axhline(0.5, color="lightgray", linewidth=0.8, linestyle=":")
ax.plot(
    periods,
    [window_response(period=p) for p in periods],
    color="royalblue",
    lw=2,
    label=f"{N}x{N} window, std {WINDOW_STD:.4f} $\\sigma/h$",
)
ax.plot(
    periods,
    [q4_response(period=p, side=footprint) for p in periods],
    color="firebrick",
    lw=1.5,
    label=f"Q4, {footprint:.0f} px side, std {Q4_STD * H / footprint:.4f} $\\sigma/h$",
)
ax.plot(
    periods,
    [q4_response(period=p, side=matched) for p in periods],
    color="firebrick",
    lw=1.5,
    linestyle="--",
    label=f"Q4, {matched:.1f} px side, std {matched_std:.4f} $\\sigma/h$",
)
for period, color in [(half_window, "royalblue"), (half_footprint, "firebrick")]:
    ax.plot(period, 0.5, "o", color=color, mec="white", zorder=3)
ax.set_xlabel("wave period (px)")
ax.set_ylabel("$T$, fitted slope / true slope")
ax.legend(loc="center right", bbox_to_anchor=(1, 0.4))
fig.savefig("strain_window_q4_frequency.png", dpi=300)
