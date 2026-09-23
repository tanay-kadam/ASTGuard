import hashlib
import json
import sys
from types import SimpleNamespace

import pytest

from astguard.data import download


def _registered_lock(tmp_path, logical_name, payload):
    lock_path = tmp_path / "sources.lock.json"
    lock_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "sources": [
                    {
                        "logical_name": logical_name,
                        "sha256": hashlib.sha256(payload).hexdigest(),
                        "rows": len(payload.splitlines()),
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return lock_path


def _fake_gdown(monkeypatch, payload):
    def fake_download(_url, destination, quiet=False):
        del quiet
        with open(destination, "wb") as handle:
            handle.write(payload)
        return destination

    monkeypatch.setitem(sys.modules, "gdown", SimpleNamespace(download=fake_download))


def test_registered_primevul_file_is_reacquired_on_fresh_clone(tmp_path, monkeypatch):
    payload = b'{"id": 1}\n'
    logical = "primevul/primevul_train.jsonl"
    lock_path = _registered_lock(tmp_path, logical, payload)
    monkeypatch.setattr(download, "PRIMEVUL_FILES", {"primevul_train.jsonl": "file-id"})
    _fake_gdown(monkeypatch, payload)
    monkeypatch.chdir(tmp_path)

    download.acquire_primevul(lock_path)

    assert (tmp_path / "data/raw/primevul/original/primevul_train.jsonl").read_bytes() == payload
    assert json.loads(lock_path.read_text(encoding="utf-8"))["sources"][0]["logical_name"] == logical


def test_registered_diversevul_download_rejects_wrong_checksum(tmp_path, monkeypatch):
    lock_path = _registered_lock(tmp_path, "diversevul/standalone", b'{"id": 1}\n')
    _fake_gdown(monkeypatch, b'{"id": 2}\n')
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ValueError, match="checksum mismatch"):
        download.acquire_diversevul(lock_path)

    assert not (tmp_path / "data/raw/diversevul/original/payload.jsonl").exists()
    assert not (tmp_path / "data/raw/diversevul/original/payload.partial").exists()
