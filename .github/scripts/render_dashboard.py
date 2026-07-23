"""Render the gh-pages status dashboard linking every published report/badge.

Used by the `docs` job in ci.yml. Lives at /dashboard/ on the deployed
site (the site root is the mdBook user guide, so the dashboard can't live
there), and links to its siblings with relative paths (../api/, etc.) so it
works regardless of the domain the site is served from.
"""

import argparse
import html

PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>dictk status dashboard</title>
<style>
  body {{
    font-family: system-ui, sans-serif;
    margin: 2rem auto;
    max-width: 40rem;
    line-height: 1.5;
  }}
  .badges img {{ margin: 0.15rem; }}
  ul {{ padding-left: 1.2rem; }}
  footer {{ margin-top: 2rem; color: #57606a; font-size: 0.9rem; }}
</style>
</head>
<body>
<h1>dictk &mdash; status dashboard</h1>

<p class="badges">
<a href="{github_repo_url}/actions/workflows/ci.yml"><img
  src="{github_repo_url}/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
<a href="../"><img
  src="https://img.shields.io/badge/docs-user%20guide-blue" alt="Docs"></a>
<a href="../api/dictk.html"><img
  src="https://img.shields.io/badge/docs-API%20reference-blue" alt="API"></a>
<a href="../coverage/"><img
  src="../badges/coverage.svg" alt="Coverage"></a>
<a href="../reports/lint/"><img
  src="../badges/lint.svg" alt="Lint"></a>
</p>

<ul>
<li><a href="../">User guide</a> &mdash; mdBook, built with dictk's own CLI on <code>PATH</code></li>
<li><a href="../api/dictk.html">API reference</a> &mdash; generated from docstrings with pdoc</li>
<li><a href="../coverage/">Coverage report</a> &mdash; full <code>pytest --cov</code> HTML output</li>
<li><a href="../reports/lint/">Lint report</a> &mdash; full pylint findings (informational; ruff gates CI)</li>
<li><a href="{github_repo_url}">Repository</a></li>
<li><a href="{github_repo_url}/commit/{sha}">Commit {short_sha}</a></li>
<li><a href="{github_repo_url}/actions/runs/{run_id}">CI run that built this page</a></li>
</ul>

<footer>Generated {timestamp} from <code>{ref_name}</code> at commit <code>{short_sha}</code>.</footer>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--github-repo", required=True, help="e.g. hovey/dictk")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--ref-name", required=True)
    parser.add_argument("--timestamp", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    page = PAGE_TEMPLATE.format(
        github_repo_url=f"https://github.com/{html.escape(args.github_repo)}",
        run_id=html.escape(args.run_id),
        sha=html.escape(args.sha),
        short_sha=html.escape(args.sha[:8]),
        ref_name=html.escape(args.ref_name),
        timestamp=html.escape(args.timestamp),
    )
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(page)


if __name__ == "__main__":
    main()
