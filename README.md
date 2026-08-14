# dictk

Digital Image Correlation Toolkit

`dictk` is a Python library for digital image correlation (DIC) — comparing
images of a specimen before and after deformation to measure displacement
and strain fields.

This is an early-stage toolkit: currently synthetic image generation,
preprocessing, and transformation utilities for building DIC test data,
with point-tracking (registration) under active development.

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
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blueviolet?style=flat)](https://hovey.github.io/dictk/main/dashboard/)&nbsp;
[![User Guide](https://img.shields.io/badge/docs-user%20guide-blue?logo=mdbook&logoColor=white&style=flat)](https://hovey.github.io/dictk/main/)&nbsp;
[![API Docs](https://img.shields.io/badge/docs-API%20reference-blue?logo=python&logoColor=white&style=flat)](https://hovey.github.io/dictk/main/api/dictk.html)
<br>
[![Tests](https://hovey.github.io/dictk/main/badges/tests.svg)](https://github.com/hovey/dictk/actions/workflows/ci.yml?query=branch%3Amain)&nbsp;
[![Coverage](https://hovey.github.io/dictk/main/badges/coverage.svg)](https://hovey.github.io/dictk/main/coverage/)&nbsp;
[![Lint](https://hovey.github.io/dictk/main/badges/lint.svg)](https://hovey.github.io/dictk/main/reports/lint/)

</td>
<td valign="top" align="center">

[![CI](https://github.com/hovey/dictk/actions/workflows/ci.yml/badge.svg?branch=dev)](https://github.com/hovey/dictk/actions/workflows/ci.yml?query=branch%3Adev)
<br>
[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blueviolet?style=flat)](https://hovey.github.io/dictk/dev/dashboard/)&nbsp;
[![User Guide](https://img.shields.io/badge/docs-user%20guide-orange?logo=mdbook&logoColor=white&style=flat)](https://hovey.github.io/dictk/dev/)&nbsp;
[![API Docs](https://img.shields.io/badge/docs-API%20reference-orange?logo=python&logoColor=white&style=flat)](https://hovey.github.io/dictk/dev/api/dictk.html)
<br>
[![Tests](https://hovey.github.io/dictk/dev/badges/tests.svg)](https://github.com/hovey/dictk/actions/workflows/ci.yml?query=branch%3Adev)&nbsp;
[![Coverage](https://hovey.github.io/dictk/dev/badges/coverage.svg)](https://hovey.github.io/dictk/dev/coverage/)&nbsp;
[![Lint](https://hovey.github.io/dictk/dev/badges/lint.svg)](https://hovey.github.io/dictk/dev/reports/lint/)

</td>
</tr>
</table>

[![Docs](https://img.shields.io/badge/docs-GitHub%20Pages-blueviolet?style=flat)](https://hovey.github.io/dictk/)

## Installation

```bash
pip install dictk
```

## Usage

```python
from dictk import checkerboard

image = checkerboard(width=200, height=200, count_x=8, count_y=8)
image.shape  # (200, 200)
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
