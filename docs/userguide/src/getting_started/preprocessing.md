# Image Preprocessing

Certain preprocessing steps can make digital image correlation more
robust to differences between a reference and current image — some in
pixel intensity, others in how well an image's content suits an
FFT-based technique such as phase correlation.

* [**Brightness and Contrast**](./brightness_contrast.md) shift and
  stretch the pixel-intensity histogram, the two most basic differences
  a reference and current image can have.
* [**Windowing**](./windowing.md) tapers an image's edges toward zero
  before a Fourier transform, reducing spectral leakage.
