# dictk

[![CI](https://github.com/hovey/dictk/actions/workflows/ci.yml/badge.svg)](https://github.com/hovey/dictk/actions/workflows/ci.yml)
[![Dashboard](https://img.shields.io/badge/status-dashboard-lightgrey)](https://hovey.github.io/dictk/main/dashboard/)
[![Docs](https://img.shields.io/badge/docs-user%20guide-blue)](https://hovey.github.io/dictk/main/)
[![API](https://img.shields.io/badge/docs-API%20reference-blue)](https://hovey.github.io/dictk/main/api/dictk.html)
[![Coverage](https://hovey.github.io/dictk/main/badges/coverage.svg)](https://hovey.github.io/dictk/main/coverage/)
[![Lint](https://hovey.github.io/dictk/main/badges/lint.svg)](https://hovey.github.io/dictk/main/reports/lint/)

Digital Image Correlation Toolkit

`dictk` is a Python library for digital image correlation (DIC) — comparing
images of a specimen before and after deformation to measure displacement
and strain fields.

This is an early-stage skeleton: a small, real, tested primitive
(zero-normalized cross-correlation) rather than a full DIC pipeline.

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

Documentation (mdBook) lives in `docs/userguide/` and is published at
https://hovey.github.io/dictk/main/ on every push to `main` (and at
https://hovey.github.io/dictk/dev/ on every push to `dev`, for previewing
in-development docs). The Python API reference is generated from docstrings
with [pdoc](https://pdoc.dev/) and published alongside it at
https://hovey.github.io/dictk/main/api/dictk.html. The full HTML coverage
report from the same run is published at
https://hovey.github.io/dictk/main/coverage/. The lint badge's score comes
from [pylint](https://pylint.readthedocs.io/), run informationally alongside
[ruff](https://docs.astral.sh/ruff/) (which actually gates CI); its full
report is published at https://hovey.github.io/dictk/main/reports/lint/. All
of the above are linked from one status dashboard at
https://hovey.github.io/dictk/main/dashboard/, and both versions are linked
from the site root at https://hovey.github.io/dictk/. See
[CONTRIBUTING.md](CONTRIBUTING.md#building-the-docs) for the exact
(version-pinned) build instructions.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, testing,
docs, and release instructions.

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
