# Image Generation

> The source for the commands on this page is `dictk`'s own `rosta` and
> `checkerboard` subcommands — see `dictk --help`.

> **Note:** the images embedded on this page are rendered as PNG
> (`--format png`), not `dictk`'s default TIFF. Browsers don't natively
> render TIFF in `<img>` tags, so a TIFF embedded here simply wouldn't
> display.
>
> Among the alternatives, PNG also wins on its own merits: it's
> lossless, whereas JPG's compression tends to smear hard edges and
> speckle-pattern detail (for the 200x200 checkerboard on this page: TIFF
> 40,256 bytes, JPG 6,760 bytes, PNG only 418 bytes — JPG is actually
> *larger* than PNG here, because its block-based compression is a poor
> fit for hard-edged content like a checkerboard). SVG doesn't help either:
> since there's no vector structure to trace, `dictk`'s SVG output just
> wraps that same PNG in a base64-encoded XML container, which comes out
> to 809 bytes here — roughly double the raw PNG for no rendering benefit.
>
> TIFF remains `dictk`'s command-line default, since it's the lossless,
> uncompressed format conventionally used for DIC and other
> scientific-imaging workflows.

> **CLI vs. API:** the subcommands on this page (`dictk rosta`,
> `dictk checkerboard`) write an image file to disk — that's their whole
> job. The corresponding Python functions, `dictk.rosta` and
> `dictk.checkerboard`, take the same parameters but perform no file I/O:
> they return a NumPy array only. That keeps the Python API composable in
> a functional style — arrays can be piped through further functions
> (e.g. `combine_images` below) before anything touches disk — and callers
> who do want a file call `dictk.imaging.write_image` explicitly, as a
> separate step. See each function's docstring (rendered in the API
> reference) for details.

## Rosta

We create a synthetic example speckle pattern with the built-in `rosta`
image generator. It implements the Rosta algorithm described by
[Olufsen](https://doi.org/10.1016/j.softx.2019.100391) (Olufsen SN,
Andersen ME, Fagerholt E. *muDIC: An open-source toolkit for digital image
correlation.* SoftwareX. 2020 Jan 1;11:100391, Algorithm 1, page 6,
[repository](https://github.com/PolymerGuy/muDIC)).

The help text for `rosta`:

```sh
dictk rosta --help
```

returns

```text
<!-- cmdrun dictk rosta --help -->
```

Create a synthetic image, 200 by 200 pixels, 50% dot density:

```sh
dictk rosta 200 200 --density 0.5 --format png -o .
```

```text
<!-- cmdrun dictk rosta 200 200 --density 0.5 --format png -o . -->
```

The result:

<figure>
    <img src="rosta_200w_by_200h_dot_4.0_den_0.5_smo_2.0.png"
    alt="rosta speckle pattern" />
    <figcaption>Synthetic speckle pattern, 200x200 pixels.</figcaption>
</figure>

The Python equivalent returns the same pixel data as a NumPy array, with no
file written:

```python
import dictk

pattern = dictk.rosta(200, 200, density=0.5)
```

```text
<!-- cmdrun python3 -c "import dictk; pattern = dictk.rosta(200, 200, density=0.5); print(f'shape={pattern.shape}, dtype={pattern.dtype}')" -->
```

## Checkerboard

To make it easier to manually identify discrete points in the speckle
pattern, `dictk` can also generate a checkerboard test image:

```sh
dictk checkerboard 200 200 --format png -o .
```

```text
<!-- cmdrun dictk checkerboard 200 200 --format png -o . -->
```

<figure>
    <img src="checkerboard_200w_by_200h_8x8.png" alt="checkerboard" />
    <figcaption>Checkerboard test image, 200x200 pixels, 8x8 squares.</figcaption>
</figure>

The Python equivalent, again returning an array with no file written:

```python
import dictk

board = dictk.checkerboard(200, 200)
```

```text
<!-- cmdrun python3 -c "import dictk; board = dictk.checkerboard(200, 200); print(f'shape={board.shape}, dtype={board.dtype}')" -->
```

## Combining into a reference image

We combine the `rosta` speckle pattern with the checkerboard into a
**reference image** `i0` by averaging their pixel values and normalizing
back to `uint8`:

```python
from dictk.imaging import combine_images, read_image, write_image

speckle = read_image("rosta_200w_by_200h_dot_4.0_den_0.5_smo_2.0.png")
checker = read_image("checkerboard_200w_by_200h_8x8.png")
i0 = combine_images(speckle, checker)
write_image(i0, "i0.png")
```

```text
<!-- cmdrun python3 -c "from dictk.imaging import combine_images, read_image, write_image; speckle = read_image('rosta_200w_by_200h_dot_4.0_den_0.5_smo_2.0.png'); checker = read_image('checkerboard_200w_by_200h_8x8.png'); write_image(combine_images(speckle, checker), 'i0.png'); print('Saved image: i0.png')" -->
```

<figure>
    <img src="i0.png" alt="reference image i0" />
    <figcaption>Reference image i0, 200x200 pixels.</figcaption>
</figure>

Because both inputs are averaged and rescaled together, the checkerboard's
squares stay clearly black or white while the speckle pattern shows up as
gray texture within them:

- Where the checkerboard is black, speckle white maps to gray and speckle
  black stays black.
- Where the checkerboard is white, speckle black maps to gray and speckle
  white stays white.

That trimodal structure is visible in the pixel-intensity histograms below:
speckle and checkerboard are both roughly bimodal (dark/light), while `i0`
picks up a distinct middle hump from the black/white-speckle-on-opposite
checkerboard combinations.

```text
<!-- cmdrun python3 -c "from dictk.imaging import read_image, save_histogram; save_histogram(read_image('rosta_200w_by_200h_dot_4.0_den_0.5_smo_2.0.png'), 'rosta_histogram.png'); save_histogram(read_image('checkerboard_200w_by_200h_8x8.png'), 'checkerboard_histogram.png'); save_histogram(read_image('i0.png'), 'i0_histogram.png'); print('Saved histograms: rosta_histogram.png, checkerboard_histogram.png, i0_histogram.png')" -->
```

rosta | checkerboard | i0
--- | --- | ---
![rosta histogram](rosta_histogram.png) | ![checkerboard histogram](checkerboard_histogram.png) | ![i0 histogram](i0_histogram.png)
