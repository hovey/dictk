# Introduction

`dictk` (Digital Image Correlation Toolkit) is a Python library for digital
image correlation (DIC) — comparing images of a specimen before and after
deformation to measure displacement and strain fields.

This guide is a work in progress. For now, it covers the one primitive the
toolkit ships with.

## Installation

```bash
pip install dictk
```

## Getting started

`dictk` currently provides a single building block: zero-normalized
cross-correlation (ZNCC), the similarity metric DIC template matching is
built on.

```python
import numpy as np
from dictk import zero_normalized_cross_correlation

a = np.array([[1.0, 2.0], [3.0, 4.0]])
b = np.array([[2.0, 4.0], [6.0, 8.0]])

score = zero_normalized_cross_correlation(a, b)
print(score)  # 1.0 -- correlated up to a brightness/contrast rescale
```
