# Slip Example

[Detection](./discontinuity_detection.md) and
[Localization](./discontinuity_localization.md) worked on a synthetic
crack and on one real crack image pair. This page introduces a second
real data set. It is a sequence of three images of one surface, labeled
t0, t1, and t2. In t2, a horizontal band crosses the image near row 700.

## Data Download

The three images below are real 1704x1500 8-bit grayscale micrographs.

<!-- cmdrun python3 -c "import hashlib, os, pathlib; files = ['slip_example_t0.tiff', 'slip_example_t1.tiff', 'slip_example_t2.tiff']; print('| File | Description | Size | SHA-256 |'); print('|---|---|---|---|'); [print(f'| [{f}]({f}) | {d} | {os.path.getsize(f) / 1024:.0f} KB | {hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()[:6]}... |') for f, d in zip(files, ['Reference configuration t0', 'Current configuration t1', 'Current configuration t2'])]" -->

```python
from dictk.image import read, write

for t in ["t0", "t1", "t2"]:
    write(
        arr=read(path=f"slip_example_{t}.tiff"),
        path=f"slip_example_{t}_preview.png",
    )
```

```text
<!-- cmdrun python3 -c "from dictk.image import read, write; suffixes = ['t0', 't1', 't2']; [write(arr=read(path=f'slip_example_{t}.tiff'), path=f'slip_example_{t}_preview.png') for t in suffixes]; print('Saved: ' + ', '.join(f'slip_example_{t}_preview.png' for t in suffixes))" -->
```

<figure id="fig-slip-example-sequence">
    <div class="figure-row">
        <div>
            <a href="slip_example_t0_preview.png" target="_blank" rel="noopener">
                <img src="slip_example_t0_preview.png" alt="t0: a speckled micrograph with no visible band" />
            </a>
            <span>(a)</span>
        </div>
        <div>
            <a href="slip_example_t1_preview.png" target="_blank" rel="noopener">
                <img src="slip_example_t1_preview.png" alt="t1: the same surface with no clearly visible band" />
            </a>
            <span>(b)</span>
        </div>
        <div>
            <a href="slip_example_t2_preview.png" target="_blank" rel="noopener">
                <img src="slip_example_t2_preview.png" alt="t2: the same surface with a horizontal band near row 700" />
            </a>
            <span>(c)</span>
        </div>
    </div>
    <figcaption>The slip example sequence, the images <a href="#data-download">downloaded above</a>. Click any panel for the full-size version. (a) t0. (b) t1. (c) t2, with a horizontal band near row 700.</figcaption>
</figure>

## Conventional DIC

We track t0 to t1 with `locate_warp` at the three kernel widths of
Bourdin et al. (2018), Fig. 4: 15, 31, and 45 px. A
`kernel_margin_width` of $m$ gives a kernel $2m + 1$ px wide. The three
kernels use margins of 7, 15, and 22 px.

### Search Margin

We first measure how far t1 moves relative to t0. A coarse grid of 56
points (`count_x=8`, `count_y=7`) tracks 200 px kernels with
`grid.locate`:

```python
<!-- cmdrun cat slip_example_motion.py -->
```

<!-- cmdrun python3 slip_example_motion.py -->

A kernel of 200 px holds hundreds of speckles, so its whole-pixel match
is reliable. No point moves more than 8 px in u or v. A search margin
of $s$ finds a point that moves up to $s$ px in any direction. The
search margin must also exceed the kernel margin, and the largest
kernel margin is 22 px. We use one search margin, 40 px, for all three
kernels. It reaches five times the largest measured motion.

### Grid Spacing

We space the grid points 10 px apart. That spacing is smaller than the
smallest kernel, 15 px, so neighboring kernels overlap at every kernel
size. Run time sets the lower limit. The second table under
[Results](#results) gives each kernel's wall time at 10 px. Bourdin et
al. use a 2 px step, which would track 25 times as many points and take
about 25 times as long.

### Points Tracked

The first grid point sits 50 px from the image's top and left edges.
That offset is the search margin plus one spacing, so every search area
stays inside the image. The same offset holds at the right and bottom
edges. The image is 1704 px wide and 1500 px tall. The grid counts are

$$
\begin{aligned}
n_x &= \left\lfloor \frac{1704 - 2 \cdot 50}{10} \right\rfloor + 1 = 161, \\
n_y &= \left\lfloor \frac{1500 - 2 \cdot 50}{10} \right\rfloor + 1 = 141,
\end{aligned}
$$

so the grid holds $161 \times 141 = 22701$ points.

### Results

The first table lists the machine that ran the tracking. Each kernel
spreads its points over one worker thread per logical CPU core. The
second table gives each kernel's points, its lost points, and its wall
time on that machine. A fit that diverges gets no displacement and
counts as lost:

<!-- cmdrun python3 slip_example_conventional.py -->

<figure id="fig-slip-example-conventional">
    <a href="slip_example_conventional.png" target="_blank" rel="noopener">
        <img src="slip_example_conventional.png" alt="six panels in three rows and two columns, u on the left and v on the right, one row per kernel width; top row, 15 px kernel, both fields a speckle of saturated red and blue squares with no visible pattern; middle row, 31 px kernel, a smooth gradient from blue at lower left to red at upper right under scattered saturated squares, densest in a vertical strip near x = 1200; bottom row, 45 px kernel, the same gradient almost free of scattered squares, crossed by sharp diagonal steps running from lower left to upper right" />
    </a>
    <figcaption>Conventional DIC from t0 to t1. Click for the full-size version. Left column: u. Right column: v. Rows: 15, 31, and 45 px kernels. Each column shares one color range. Black squares mark diverged fits. The 45 px kernel shows diagonal steps from lower left to upper right.</figcaption>
</figure>

> **Note:** We judge the 15, 31, and 45 px kernels in
> [Figure](#fig-slip-example-conventional) by eye. A visual check cannot
> flag one wild fit inside a smooth field. A numerical criterion should
> flag each garbage result instead, such as the ZNSSD gate of
> [Seed Propagation](./seed_propagation.md). The speckle pattern and the
> image resolution determine the kernel size. A kernel must hold enough
> speckles to match one position in the search area.

### `slip_example_conventional.py`

```python
<!-- cmdrun cat slip_example_conventional.py -->
```
