# Contributing to `dictk`

`dictk` is developed on [GitHub](https://github.com/hovey/dictk) using
[Git](https://git-scm.com/) for version control. Git is the tool that tracks
changes to the source on your own computer; GitHub is the hosting service
that holds the canonical copy of the repository, tracks issues and pull
requests, and runs the CI/CD pipeline described [below](#cicd-architecture).

## Cloning vs. forking

Contributors can get a working copy of `dictk` by either cloning or forking
the repository.

| Cloning | Forking |
| --- | --- |
| A **Git** action: it creates a copy of the repository on your own computer. | A **GitHub** action: it creates a personal copy of the entire project under your own GitHub account. |
| For **authorized collaborators** who can push changes directly to the main project. | For **external contributors** to make changes without affecting the original repository, then submit a pull request to share those changes. |

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

source .venv/bin/activate       # bash/zsh
source .venv/bin/activate.fish  # fish
.venv\Scripts\activate          # Windows

pip install -e ".[dev]"
```

## Git workflow

### Branching model

`main` and `dev` are both long-lived: `dev` is branched from `main`, and
`main` only moves forward via merges from `dev` (each push to `main` is a
potential release — see ["Releasing"](#releasing) below). Actual development happens one
level further out, on `dev-feature`, a branch cut from `dev`.

```
main          ●───────────────●───────────  (releases only, tagged)
                   \                \
dev           ●─────●───●───●───●────●────  (integration branch)
               \       \         \
dev-feature     ●───●   ●─●───●   ●──●      (your work)
```

`dev-feature` above is a placeholder — name each branch `dev-<short-description>`
so its purpose is clear at a glance. For example:

- `dev-cicd` — CI/CD pipeline or workflow-file changes
- `dev-algorithm-refactor` — refactoring an existing algorithm or module
- `dev-imaging` — new imaging transformations/workflows
- `dev-docs` — documentation-only updates

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

**Which to pick**

* Use **merge** if the branch is shared with others or you want a clear record of when `dev`'s changes came in
* Use **rebase** if it's mostly just your own branch and you want a clean, linear commit history without merge bubbles.

**Tip** — before doing either, it's worth running:

```bash
git log dev-feature..dev --oneline
```

to preview what's coming in, so conflicts aren't a total surprise.

## Development workflow

Developers work locally and periodically push to their `dev-<feature>`
branch. Before pushing changes, developers should check code quality
locally rather than solely relying on CI to catch problems. This means
running tests, linting, format checking (ruff), code coverage, and
confirming that the documentation (mdBook + pdoc) builds locally. Catching
issues locally is faster than waiting on a CI run, and it keeps the CI
pipeline green for everyone else.

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

`pyproject.toml` has no `[tool.ruff.lint]` section, so `ruff check` runs
ruff's bare default rule selection — `E4`/`E7`/`E9` (pycodestyle basics)
plus `F` (pyflakes). This is deliberate, not an oversight. `ruff check` is a
hard CI gate; broader rule sets (`D` docstring-style, `ANN`
type-annotation-completeness, `S` security, and the rest) risk fighting
conventions already established elsewhere in this codebase (e.g. the
Google-style docstrings `pdoc --docformat google` depends on), or simply
duplicating ground [`pylint`](#running-pylint-informational) already
covers informationally, without ruff's same all-or-nothing gating risk.

### Building the docs

Documentation is an [mdBook](https://rust-lang.github.io/mdBook/) under
`docs/userguide/`, with two preprocessors enabled:
[mdbook-cmdrun](https://github.com/FauconFan/mdbook-cmdrun), so pages can
embed live, always-accurate command output (see the "Image Generation"
page for an example) instead of pasted-by-hand output, and
[mdbook-katex](https://github.com/lzanini/mdbook-katex), so pages can
include `$$...$$` LaTeX math blocks (see the "Single Point Motion" page).
Neither is a Python dependency:

```bash
# mdbook must be pinned to 0.4.52: mdbook-cmdrun and mdbook-katex's 0.9.x
# line both depend on the mdbook crate's 0.4.x preprocessor JSON schema,
# which changed in mdbook 0.5 and broke compatibility
# (https://github.com/FauconFan/mdbook-cmdrun/issues/22, open as of this
# writing; mdbook-katex made the same jump at its own 0.10.0). Do not
# `brew install mdbook` or `cargo install mdbook`/`mdbook-katex` without a
# --version pin, or the build will fail with "Unable to parse the input".
cargo install mdbook --version 0.4.52
cargo install mdbook-cmdrun
cargo install mdbook-katex --version 0.9.4
```

If you already have a newer `mdbook` from Homebrew or elsewhere on your
`PATH`, make sure `~/.cargo/bin` comes first (or check `mdbook --version`
reports `0.4.52` before building).

`book.toml` lives at the repo root (not inside `docs/userguide/`), with
`src = "docs/userguide/src"` and `build-dir = "docs/userguide/book"`, so
both commands below run from the repo root:

```bash
uv run mdbook build           # build once, output in docs/userguide/book/
uv run mdbook serve --open    # live preview at http://localhost:3000
```

`uv run` puts `dictk`'s own CLI on `PATH` for the build, since some
`cmdrun` directives invoke `dictk` directly.

### Building the API docs

Python API reference docs (function signatures, docstrings) are generated
from source with [pdoc](https://pdoc.dev/), a dev dependency:

```bash
uv run pdoc dictk -o docs/api --docformat google --math -t docs/pdoc_templates   # build once, output in docs/api/
uv run pdoc dictk --docformat google --math -t docs/pdoc_templates              # live preview, serves on localhost
```

`--docformat google` matters: pdoc defaults to `restructuredtext`, which
doesn't recognize this codebase's Google-style `Args:`/`Returns:`/`Raises:`
docstring sections — without it, an `Args:` section renders as one flat
paragraph instead of a proper bulleted list.

`--math` matters too: several docstrings (`dictk.correlation`'s CC/NCC/
ZCC/ZNCC/phase-correlation formulas) use `$...$`/`$$...$$` LaTeX — without
it, no MathJax gets included and the raw LaTeX source shows up literally
instead of being rendered. A separate trap in the same area: pdoc treats
a docstring as Markdown before MathJax ever sees it, and Markdown's own
backslash-escape rule silently strips the backslash off LaTeX commands
like `\!` (a backslash followed by ASCII punctuation). Avoid that pattern
in docstring math, or double the backslash (`\\!`).

No submodules need listing on the command line — bare `pdoc dictk`
discovers all of them, and also builds the "Submodules" links on the
`dictk.html` landing page, because every one of them
(`image`/`translation`/`correlation`/`grid`/`cli`/`rosta`) is named
directly in `dictk/__init__.py`'s own `__all__`, alongside the
individual functions (`astronaut`, `checkerboard`, `rosta`,
`__version__`) it re-exports:
[pdoc's `__all__` handling](https://pdoc.dev/docs/pdoc.html#what-objects-are-documented)
treats a name in `__all__` that isn't already a bound attribute as a
submodule to import and document. Leaving a submodule out of `__all__`
doesn't fail the build — it silently drops that module from both the
generated docs and the landing page's own navigation — so if you add a
new top-level submodule, add its name to `__all__` too, not to this
command.

Output goes to `docs/api/` (gitignored, regenerated on demand). CI builds
this too and publishes it alongside the mdBook user guide — see
["CI/CD architecture"](#cicd-architecture) below.

**Development note:** `-t docs/pdoc_templates` points pdoc at
`docs/pdoc_templates/custom.css`, pdoc's own supported override point
(`-t`/`--template-directory` — see
[pdoc's documentation](https://pdoc.dev/docs/pdoc.html)). It's included
last, after `theme.css`/`layout.css`/`content.css`, so it always wins
the cascade. This one softens pdoc's default theme: a pure white page
background (`--pdoc-background: #fff`) with code-block/highlighted-box
backgrounds only slightly darker (`--code: #f8f8f8`, `--accent: #eee`)
reads as a stark white glare across the page as a whole. The override
shifts all three together — `--pdoc-background: #efede7`,
`--code: #e3dfd7`, `--accent: #d7d3c9` — rather than tinting the
background alone, so the page < code-block < accent-box hierarchy
pdoc's default theme establishes stays intact, just softer throughout.
Tuned in two successive passes, each computed in HSL space (same hue/
saturation per variable, lightness lowered by a measured delta) rather
than picked by eye, so the gaps between the three tiers stay even
instead of collapsing into each other. `--accent2` (the border/
scrollbar gray, `#c1c1c1`) is untouched — already reads with plenty of
contrast against every tone above.

### Building the coverage badge

The README's coverage badge is a real SVG generated from `coverage.xml` with
[genbadge](https://smarie.github.io/python-genbadge/), a dev dependency —
not a static label:

```bash
uv run pytest --cov=src/dictk --cov-report=xml --cov-report=html
uv run genbadge coverage -i coverage.xml -o coverage-badge.svg
```

In CI this runs in the `docs` job (not `test`) using the coverage.xml
produced by the `test` job's `report-test` artifact, so the badge only
updates on pushes to `main` or `dev` — same cadence as the Docs and API
badges, not per-PR. Both `coverage-badge.svg` and the full `htmlcov/` report
are staged into the deployed site under that branch's subdirectory
(`<branch>/badges/coverage.svg` and `<branch>/coverage/` respectively) — see
["CI/CD architecture"](#cicd-architecture) below.

### Building the tests badge

The README's tests badge (`tests: N pass M fail`) is a real SVG built from
pytest's own JUnit XML report, not a static label:

```bash
uv run pytest --cov=src/dictk --cov-report=xml --cov-report=html --junitxml=junit.xml
uv run python .github/scripts/generate_tests_badge.py --input junit.xml --output tests-badge.svg
```

`--junitxml` is a builtin pytest flag — no extra plugin needed.
`generate_tests_badge.py` parses that report's pass/fail/skip counts and
requests a matching badge from shields.io directly (same service
[genbadge](https://smarie.github.io/python-genbadge/) uses for the coverage
badge above, just called directly here rather than through that library,
since genbadge's own test-badge format is `N/M`, not the `N pass M fail`
wording this one matches) — green when nothing fails, red otherwise. Like
the coverage badge, this runs in the `docs` job using the `test` job's
`report-test` artifact, so it updates on pushes to `main`/`dev` only. Staged
into the deployed site at `<branch>/badges/tests.svg`.

**Development note:** shields.io returns `403 Forbidden` for `urllib`'s
default User-Agent string (`Python-urllib/x.y`) — presumably basic bot
filtering, since `curl` (used by the lint badge below) isn't blocked.
Fixed by setting an explicit `User-Agent` header on the request rather
than shelling out to `curl` from a Python script for no other reason.

### Running pylint (informational)

ruff (`ruff format --check` and `ruff check`) is what actually gates CI —
see ["Linting and formatting"](#linting-and-formatting) above. [pylint](https://pylint.readthedocs.io/)
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
staged into the deployed site at `<branch>/reports/lint/`, and the badge at
`<branch>/badges/lint.svg` — same cadence as the other gh-pages badges
(updates on pushes to `main` or `dev`).

### Building the status dashboard

`<branch>/dashboard/` on the deployed site is a single page linking every
badge and report above for that branch, generated by
`.github/scripts/render_dashboard.py`. It exists because the mdBook user
guide occupies that branch's subdirectory root, so there's no natural
landing page that lists the API reference, coverage report, and lint report
together — rather than expecting visitors to already know those paths, or
scattering the links across the README only. It doesn't require any of the
other artifacts to already exist locally (it only generates links to them,
using paths relative to `<branch>/dashboard/`, e.g. `../coverage/`):

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
deployed site at `<branch>/dashboard/`.

### Building the root landing page

The site root (`/`) doesn't belong to either branch — `main` and `dev` each
deploy to their own subdirectory (see ["CI/CD
architecture"](#cicd-architecture) below), so the root is a two-column
dashboard (main "Released" in blue, dev "Development" in orange) linking to
each branch's user guide, API reference, dashboard, coverage, lint, and
tests badges, styled with the Tailwind CDN build — modeled on
[sandialabs/rattlesnake-vibration-controller's gh-pages
dashboard](https://sandialabs.github.io/rattlesnake-vibration-controller/).
It's generated by `.github/scripts/render_landing.py` and regenerated on
every deploy from whichever branch ran most recently (only the footer's
timestamp/commit/CI-run attribution changes between deploys — the two
columns' links are static):

```bash
uv run python .github/scripts/render_landing.py \
  --github-repo hovey/dictk \
  --run-id local \
  --sha "$(git rev-parse HEAD)" \
  --ref-name "$(git rev-parse --abbrev-ref HEAD)" \
  --timestamp "$(date -u +'%Y-%m-%d %H:%M:%S UTC')" \
  --output landing.html
```

`landing.html` is staged as `index.html` at the deployed site's root.

### Before pushing

There's no `preflight` command yet (see rattlesnake-vibration-controller's
`preflight.py` for an example of what that could grow into) — for now, run
the checks manually:

```bash
uv run ruff format --check
uv run ruff check
uv run pytest --cov=src/dictk --cov-report=xml --cov-report=html --junitxml=junit.xml
uv run mdbook build
uv run pdoc dictk -o docs/api --docformat google --math -t docs/pdoc_templates
uv run genbadge coverage -i coverage.xml -o coverage-badge.svg
uv run python .github/scripts/generate_tests_badge.py --input junit.xml --output tests-badge.svg
uv run pylint src/dictk --output-format=text --reports=yes
```

These are exactly the checks the `test` and `docs` jobs run in CI.

## CI/CD architecture

CI and releasing live in two workflows: `.github/workflows/ci.yml` (checks
and docs, on every push/PR) and `.github/workflows/release.yml` (publishing,
on a version tag push).

`ci.yml` has two jobs, plus a `workflow_call` trigger so `release.yml` can
invoke it as a reusable workflow:

- **`test`** — runs on every push, pull request, and when called from
  `release.yml`. Installs dependencies with `uv sync`, runs `uv build` as a
  build sanity check, `ruff format --check`, `ruff check`, and `pytest --cov`
  (with `--junitxml` too). Uploads the coverage and JUnit XML reports as a
  build artifact (`report-test`).
- **`docs`** — runs only on pushes to `main` or `dev`, after `test` passes
  (this `if` condition also means it's skipped when `release.yml` calls
  `ci.yml` from a tag push, since the ref won't be `refs/heads/main` or
  `refs/heads/dev`). Installs the pinned `mdbook` 0.4.52, `mdbook-cmdrun`,
  and `mdbook-katex` (cached via `actions/cache`), downloads the `test`
  job's `report-test` artifact, builds the mdBook user guide with `dictk`'s
  own CLI on `PATH`, builds the pdoc API reference, generates a coverage
  badge from `coverage.xml` with
  [genbadge](https://smarie.github.io/python-genbadge/) and a tests badge
  from `junit.xml` (`N pass M fail`, via `generate_tests_badge.py` — see
  ["Building the tests badge"](#building-the-tests-badge) above), runs
  pylint informationally to get a 0-10 score (fetched as a shields.io
  badge) and a full findings report, renders a status dashboard linking all
  of the above, and stages all of it into one directory (user guide at the
  root, API reference under `api/`, badges under `badges/coverage.svg`,
  `badges/lint.svg`, and `badges/tests.svg`, full HTML coverage report
  under `coverage/`, full pylint report under `reports/lint/`, dashboard
  under `dashboard/`).

  That staged directory becomes the *whole subtree* for whichever branch
  triggered the run — deployed to `main/` or `dev/` on the `gh-pages`
  branch (published via GitHub Pages), alongside a regenerated root
  `index.html` landing page linking to both (see ["Building the root
  landing page"](#building-the-root-landing-page) above). Deployment is a
  manual clone-of-`gh-pages` → replace only `${DEPLOY_SUBDIR}/` and
  `index.html` → commit → push, not `peaceiris/actions-gh-pages`: that
  action replaces the whole `publish_dir` (or, with `keep_files`, tries to
  preserve everything else, which is imprecise if `main` and `dev` deploy
  close together and risks one branch's content clobbering the other's — a
  problem [sandialabs/rattlesnake-vibration-controller's
  `ci.yml`](https://github.com/sandialabs/rattlesnake-vibration-controller)
  hit and solved the same way). The job's `concurrency` group
  (`gh-pages-deploy`, `cancel-in-progress: false`) serializes `main`'s and
  `dev`'s deploys so this step never runs for both at once.

`release.yml` triggers on pushing a tag matching `v*` and runs, in order:

- **`validate_tag`** — verifies the tag is valid [PEP 440](https://peps.python.org/pep-0440/),
  that it's strictly newer than every existing tag, and that its branch
  matches its prerelease status: a prerelease tag (`a`/`b`/`rc`/`.dev` suffix)
  must be reachable from `origin/dev`; a stable/post tag must be reachable
  from `origin/main` specifically. Outputs `is_prerelease` for the jobs below.
- **`test`** — `needs: validate_tag`, calls `ci.yml`'s `test` job fresh at the
  tagged commit (not reused from an earlier push-to-main run).
- **`build`** — `needs: test`. Runs `uv build`, generates a build-provenance
  attestation for the dist files, and uploads them as an artifact.
- **`github-release`** — `needs: [build, validate_tag]`. Creates a GitHub
  Release with auto-generated notes, attaching the dist files, marked
  prerelease or not per `validate_tag`'s output.
- **`publish_testpypi`** / **`publish_pypi`** — `needs: [build, github-release,
  validate_tag]`, gated on `is_prerelease` being `true`/`false` respectively.
  Publishes to TestPyPI or PyPI. See ["Releasing"](#releasing) below.

This is intentionally a minimal setup — no matrix OS/Python testing, no
containerized builds. pytribeam's `ci.yml` and
rattlesnake-vibration-controller's `ci.yml`/`release.yml` are useful
references for growing any of this out later (`dictk`'s `release.yml` is in
fact modeled on rattlesnake-vibration-controller's, with one addition: tying
the branch check to prerelease status, described above).

## Versioning

Versions are derived automatically from git tags via
[hatch-vcs](https://github.com/ofek/hatch-vcs) — there is no hand-maintained
version string anywhere in the source. Tag format is a `v`-prefixed
[PEP 440](https://peps.python.org/pep-0440/) version, e.g. `v0.1.0`.

If the current commit isn't exactly at a tag (or the working tree is dirty),
`hatch-vcs` appends a local version segment (e.g. `0.1.dev1+gd975d09`).
**PyPI and TestPyPI reject uploads with a local version segment**, so a
publishable commit must be exactly the tagged commit.

### Tags and semantic versioning

Tags follow [PEP 440](https://peps.python.org/pep-0440/), which requires
version strings to follow this structure:

```
N.N.N[{a|b|rc}N][.postN][.devN]
```

#### Example tags

Prerelease tags:

| tag | description |
| --- | --- |
| `v1.1.0a1` | The first **alpha** for version 1.1.0 |
| `v1.1.0b2` | The second **beta** for version 1.1.0 |
| `v1.1.0rc1` | The first **release candidate** for version 1.1.0 |

A **release candidate** is made during the final testing stage before a full
release.

Stable release tags (e.g., starting from a `v1.0.0` release):

| tag | description |
| --- | --- |
| `v1.0.1` | **Patch release**: backwards-compatible bug fixes |
| `v1.1.0` | **Minor release**: new features that are backwards-compatible |
| `v2.0.0` | **Major release**: significant changes or breaking API updates |

Development and post-release tags:

| tag | description |
| --- | --- |
| `v1.1.0.dev1` | A version currently under development |
| `v1.0.0.post1` | A fix for a minor error in the release process, such as a typo in the documentation, without changing the code |

### Release on tag

Pushing a tag is what triggers `release.yml` (see
["CI/CD architecture"](#cicd-architecture) above) — there's no separate
commit-message keyword. Which registry it publishes to is decided by the
tag's own shape: a prerelease tag (`a`/`b`/`rc`/`.dev` suffix) publishes to
TestPyPI, a stable/post tag publishes to PyPI. The branch the tag is cut from
has to match: prerelease tags on `dev`, stable/post tags on `main`. See
["Merging `dev` into `main`"](#merging-dev-into-main) and
["Publishing a release"](#publishing-a-release) below for the actual
commands.

## Releasing

Releases are triggered by pushing a git tag matching `v*` — see
["Release on tag"](#release-on-tag) above. `validate_tag` (the first job in `release.yml`) checks the tag is
valid PEP 440, strictly newer than every existing tag, and cut from the
branch its prerelease status requires (`dev` for prerelease, `main` for
stable/post). Because the release jobs build whatever `hatch-vcs` resolves at
the tagged commit, the tag must point at the exact commit you want published.

### Merging `dev` into `main`

`main` is a protected branch — it only accepts changes through a merged pull
request, even for repo admins, so `git push origin main` will be rejected.
This step is only needed before a **stable** release (prereleases tag `dev`
directly — see ["Publishing a release"](#publishing-a-release) below). Merge
`dev` into `main` through a PR:

```bash
git checkout dev
git pull origin dev
gh pr create --base main --head dev --title "Merge dev into main" --body ""
gh pr merge --merge
```

No approving review is required, so you can merge your own PR.

### One-time setup (already done for this repo)

1. GitHub → repo Settings → Environments: create `testpypi` and `pypi`
   environments. `pypi` has a "Required reviewers" rule (you) configured, so
   a real release needs manual approval in the Actions UI before publishing
   — `testpypi` doesn't need this.
2. On [test.pypi.org](https://test.pypi.org) and
   [pypi.org](https://pypi.org), under the `dictk` project's "Publishing"
   settings, add a trusted publisher: owner `hovey`, repository `dictk`,
   **workflow file `release.yml`** (not `ci.yml` — publishing happens in the
   tag-triggered workflow), environment name `testpypi` (for TestPyPI) or
   `pypi` (for PyPI).

No API tokens are stored anywhere — publishing uses OIDC trusted publishing
via the `id-token: write` permission.

### Publishing a release

**Prerelease (TestPyPI)** — tag `dev` directly, no PR needed:

```bash
git checkout dev
git pull origin dev
git tag v0.1.0rc1
git push origin v0.1.0rc1
```

**Stable (PyPI)** — merge `dev` into `main` first (see
["Merging `dev` into `main`"](#merging-dev-into-main) above), then tag
`main`:

```bash
git checkout main
git pull origin main
git tag v0.1.0
git push origin v0.1.0
```

Either way, watch the Actions tab: `validate_tag` → `test` → `build` →
`github-release` → `publish_testpypi`/`publish_pypi`. For a prerelease, check
`https://test.pypi.org/project/dictk/` once it succeeds. For a stable
release, the `publish_pypi` job pauses for your approval (the `pypi`
environment's required reviewer) before it runs; approve it from the Actions
run page, then check `https://pypi.org/project/dictk/`.

Uploads to PyPI (and TestPyPI) are permanent — a given version's files can
never be re-uploaded or deleted, only "yanked". Prefer testing on TestPyPI
first, as with `v0.1.0rc1` above, before publishing the stable release.
