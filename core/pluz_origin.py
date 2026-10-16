"""
pluz_origin.py -- makes git's "origin" match GH_USER / GH_REPO from .env, so .env is the
single place that says which repo you push to (change the name in .env and re-run).

Exit codes:  0 = origin already right (or this folder is not a git repo yet)
             3 = origin was missing or pointed somewhere else and has been changed:
                 the launcher then fetches the new repo and re-bases the folder on it
             1 = error
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pluz_common import repo_root, load_env  # noqa: E402


def norm(url: str) -> str:
    u = re.sub(r"^https://[^@/]+@", "https://", url.strip()).rstrip("/").lower()
    return u[:-4] if u.endswith(".git") else u


def main(argv=None) -> int:
    root = repo_root()
    env = load_env(root)
    user, repo = env.get("GH_USER"), env.get("GH_REPO")
    git = os.environ.get("PLUZ_GIT") or "git"

    def run(*a):
        return subprocess.run([git, *a], cwd=root, capture_output=True, text=True)

    if run("rev-parse", "--is-inside-work-tree").returncode != 0:
        return 0
    if not user or not repo:
        print("[WARN] GH_USER / GH_REPO are not set in .env, so origin was left as it is.")
        return 0
    want = f"https://github.com/{user}/{repo}.git"
    have = run("config", "--get", "remote.origin.url")
    if have.returncode != 0:
        r = run("remote", "add", "origin", want)
        print(f"[INFO] this folder had no origin; set it to {want}")
        return 3 if r.returncode == 0 else 1
    if norm(have.stdout) == norm(want):
        return 0
    r = run("remote", "set-url", "origin", want)
    if r.returncode != 0:
        print(f"[FAIL] could not change origin: {r.stderr.strip()}")
        return 1
    print(f"[INFO] origin pointed to {re.sub(r'://[^@/]+@', '://', have.stdout.strip())}")
    print(f"[INFO] now set to {want}  (from GH_USER / GH_REPO in .env)")
    return 3


if __name__ == "__main__":
    sys.exit(main())
