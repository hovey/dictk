"""Frequency response of a 15x15 window at 5 px spacing: the fitted slope
of u = sin(kX) over the true slope at the window center, from the discrete
least-squares fit and from the continuum formula with half-width nh/2.
"""

import matplotlib.pyplot as plt
import numpy as np

H = 5.0
M = 7
N = 2 * M + 1
BIAS_PERIOD = 51.0

q = np.arange(-M, M + 1)


def discrete(*, period: float) -> float:
    k = 2 * np.pi / period
    return (q * np.sin(k * H * q)).sum() / ((q * q).sum() * H * k)


def continuum(*, period: float) -> float:
    z = (2 * np.pi / period) * N * H / 2
    return 3 * (np.sin(z) - z * np.cos(z)) / z**3


def period_where(*, target: float, low: float, high: float) -> float:
    for _ in range(60):
        mid = 0.5 * (low + high)
        if (discrete(period=low) - target) * (discrete(period=mid) - target) <= 0:
            high = mid
        else:
            low = mid
    return 0.5 * (low + high)


print(
    f"At a {BIAS_PERIOD:.0f} px period, the discrete fit gives "
    f"$T$ = {discrete(period=BIAS_PERIOD):+.4f}. The continuum formula with "
    f"$a = nh/2$ gives {continuum(period=BIAS_PERIOD):+.4f}. "
    f"The discrete $T$ crosses zero at a "
    f"{period_where(target=0.0, low=45, high=70):.1f} px period. "
    f"It reaches 0.5 at {period_where(target=0.5, low=60, high=300):.0f} px "
    f"and 0.9 at {period_where(target=0.9, low=100, high=600):.0f} px."
)

periods = np.linspace(20, 400, 800)
plt.rcParams.update({"font.family": "serif", "mathtext.fontset": "cm"})
fig, ax = plt.subplots(figsize=(7, 4), constrained_layout=True)
ax.axhline(0, color="gray", linewidth=0.8)
ax.plot(
    periods,
    [continuum(period=x) for x in periods],
    "-",
    color="black",
    label="continuum, $a = nh/2$",
)
ax.plot(
    periods,
    [discrete(period=x) for x in periods],
    "--",
    color="royalblue",
    label=f"discrete, ${N}\\times{N}$ points, $h$ = {H:.0f} px",
)
ax.plot(
    BIAS_PERIOD,
    discrete(period=BIAS_PERIOD),
    "o",
    color="red",
    label=f"{BIAS_PERIOD:.0f} px wave, $T$ = {discrete(period=BIAS_PERIOD):+.3f}",
)
ax.axvline(
    N * H, color="gray", linestyle=":", label=f"period = window extent, {N * H:.0f} px"
)
ax.set_xlabel("wave period (px)")
ax.set_ylabel("$T$, fitted slope / true slope")
ax.legend(loc="lower right")
fig.savefig("strain_window_frequency.png", dpi=300)
