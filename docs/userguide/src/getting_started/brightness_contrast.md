# Brightness and Contrast

This page covers two preprocessing steps that can make digital image
correlation more robust to pixel-intensity differences between a
reference and deformed image, using the [astronaut reference
image](./image_generation.md#astronaut) from Image Generation as an
example.

## Brightness

[**Brightness**](../api/dictk/image.html#brightness) shifts the entire
pixel-intensity histogram up or down by a constant amount — the whole
image gets lighter or darker together, dark areas included. Pushed too
far, dark regions wash out to a flat gray and highlights clip at pure
white (255), permanently losing detail.

```python
import dictk
from dictk.image import brightness, histogram_save, write

photo = dictk.astronaut(width=300, height=300)
write(arr=photo, path="astronaut_original.png")
histogram_save(arr=photo, path="astronaut_original_histogram.png")

bright_1_5 = brightness(arr=photo, factor=1.5)
write(arr=bright_1_5, path="astronaut_brightness_1.5.png")
histogram_save(arr=bright_1_5, path="astronaut_brightness_1.5_histogram.png")

bright_2_0 = brightness(arr=photo, factor=2.0)
write(arr=bright_2_0, path="astronaut_brightness_2.0.png")
histogram_save(arr=bright_2_0, path="astronaut_brightness_2.0_histogram.png")
```

```text
<!-- cmdrun python3 -c "import dictk; from dictk.image import brightness, histogram_save, write; photo = dictk.astronaut(width=300, height=300); write(arr=photo, path='astronaut_original.png'); histogram_save(arr=photo, path='astronaut_original_histogram.png'); bright_1_5 = brightness(arr=photo, factor=1.5); write(arr=bright_1_5, path='astronaut_brightness_1.5.png'); histogram_save(arr=bright_1_5, path='astronaut_brightness_1.5_histogram.png'); bright_2_0 = brightness(arr=photo, factor=2.0); write(arr=bright_2_0, path='astronaut_brightness_2.0.png'); histogram_save(arr=bright_2_0, path='astronaut_brightness_2.0_histogram.png'); print('Saved: astronaut_original.png, astronaut_brightness_1.5.png, astronaut_brightness_2.0.png')" -->
```

factor=1.0 (original) | factor=1.5 | factor=2.0
--- | --- | ---
![original](astronaut_original.png) | ![brightness 1.5](astronaut_brightness_1.5.png) | ![brightness 2.0](astronaut_brightness_2.0.png)

factor=1.0 (original) | factor=1.5 | factor=2.0
--- | --- | ---
![original histogram](astronaut_original_histogram.png) | ![brightness 1.5 histogram](astronaut_brightness_1.5_histogram.png) | ![brightness 2.0 histogram](astronaut_brightness_2.0_histogram.png)

At factor=1.5 the histogram shifts right as a whole — midtones move into
the brighter half and the mean climbs, with a few highlights starting to
clip at 255. At factor=2.0 the shift is large enough that a big share of
pixels pile up at that 255 ceiling, visible as a tall spike at the
histogram's right edge: real detail that's been clipped away and can't be
recovered.

## Contrast

[**Contrast**](../api/dictk/image.html#contrast) is the spread between
an image's darkest and lightest pixels. Increasing contrast stretches the
histogram outward from its own mean — darks get darker, lights get
lighter — while the mean itself stays roughly
where it was.

```python
import dictk
from dictk.image import contrast, histogram_save, write

photo = dictk.astronaut(width=300, height=300)

contrast_1_5 = contrast(arr=photo, factor=1.5)
write(arr=contrast_1_5, path="astronaut_contrast_1.5.png")
histogram_save(arr=contrast_1_5, path="astronaut_contrast_1.5_histogram.png")

contrast_2_0 = contrast(arr=photo, factor=2.0)
write(arr=contrast_2_0, path="astronaut_contrast_2.0.png")
histogram_save(arr=contrast_2_0, path="astronaut_contrast_2.0_histogram.png")
```

```text
<!-- cmdrun python3 -c "import dictk; from dictk.image import contrast, histogram_save, write; photo = dictk.astronaut(width=300, height=300); contrast_1_5 = contrast(arr=photo, factor=1.5); write(arr=contrast_1_5, path='astronaut_contrast_1.5.png'); histogram_save(arr=contrast_1_5, path='astronaut_contrast_1.5_histogram.png'); contrast_2_0 = contrast(arr=photo, factor=2.0); write(arr=contrast_2_0, path='astronaut_contrast_2.0.png'); histogram_save(arr=contrast_2_0, path='astronaut_contrast_2.0_histogram.png'); print('Saved: astronaut_contrast_1.5.png, astronaut_contrast_2.0.png')" -->
```

factor=1.0 (original) | factor=1.5 | factor=2.0
--- | --- | ---
![original](astronaut_original.png) | ![contrast 1.5](astronaut_contrast_1.5.png) | ![contrast 2.0](astronaut_contrast_2.0.png)

factor=1.0 (original) | factor=1.5 | factor=2.0
--- | --- | ---
![original histogram](astronaut_original_histogram.png) | ![contrast 1.5 histogram](astronaut_contrast_1.5_histogram.png) | ![contrast 2.0 histogram](astronaut_contrast_2.0_histogram.png)

At factor=1.5 the histogram spreads outward from the mean rather than
shifting — the astronaut's silhouette and helmet edges get sharper, while
the mean barely moves. At factor=2.0 the spread is wide enough that more
pixels pile up at both the 0 and 255 ends, crushing fine midtone detail
even as high-contrast edges sharpen further.

> **Key Insight:** Contrast stretches the histogram, while brightness
> translates it.
