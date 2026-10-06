#!/bin/sh
# mdbook preprocessor entry point for [preprocessor.cmdrun]. Runs
# mdbook-cmdrun with a `python3` shim first on PATH, so each
# `<!-- cmdrun python3 ... -->` block goes through cache_run.py.
# DICTK_BOOK_CACHE=off bypasses the cache; =verify re-runs and diffs.
# CI always bypasses it.
if [ "$1" = "supports" ] || [ -n "$CI" ] || [ "$DICTK_BOOK_CACHE" = "off" ]; then
    exec mdbook-cmdrun "$@"
fi
if [ "$DICTK_BOOK_CACHE" = "verify" ]; then
    rm -f "$(cd "$(dirname "$0")" && pwd)/.cmdrun_cache/verify_report.txt"
fi
DICTK_REAL_PYTHON=$(command -v python3)
export DICTK_REAL_PYTHON
PATH="$(cd "$(dirname "$0")" && pwd)/cache_shim:$PATH"
export PATH
exec mdbook-cmdrun "$@"
