"""Cached stand-in for `python3` inside cmdrun blocks.

Keys each run on the command, every file git sees in the page
directory except `.md` pages (tracked, or untracked and not ignored), every .py under
`src/dictk`, `uv.lock`, and the Python version. A hit replays the
stored stdout and restores the generated files the run wrote. Only
image, data, and archive suffixes count as output, so a `.md` or `.py`
file saved during a run is never stored or restored. A miss runs the
script and stores both.

DICTK_BOOK_CACHE=verify ignores the cache, re-runs, and reports any
stdout or output file that differs from the stored entry (zip files
compare by member contents, since zips embed timestamps). The report\nlands in `.cmdrun_cache/verify_report.txt`, because `mdbook-cmdrun`\ndiscards a command's stderr.
"""

import fcntl
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CACHE = HERE / ".cmdrun_cache"
DATA_SUFFIXES = {
    ".png",
    ".tiff",
    ".tif",
    ".jpg",
    ".jpeg",
    ".csv",
    ".npy",
    ".npz",
    ".json",
    ".txt",
}
OUTPUT_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
    ".gif",
    ".svg",
    ".pdf",
    ".csv",
    ".json",
    ".txt",
    ".npy",
    ".npz",
    ".zip",
}
VERSION = "2"


def file_hash(path, memo):
    stat = path.stat()
    token = [stat.st_mtime_ns, stat.st_size]
    entry = memo.get(str(path))
    if entry and entry[0] == token:
        return entry[1]
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    memo[str(path)] = [token, digest]
    return digest


def same_file(a, b):
    if a.suffix == ".zip" and b.suffix == ".zip":
        with zipfile.ZipFile(a) as za, zipfile.ZipFile(b) as zb:
            return za.namelist() == zb.namelist() and all(
                za.read(name) == zb.read(name) for name in za.namelist()
            )
    return a.read_bytes() == b.read_bytes()


def load_json(path, default):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return default


def snapshot(directory):
    return {
        str(p): (p.stat().st_mtime_ns, p.stat().st_size)
        for p in directory.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts
    }


def main():
    argv = sys.argv[1:]
    cwd = Path.cwd()
    mode = os.environ.get("DICTK_BOOK_CACHE", "on")
    command = " ".join(argv)
    excluded = [
        line.strip()
        for line in (HERE / "cache_exclude.txt").read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]

    def run():
        return subprocess.run([sys.executable, *argv], cwd=cwd, stdout=subprocess.PIPE)

    if any(pattern in command for pattern in excluded):
        result = run()
        sys.stdout.buffer.write(result.stdout)
        sys.exit(result.returncode)

    CACHE.mkdir(exist_ok=True)
    lock = open(CACHE / "lock", "w")
    fcntl.flock(lock, fcntl.LOCK_EX)
    memo = load_json(CACHE / "hashmemo.json", {})

    parts = [VERSION, sys.version, command, str(cwd)]
    tracked = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "."],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if tracked.returncode == 0:
        inputs = [
            cwd / name
            for name in sorted(tracked.stdout.splitlines())
            if not name.endswith(".md")
        ]
    else:
        inputs = [
            p
            for p in sorted(cwd.iterdir())
            if p.is_file() and (p.suffix == ".py" or p.suffix in DATA_SUFFIXES)
        ]
    inputs += sorted((ROOT / "src" / "dictk").rglob("*.py"))
    inputs += [ROOT / "uv.lock", ROOT / "pyproject.toml"]
    for p in inputs:
        if p.is_file():
            parts.append(f"{p}:{file_hash(p, memo)}")
    key = hashlib.sha256("\n".join(parts).encode()).hexdigest()
    (CACHE / "hashmemo.json").write_text(json.dumps(memo))

    entry = CACHE / key
    if entry.is_dir() and mode == "on":
        meta = load_json(entry / "meta.json", {"files": []})
        for rel in meta["files"]:
            if Path(rel).suffix not in OUTPUT_SUFFIXES:
                continue
            stored = entry / "files" / rel
            target = cwd / rel
            if not target.exists() or target.read_bytes() != stored.read_bytes():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(stored, target)
        sys.stdout.buffer.write((entry / "stdout.bin").read_bytes())
        return

    before = snapshot(cwd)
    result = run()
    if result.returncode != 0:
        sys.stdout.buffer.write(result.stdout)
        sys.exit(result.returncode)
    after = snapshot(cwd)
    changed = sorted(
        str(Path(p).relative_to(cwd))
        for p, sig in after.items()
        if before.get(p) != sig and Path(p).suffix in OUTPUT_SUFFIXES
    )

    if mode == "verify" and entry.is_dir():
        problems = []
        if (entry / "stdout.bin").read_bytes() != result.stdout:
            problems.append("stdout")
        for rel in load_json(entry / "meta.json", {"files": []})["files"]:
            stored = entry / "files" / rel
            if not (cwd / rel).exists() or not same_file(cwd / rel, stored):
                problems.append(rel)
        with open(CACHE / "verify_report.txt", "a") as report:
            status = f"MISMATCH {problems}" if problems else "ok"
            report.write(f"{status}\t{command[:100]}\n")
    else:
        staging = CACHE / (key + ".tmp")
        shutil.rmtree(staging, ignore_errors=True)
        (staging / "files").mkdir(parents=True)
        for rel in changed:
            (staging / "files" / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(cwd / rel, staging / "files" / rel)
        (staging / "stdout.bin").write_bytes(result.stdout)
        (staging / "meta.json").write_text(
            json.dumps({"files": changed, "command": command})
        )
        shutil.rmtree(entry, ignore_errors=True)
        staging.rename(entry)
    sys.stdout.buffer.write(result.stdout)


if __name__ == "__main__":
    main()
