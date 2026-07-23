# Image Generation

> The source for the commands on this page is `dictk`'s own `rosta`,
> `checkerboard`, and `astronaut` subcommands — see `dictk --help`.

> **Note:** the images embedded on this page are rendered as PNG
> (`--format png`), not `dictk`'s default TIFF. Browsers don't natively
> render TIFF in `<img>` tags, so a TIFF embedded here simply wouldn't
> display.
>
> Among the alternatives, PNG also wins on its own merits: it is
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

> **CLI vs. API:** the Command Line Interface (CLI) subcommands on this page
> (`dictk rosta`, `dictk checkerboard`, `dictk astronaut`) write an image
> file to disk — that's their whole job. The corresponding Python
> functions, [`dictk.rosta`](../api/dictk.html#rosta),
> [`dictk.checkerboard`](../api/dictk.html#checkerboard), and
> [`dictk.astronaut`](../api/dictk.html#astronaut), take the same
> parameters but perform no file I/O: they return a NumPy array only. That
> keeps the Python API composable in a functional style — arrays can be
> piped through further functions (e.g.
> [`combine_images`](../api/dictk/imaging.html#combine_images) below)
> before anything touches disk — and callers who do want a file call
> [`dictk.imaging.write_image`](../api/dictk/imaging.html#write_image)
> explicitly, as a separate step. See each function's docstring (rendered
> in the API reference) for details.

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

Note that the file name is automatically chosen based on the input parameters.

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
pattern, `dictk` can also generate a checkerboard test image.

The help text for `checkerboard`:

```sh
dictk checkerboard --help
```

returns

```text
<!-- cmdrun dictk checkerboard --help -->
```

Create a synthetic image, 200 by 200 pixels:

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

## Astronaut

Unlike `rosta` and `checkerboard`, which procedurally generate a fresh
synthetic pattern from parameters, `astronaut` loads a bundled real-world
photograph and converts it to grayscale — useful for exercising `dictk`'s
imaging utilities against something other than a synthetic pattern. The
source is a NASA portrait of astronaut Eileen Collins, from the NASA Great
Images database ("No known copyright restrictions, released into the
public domain."). Its native resolution is 512x512; passing `width`/
`height` other than that resizes the source image rather than generating a
new one at that size.

The help text for `astronaut`:

```sh
dictk astronaut --help
```

returns

```text
<!-- cmdrun dictk astronaut --help -->
```

Save it at 300 by 300 pixels — smaller downscales from the native 512x512
start to lose too much detail:

```sh
dictk astronaut 300 300 --format png -o .
```

```text
<!-- cmdrun dictk astronaut 300 300 --format png -o . -->
```

<figure>
    <img src="astronaut_300w_by_300h.png" alt="astronaut" />
    <figcaption>NASA portrait of astronaut Eileen Collins, resized to 300x300 pixels.</figcaption>
</figure>

The Python equivalent, again returning an array with no file written:

```python
import dictk

photo = dictk.astronaut(300, 300)
```

```text
<!-- cmdrun python3 -c "import dictk; photo = dictk.astronaut(300, 300); print(f'shape={photo.shape}, dtype={photo.dtype}')" -->
```

## Combining into a reference image

[`combine_images`](../api/dictk/imaging.html#combine_images) works on any
two grayscale images of the same shape, so it isn't limited to combining
the two synthetic images below —
[Speckle + Astronaut](#speckle--astronaut) further down combines `rosta`
with a real photograph instead.

### Speckle + Checkerboard

We combine the `rosta` speckle pattern with the checkerboard into a
**reference image** `checkerboard0` by averaging their pixel values and
normalizing back to `uint8`:

```python
from dictk.imaging import combine_images, read_image, write_image

speckle = read_image("rosta_200w_by_200h_dot_4.0_den_0.5_smo_2.0.png")
checker = read_image("checkerboard_200w_by_200h_8x8.png")
checkerboard0 = combine_images(speckle, checker)
write_image(checkerboard0, "checkerboard0.png")
```

```text
<!-- cmdrun python3 -c "from dictk.imaging import combine_images, read_image, write_image; speckle = read_image('rosta_200w_by_200h_dot_4.0_den_0.5_smo_2.0.png'); checker = read_image('checkerboard_200w_by_200h_8x8.png'); write_image(combine_images(speckle, checker), 'checkerboard0.png'); print('Saved image: checkerboard0.png')" -->
```

<figure>
    <img src="checkerboard0.png" alt="reference image checkerboard0" />
    <figcaption>Reference image checkerboard0, 200x200 pixels.</figcaption>
</figure>

Because both inputs are averaged and rescaled together, the checkerboard's
squares stay clearly black or white while the speckle pattern shows up as
gray texture within them:

- Where the checkerboard is black, speckle white maps to gray and speckle
  black stays black.
- Where the checkerboard is white, speckle black maps to gray and speckle
  white stays white.

That trimodal structure is visible in the pixel-intensity histograms below:
speckle and checkerboard are both roughly bimodal (dark/light), while
`checkerboard0` picks up a distinct middle hump from the
black/white-speckle-on-opposite checkerboard combinations.

```python
from dictk.imaging import read_image, save_histogram

speckle = read_image("rosta_200w_by_200h_dot_4.0_den_0.5_smo_2.0.png")
checker = read_image("checkerboard_200w_by_200h_8x8.png")
checkerboard0 = read_image("checkerboard0.png")

save_histogram(speckle, "rosta_histogram.png")
save_histogram(checker, "checkerboard_histogram.png")
save_histogram(checkerboard0, "checkerboard0_histogram.png")
```

```text
<!-- cmdrun python3 -c "from dictk.imaging import read_image, save_histogram; save_histogram(read_image('rosta_200w_by_200h_dot_4.0_den_0.5_smo_2.0.png'), 'rosta_histogram.png'); save_histogram(read_image('checkerboard_200w_by_200h_8x8.png'), 'checkerboard_histogram.png'); save_histogram(read_image('checkerboard0.png'), 'checkerboard0_histogram.png'); print('Saved histograms: rosta_histogram.png, checkerboard_histogram.png, checkerboard0_histogram.png')" -->
```

rosta | checkerboard | checkerboard0
--- | --- | ---
![rosta histogram](rosta_histogram.png) | ![checkerboard histogram](checkerboard_histogram.png) | ![checkerboard0 histogram](checkerboard0_histogram.png)

### Speckle + Astronaut

The checkerboard above is a stand-in for an actual specimen — in a real
DIC setup, the speckle pattern is applied directly to the surface being
measured, not swapped in from another generator. Combining `rosta` with
the `astronaut` photo instead of the checkerboard is closer to that: a
speckle pattern overlaid on a realistic, non-uniform grayscale image.

This time the two source images are never written to disk at all — both
[`dictk.rosta`](../api/dictk.html#rosta) and
[`dictk.astronaut`](../api/dictk.html#astronaut) return arrays directly,
which [`combine_images`](../api/dictk/imaging.html#combine_images) accepts
as-is, so only the combined result `astronaut0` is saved:

```python
import dictk
from dictk.imaging import combine_images, write_image

speckle = dictk.rosta(300, 300, density=0.5)
photo = dictk.astronaut(300, 300)
astronaut0 = combine_images(speckle, photo)
write_image(astronaut0, "astronaut0.png")
```

```text
<!-- cmdrun python3 -c "import dictk; from dictk.imaging import combine_images, write_image; speckle = dictk.rosta(300, 300, density=0.5); photo = dictk.astronaut(300, 300); astronaut0 = combine_images(speckle, photo); write_image(astronaut0, 'astronaut0.png'); print('Saved image: astronaut0.png')" -->
```

<figure>
    <img src="astronaut0.png" alt="reference image astronaut0: rosta speckle over the astronaut photo" />
    <figcaption>Reference image astronaut0: rosta speckle pattern combined with the astronaut photo, 300x300 pixels.</figcaption>
</figure>

Both `checkerboard0.png` and `astronaut0.png` are also bundled in
`src/dictk/data/`, alongside the source `astronaut.png`, so later examples
can reuse them without regenerating from scratch each time.
