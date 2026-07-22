# Contributing to dictk

## Getting the source code

```bash
git clone git@github.com:hovey/dictk.git
cd dictk
```

## Installation

### Using `uv` (recommended)

Install [uv](https://docs.astral.sh/uv/) if you don't already have it:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# or via Homebrew
brew install uv
```

Then, from the repository root:

```bash
uv sync --all-extras --dev
```

This creates a `.venv` and installs `dictk` plus its dev dependencies
(`pytest`, `pytest-cov`, `ruff`). Run commands inside that environment with
the `uv run` prefix, e.g. `uv run pytest`.

### Using `venv` and `pip` (alternative)

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Development workflow

### Running tests

```bash
uv run pytest
```

With coverage (matches what CI runs):

```bash
uv run pytest --cov=src/dictk --cov-report=xml --cov-report=html
```

Coverage HTML report is written to `htmlcov/index.html`.

### Linting and formatting

[ruff](https://docs.astral.sh/ruff/) handles both formatting and linting.

```bash
uv run ruff format          # auto-format
uv run ruff format --check  # verify formatting without changing files (CI runs this)
uv run ruff check           # lint
```

### Building the docs

Documentation is an [mdBook](https://rust-lang.github.io/mdBook/) under
`docs/userguide/`. Building it requires the `mdbook` binary (not a Python
dependency):

```bash
# macOS
brew install mdbook

# or via cargo
cargo install mdbook
```

```bash
mdbook build docs/userguide          # build once, output in docs/userguide/book/
mdbook serve docs/userguide          # live preview at http://localhost:3000
```

### Before pushing

There's no `preflight` command yet (see rattlesnake-vibration-controller's
`preflight.py` for an example of what that could grow into) — for now, run
the checks manually:

```bash
uv run ruff format --check
uv run ruff check
uv run pytest --cov=src/dictk
mdbook build docs/userguide
```

These are exactly the checks the `test` and `docs` jobs run in CI.

## CI/CD architecture

Everything lives in a single workflow, `.github/workflows/ci.yml`, with
three jobs:

- **`test`** — runs on every push and pull request. Installs dependencies
  with `uv sync`, runs `uv build` as a build sanity check, `ruff format
  --check`, `ruff check`, and `pytest --cov`. Uploads the coverage report as
  a build artifact.
- **`docs`** — runs only on pushes to `main`, after `test` passes. Builds
  the mdBook user guide and deploys it to the `gh-pages` branch (published
  via GitHub Pages).
- **`release`** — runs only on pushes to `main`, after `test` passes, and
  only if the pushed commit's message contains `[testpypi]` or `[pypi]`.
  Publishes the built package to TestPyPI or PyPI respectively. See
  "Releasing" below.

This is intentionally a minimal setup — no matrix OS/Python testing, no
containerized builds, no lint/coverage badge generation, no dashboard page.
pytribeam's `ci.yml` and rattlesnake-vibration-controller's `ci.yml`/
`release.yml` are useful references for growing any of this out later.

## Versioning

Versions are derived automatically from git tags via
[hatch-vcs](https://github.com/ofek/hatch-vcs) — there is no hand-maintained
version string anywhere in the source. Tag format is a `v`-prefixed
[PEP 440](https://peps.python.org/pep-0440/) version, e.g. `v0.1.0`.

If the current commit isn't exactly at a tag (or the working tree is dirty),
`hatch-vcs` appends a local version segment (e.g. `0.1.dev1+gd975d09`).
**PyPI and TestPyPI reject uploads with a local version segment**, so a
publishable commit must be exactly the tagged commit.

## Releasing

Releases are triggered by pushing a commit to `main` whose message contains
a keyword — `[testpypi]` for a TestPyPI release, `[pypi]` for a real PyPI
release. If a commit message contains both, `[pypi]` takes priority. Because
the release job builds whatever `hatch-vcs` resolves at that commit, the tag
for the version you want to publish must point at that exact commit.

### One-time setup (already done for this repo)

1. GitHub → repo Settings → Environments: create `testpypi` and `pypi`
   environments. (Optional but recommended: add "Required reviewers" on the
   `pypi` environment so a real release needs manual approval before
   publishing — TestPyPI doesn't need this.)
2. On [test.pypi.org](https://test.pypi.org) and
   [pypi.org](https://pypi.org), under the `dictk` project's "Publishing"
   settings, add a trusted publisher: owner `hovey`, repository `dictk`,
   workflow file `ci.yml`, environment name `testpypi` (for TestPyPI) or
   `pypi` (for PyPI).

No API tokens are stored anywhere — publishing uses OIDC trusted publishing
via the `id-token: write` permission.

### Publishing a release

```bash
# Make sure your working tree is clean and you're on main, up to date
git checkout main
git pull

# Commit the release (an empty commit is fine if there's nothing else to land)
git commit --allow-empty -m "chore: release v0.1.0 [testpypi]"

# Tag that exact commit
git tag v0.1.0

# Push the tag before the branch, so it's visible when CI checks out the repo
git push origin v0.1.0
git push origin main
```

Watch the Actions tab: `test` → `release` job, under the `testpypi`
environment. Once it succeeds, check
`https://test.pypi.org/project/dictk/` for the new version.

For a real PyPI release, repeat with `[pypi]` instead of `[testpypi]` and a
new tag/version (PyPI and TestPyPI are independent indexes, but reusing a
version number across a test and a real release invites confusion — prefer
a fresh version, e.g. `v0.1.1`, for the real release):

```bash
git commit --allow-empty -m "chore: release v0.1.1 [pypi]"
git tag v0.1.1
git push origin v0.1.1
git push origin main
```

Uploads to PyPI (and TestPyPI) are permanent — a given version's files can
never be re-uploaded or deleted, only "yanked". Prefer testing on TestPyPI
first, as with `v0.1.0` above, before publishing the same content to PyPI.
