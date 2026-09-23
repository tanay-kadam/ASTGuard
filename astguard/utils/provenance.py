from __future__ import annotations

import importlib.metadata
import os
import platform
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .hashing import object_hash, sha256_file


def environment_snapshot(packages: Iterable[str] = ()) -> dict:
    versions: dict[str, str | None] = {}
    for name in packages:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return {
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "hostname": socket.gethostname(),
        "packages": versions,
    }


def source_identity(root: str | Path = ".") -> dict:
    root = Path(root).resolve()
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL
        ).strip()
        dirty = subprocess.check_output(
            ["git", "diff", "--binary"], cwd=root, stderr=subprocess.DEVNULL
        )
        return {"kind": "git", "commit": commit, "dirty_diff_hash": object_hash(dirty.hex())}
    except (FileNotFoundError, subprocess.CalledProcessError):
        entries = []
        for directory,subdirectories,filenames in os.walk(root):
            subdirectories[:]=[name for name in subdirectories if not name.startswith('.') and name not in {'runs','data','artifacts','results','third_party'}]
            for name in filenames:
                if name.endswith('.py'):
                    path=Path(directory)/name
                    entries.append((path.relative_to(root).as_posix(),sha256_file(path)))
        entries.sort()
        return {"kind": "source_tree", "hash": object_hash(entries), "file_count": len(entries)}
