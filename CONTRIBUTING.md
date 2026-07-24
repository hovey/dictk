# Contributing to dictk

dictk is developed on [GitHub](https://github.com/hovey/dictk) using
[Git](https://git-scm.com/) for version control. Git is the tool that tracks
changes to the source on your own computer; GitHub is the hosting service
that holds the canonical copy of the repository, tracks issues and pull
requests, and runs the CI/CD pipeline described below.

## Cloning vs. forking

Contributors can get a working copy of dictk by either cloning or forking
the repository. Cloning is a Git action: it creates a copy of the
repository on your own computer. Forking is a GitHub action: it creates a
personal copy of the entire project under your own GitHub account.

**Cloning** is for authorized collaborators who can push changes directly
to the main project. **Forking** lets external contributors make changes
without affecting the original repository, then submit a pull request to
share those changes.

## Getting the source code

Collaborators should clone directly:

```bash
git clone git@github.com:hovey/dictk.git
cd dictk
```

External contributors should first fork the repository to their own GitHub
account, then clone their fork locally.

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

## Git workflow

### Branching model

`main` and `dev` are both long-lived: `dev` is branched from `main`, and
`main` only moves forward via merges from `dev` (each push to `main` is a
potential release — see "Releasing" below). Actual development happens one
level further out, on `dev-feature`, a branch cut from `dev`.

```
main          ●───────────────●───────────  (releases only, tagged)
                   \                \
dev           ●─────●───●───●───●────●────  (integration branch)
               \       \         \
dev-feature     ●───●   ●─●───●   ●──●      (your work)
```

### Starting a dev-feature branch

```bash
git checkout dev
git pull origin dev
git checkout -b dev-feature
```

### Keeping your dev-feature branch up to date with `dev`

Before opening a PR, or periodically during long-lived work, bring in `dev`'s
latest changes.

**Option 1: Merge** (safer, keeps history of both branches)

```bash
git checkout dev
git pull origin dev
git checkout dev-feature
git merge dev
```

If there are conflicts, git will tell you which files — resolve them, then:

```bash
git add <resolved-files>
git commit
```

**Option 2: Rebase** (cleaner, linear history)

```bash
git checkout dev
git pull origin dev
git checkout dev-feature
git rebase dev
```

If conflicts come up during rebase, fix them then run `git add <files>`
followed by `git rebase --continue` (repeat until done). To bail out at any
point: `git rebase --abort`.

**Pushing after either approach** — if `dev-feature` was already pushed and
has commits others might be using:

- After a **merge**: `git push origin dev-feature`
- After a **rebase**: `git push origin dev-feature --force-with-lease`
  (rebase rewrites history, so you need a force push — `--force-with-lease`
  is safer than `--force` since it won't overwrite someone else's pushed
  work)

**Which to pick** — use merge if the branch is shared with others or you want
a clear record of when `dev`'s changes came in; use rebase if it's mostly
just your own branch and you want a clean, linear commit history without
merge bubbles.

**Tip** — before doing either, it's worth running:

```bash
git log dev-feature..dev --oneline
```

to preview what's coming in, so conflicts aren't a total surprise.

### Releasing: merging `dev` into `main`

`main` is a protected branch — it only accepts changes through a merged pull
request, even for repo admins, so `git push origin main` will be rejected.
Once `dev` is ready to ship, open a PR from `dev` into `main` and merge it:

```bash
git checkout dev
git pull origin dev
gh pr create --base main --head dev --title "Merge dev into main" --body ""
gh pr merge --merge
```

(No approving review is required, so you can merge your own PR.) Merging
doesn't publish anything by itself — a push to `main` also needs a commit
message containing `[testpypi]` or `[pypi]` to trigger the `release` job (see
"Releasing" below). That keyword can be in the PR's merge commit message, or
in a follow-up release commit on `main` as described there.

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
`docs/userguide/`, with the
[mdbook-cmdrun](https://github.com/FauconFan/mdbook-cmdrun) preprocessor
enabled so pages can embed live, always-accurate command output (see the
"Image Generation" page for an example) instead of pasted-by-hand output.
Neither is a Python dependency:

```bash
# mdbook must be pinned to 0.4.52: mdbook-cmdrun depends on the mdbook
# crate's 0.4.x preprocessor JSON schema, which changed in mdbook 0.5 and
# broke compatibility (https://github.com/FauconFan/mdbook-cmdrun/issues/22,
# open as of this writing). Do not `brew install mdbook` or
# `cargo install mdbook` without a --version pin, or cmdrun pages will fail
# to build with "Unable to parse the input".
cargo install mdbook --version 0.4.52
cargo install mdbook-cmdrun
```

If you already have a newer `mdbook` from Homebrew or elsewhere on your
`PATH`, make sure `~/.cargo/bin` comes first (or check `mdbook --version`
reports `0.4.52` before building).

```bash
# mdbook-cmdrun resolves each cmdrun command's working directory relative
# to the process's cwd, so you must `cd` into docs/userguide first — running
# `mdbook build docs/userguide` from the repo root will fail with
# "Fail to run shell".
cd docs/userguide
uv run mdbook build           # build once, output in docs/userguide/book/
uv run mdbook serve           # live preview at http://localhost:3000
```

`uv run` puts dictk's own CLI on `PATH` for the build, since some
`cmdrun` directives invoke `dictk` directly.

### Building the API docs

Python API reference docs (function signatures, docstrings) are generated
from source with [pdoc](https://pdoc.dev/), a dev dependency:

```bash
uv run pdoc dictk dictk.core dictk.imaging dictk.cli -o docs/api
```

`dictk.rosta` doesn't need to be listed explicitly — pdoc's submodule
discovery respects a package's `__all__`, and `rosta` is exported there (see
below), so it's picked up automatically. The other submodules (`core`,
`imaging`, `cli`) aren't in `__all__` — `dictk/__init__.py` only lists the
individual functions it re-exports, not module names — so pdoc's automatic
package walk skips them unless named explicitly on the command line, per
[pdoc's `__all__` handling](https://pdoc.dev/docs/pdoc.html#what-objects-are-documented). If you add a new top-level submodule, add it to this
command too, or it will silently go undocumented.

```bash
uv run pdoc dictk dictk.core dictk.imaging dictk.cli   # live preview, serves on localhost
```

Output goes to `docs/api/` (gitignored, regenerated on demand). CI builds
this too and publishes it alongside the mdBook user guide — see "CI/CD
architecture" below.

### Building the coverage badge

The README's coverage badge is a real SVG generated from `coverage.xml` with
[genbadge](https://smarie.github.io/python-genbadge/), a dev dependency —
not a static label:

```bash
uv run pytest --cov=src/dictk --cov-report=xml --cov-report=html
uv run genbadge coverage -i coverage.xml -o coverage-badge.svg
```

In CI this runs in the `docs` job (not `test`) using the coverage.xml
produced by the `test` job's `report-coverage` artifact, so the badge only
updates on pushes to `main` — same cadence as the Docs and API badges, not
per-PR. Both `coverage-badge.svg` and the full `htmlcov/` report are staged
into the deployed site (`/badges/coverage.svg` and `/coverage/`
respectively) — see "CI/CD architecture" below.

### Running pylint (informational)

ruff (`ruff format --check` and `ruff check`) is what actually gates CI —
see "Linting and formatting" above. [pylint](https://pylint.readthedocs.io/)
also runs, but only in the `docs` job, and only informationally: it can't
fail the build. It exists purely because ruff has no equivalent of pylint's
`Your code has been rated at X.XX/10` score, and the README's lint badge
wants a score, not just a pass/fail (which the CI badge already covers).
Since pylint and ruff check overlapping-but-different rule sets, expect
pylint to flag a few things ruff doesn't (and vice versa) — that's expected
duplication from running two linters, not a bug in either.

```bash
uv run pylint src/dictk --output-format=text --reports=yes > pylint-report.txt
uv run python .github/scripts/render_pylint_report.py \
  --input pylint-report.txt --output pylint-report.html
```

The badge itself is built by extracting the score from that output and
requesting a matching badge from shields.io — see the "Run pylint
(informational) and generate lint badge/report" step in `ci.yml` for the
exact score-extraction and color-threshold logic. `pylint-report.html` is
staged into the deployed site at `/reports/lint/`, and the badge at
`/badges/lint.svg` — same cadence as the other gh-pages badges (updates on
pushes to `main` only).

### Building the status dashboard

`/dashboard/` on the deployed site is a single page linking every badge and
report above, generated by `.github/scripts/render_dashboard.py`. It exists
because the mdBook user guide occupies the site root, so there's no natural
landing page that lists the API reference, coverage report, and lint report
together — rather than expecting visitors to already know those paths, or
scattering the links across the README only. It doesn't require any of the
other artifacts to already exist locally (it only generates links to them,
using paths relative to `/dashboard/`, e.g. `../coverage/`):

```bash
uv run python .github/scripts/render_dashboard.py \
  --github-repo hovey/dictk \
  --run-id local \
  --sha "$(git rev-parse HEAD)" \
  --ref-name "$(git rev-parse --abbrev-ref HEAD)" \
  --timestamp "$(date -u +'%Y-%m-%d %H:%M:%S UTC')" \
  --output dashboard.html
```

In CI, `${{ github.run_id }}`, `${{ github.sha }}`, and `${{ github.ref_name }}`
fill in the run metadata instead. `dashboard.html` is staged into the
deployed site at `/dashboard/`.

### Before pushing

There's no `preflight` command yet (see rattlesnake-vibration-controller's
`preflight.py` for an example of what that could grow into) — for now, run
the checks manually:

```bash
uv run ruff format --check
uv run ruff check
uv run pytest --cov=src/dictk --cov-report=xml --cov-report=html
(cd docs/userguide && uv run mdbook build)
uv run pdoc dictk dictk.core dictk.imaging dictk.cli -o docs/api
uv run genbadge coverage -i coverage.xml -o coverage-badge.svg
uv run pylint src/dictk --output-format=text --reports=yes
```

These are exactly the checks the `test` and `docs` jobs run in CI.

## CI/CD architecture

Everything lives in a single workflow, `.github/workflows/ci.yml`, with
three jobs:

- **`test`** — runs on every push and pull request. Installs dependencies
  with `uv sync`, runs `uv build` as a build sanity check, `ruff format
  --check`, `ruff check`, and `pytest --cov`. Uploads the coverage report as
  a build artifact.
- **`docs`** — runs only on pushes to `main`, after `test` passes. Installs
  the pinned `mdbook` 0.4.52 and `mdbook-cmdrun` (cached via
  `actions/cache`), downloads the `test` job's coverage artifact, builds the
  mdBook user guide with dictk's own CLI on `PATH`, builds the pdoc API
  reference, generates a coverage badge from `coverage.xml` with
  [genbadge](https://smarie.github.io/python-genbadge/), runs pylint
  informationally to get a 0-10 score (fetched as a shields.io badge) and a
  full findings report, renders a status dashboard linking all of the above,
  stages all of it into one directory (user guide at the root, API reference
  under `/api/`, badges under `/badges/coverage.svg` and `/badges/lint.svg`,
  full HTML coverage report under `/coverage/`, full pylint report under
  `/reports/lint/`, dashboard under `/dashboard/`), and deploys the combined
  site to the `gh-pages` branch (published via GitHub Pages). Everything is
  staged together because `peaceiris/actions-gh-pages` replaces the whole
  `publish_dir` on each deploy — publishing pieces separately would have
  each deploy wipe out the last.
- **`release`** — runs only on pushes to `main`, after `test` passes, and
  only if the pushed commit's message contains `[testpypi]` or `[pypi]`.
  Publishes the built package to TestPyPI or PyPI respectively. See
  "Releasing" below.

This is intentionally a minimal setup — no matrix OS/Python testing, no
containerized builds, no lint badge or dashboard page. pytribeam's `ci.yml`
and rattlesnake-vibration-controller's `ci.yml`/`release.yml` are useful
references for growing any of this out later.

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

`main` is protected, so the release commit has to land via a merged PR
rather than a direct push:

```bash
# Make sure your working tree is clean and dev is up to date
git checkout dev
git pull origin dev
git checkout -b release/v0.1.0

# Commit the release (an empty commit is fine if there's nothing else to land)
git commit --allow-empty -m "chore: release v0.1.0 [testpypi]"
git push origin release/v0.1.0

# Open and merge the PR — use --squash so the commit message above
# (with its [testpypi]/[pypi] keyword) becomes the commit on main
gh pr create --base main --head release/v0.1.0 \
  --title "chore: release v0.1.0 [testpypi]" --body ""
gh pr merge --squash

# Pull the merged commit and tag exactly that commit
git checkout main
git pull origin main
git tag v0.1.0
git push origin v0.1.0
```

Watch the Actions tab: `test` → `release` job, under the `testpypi`
environment. Once it succeeds, check
`https://test.pypi.org/project/dictk/` for the new version.

For a real PyPI release, repeat with `[pypi]` instead of `[testpypi]` and a
new tag/version (PyPI and TestPyPI are independent indexes, but reusing a
version number across a test and a real release invites confusion — prefer
a fresh version, e.g. `v0.1.1`, for the real release):

```bash
git checkout dev
git pull origin dev
git checkout -b release/v0.1.1
git commit --allow-empty -m "chore: release v0.1.1 [pypi]"
git push origin release/v0.1.1
gh pr create --base main --head release/v0.1.1 \
  --title "chore: release v0.1.1 [pypi]" --body ""
gh pr merge --squash
git checkout main
git pull origin main
git tag v0.1.1
git push origin v0.1.1
```

Uploads to PyPI (and TestPyPI) are permanent — a given version's files can
never be re-uploaded or deleted, only "yanked". Prefer testing on TestPyPI
first, as with `v0.1.0` above, before publishing the same content to PyPI.
