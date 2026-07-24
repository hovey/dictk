# dictk

Digital Image Correlation Toolkit

`dictk` is a Python library for digital image correlation (DIC) — comparing
images of a specimen before and after deformation to measure displacement
and strain fields.

This is an early-stage skeleton: a small, real, tested primitive
(zero-normalized cross-correlation) rather than a full DIC pipeline.

## Documentation

<table>
<tr>
<th>🚀 main (released)</th>
<th>🛠️ dev (in development)</th>
</tr>
<tr>
<td valign="top" align="center">

[![CI](https://github.com/hovey/dictk/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/hovey/dictk/actions/workflows/ci.yml?query=branch%3Amain)
<br>
[![Docs](https://img.shields.io/badge/docs-Pages-blueviolet)](https://hovey.github.io/dictk/main/dashboard/)&nbsp;
[![User Guide](https://img.shields.io/badge/docs-user%20guide-blue?logo=mdbook&logoColor=white)](https://hovey.github.io/dictk/main/)&nbsp;
[![API Docs](https://img.shields.io/badge/docs-API%20reference-blue?logo=python&logoColor=white)](https://hovey.github.io/dictk/main/api/dictk.html)
<br>
[![Coverage](https://hovey.github.io/dictk/main/badges/coverage.svg)](https://hovey.github.io/dictk/main/coverage/)&nbsp;
[![Lint](https://hovey.github.io/dictk/main/badges/lint.svg)](https://hovey.github.io/dictk/main/reports/lint/)

</td>
<td valign="top" align="center">

[![CI](https://github.com/hovey/dictk/actions/workflows/ci.yml/badge.svg?branch=dev)](https://github.com/hovey/dictk/actions/workflows/ci.yml?query=branch%3Adev)
<br>
[![Docs](https://img.shields.io/badge/docs-Pages-blueviolet)](https://hovey.github.io/dictk/dev/dashboard/)&nbsp;
[![User Guide](https://img.shields.io/badge/docs-user%20guide-orange?logo=mdbook&logoColor=white)](https://hovey.github.io/dictk/dev/)&nbsp;
[![API Docs](https://img.shields.io/badge/docs-API%20reference-orange?logo=python&logoColor=white)](https://hovey.github.io/dictk/dev/api/dictk.html)
<br>
[![Coverage](https://hovey.github.io/dictk/dev/badges/coverage.svg)](https://hovey.github.io/dictk/dev/coverage/)&nbsp;
[![Lint](https://hovey.github.io/dictk/dev/badges/lint.svg)](https://hovey.github.io/dictk/dev/reports/lint/)

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
