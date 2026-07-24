# dictk

Digital Image Correlation Toolkit

`dictk` is a Python library for digital image correlation (DIC) — comparing
images of a specimen before and after deformation to measure displacement
and strain fields.

This is an early-stage skeleton: a small, real, tested primitive
(zero-normalized cross-correlation) rather than a full DIC pipeline.

## Documentation

Rebuilt on every push to its branch — `main` is the latest release,
`dev` is in-development preview:

<table>
<tr>
<th>🚀 main (released)</th>
<th>🛠️ dev (in development)</th>
</tr>
<tr>
<td valign="top">

- [![CI](https://github.com/hovey/dictk/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/hovey/dictk/actions/workflows/ci.yml?query=branch%3Amain)
- [Status dashboard](https://hovey.github.io/dictk/main/dashboard/)
- [User guide](https://hovey.github.io/dictk/main/)
- [API reference](https://hovey.github.io/dictk/main/api/dictk.html)
- [![Coverage](https://hovey.github.io/dictk/main/badges/coverage.svg)](https://hovey.github.io/dictk/main/coverage/)
- [![Lint](https://hovey.github.io/dictk/main/badges/lint.svg)](https://hovey.github.io/dictk/main/reports/lint/)

</td>
<td valign="top">

- [![CI](https://github.com/hovey/dictk/actions/workflows/ci.yml/badge.svg?branch=dev)](https://github.com/hovey/dictk/actions/workflows/ci.yml?query=branch%3Adev)
- [Status dashboard](https://hovey.github.io/dictk/dev/dashboard/)
- [User guide](https://hovey.github.io/dictk/dev/)
- [API reference](https://hovey.github.io/dictk/dev/api/dictk.html)
- [![Coverage](https://hovey.github.io/dictk/dev/badges/coverage.svg)](https://hovey.github.io/dictk/dev/coverage/)
- [![Lint](https://hovey.github.io/dictk/dev/badges/lint.svg)](https://hovey.github.io/dictk/dev/reports/lint/)

</td>
</tr>
</table>

[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blueviolet)](https://hovey.github.io/dictk/)

## Installation

```bash
pip install dictk
```

## Usage

```python
import numpy as np
from dictk import zero_normalized_cross_correlation

a = np.array([[1.0, 2.0], [3.0, 4.0]])
b = np.array([[2.0, 4.0], [6.0, 8.0]])

zero_normalized_cross_correlation(a, b)  # 1.0
```

## Development

This project uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
uv sync --all-extras --dev
uv run pytest --cov=src/dictk
uv run ruff format --check
uv run ruff check
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, testing,
docs, and release instructions.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
