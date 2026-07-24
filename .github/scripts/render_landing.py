"""Render the gh-pages root landing page linking to the main/ and dev/ sites.

Used by the `docs` job in ci.yml. Both branches deploy to their own
subdirectory (see CONTRIBUTING.md#cicd-architecture) rather than the site
root, so this regenerates the root index.html on every deploy — whichever
branch (main or dev) ran most recently — to point at both.
"""

import argparse
import html

PAGE_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>dictk</title>
<style>
  body {{
    font-family: system-ui, sans-serif;
    margin: 2rem auto;
    max-width: 40rem;
    line-height: 1.5;
  }}
  ul {{ padding-left: 1.2rem; }}
  footer {{ margin-top: 2rem; color: #57606a; font-size: 0.9rem; }}
</style>
</head>
<body>
<h1>dictk</h1>

<p>Digital Image Correlation Toolkit &mdash; pick a version:</p>

<ul>
<li><a href="main/">main</a> &mdash; latest released user guide, API reference, coverage and lint reports</li>
<li><a href="dev/">dev</a> &mdash; in-development user guide, API reference, coverage and lint reports</li>
</ul>

<p><a href="{github_repo_url}">Repository</a></p>

<footer>Last refreshed {timestamp} by a deploy of <code>{ref_name}</code> at commit
<code>{short_sha}</code> (<a href="{github_repo_url}/actions/runs/{run_id}">CI run</a>).</footer>
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
