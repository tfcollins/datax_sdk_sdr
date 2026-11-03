import io
import json

import pytest

from datax_support import cli
from datax_support.fetch import fetch_manifest, manifests_from_sources

SRC_PRIVATE = {
    "repository": "tfcollins/tick",
    "branch": "main",
    "revision": "abc123",
    "path": "support.json",
    "private": True,
}
SRC_PUBLIC = {
    "repository": "tfcollins/hopcap",
    "branch": "main",
    "revision": "def456",
    "path": "support.json",
    "private": False,
}
BODY = {"schema": 1, "project": "tick", "platforms": {}}


class FakeUrlopen:
    def __init__(self):
        self.url = None
        self.headers = {}

    def __call__(self, req, timeout=None):
        self.url = req.full_url
        self.headers = dict(req.header_items())
        return io.BytesIO(json.dumps(BODY).encode())


@pytest.fixture
def fake_urlopen(monkeypatch):
    fake = FakeUrlopen()
    monkeypatch.setattr("datax_support.fetch.urlopen", fake)
    return fake


def test_fetch_uses_pinned_revision_and_bearer_token(fake_urlopen):
    fetch_manifest(SRC_PRIVATE, token="t")
    assert fake_urlopen.url.endswith("/tfcollins/tick/abc123/support.json")
    assert fake_urlopen.headers["Authorization"] == "Bearer t"


def test_branch_tips_uses_branch_not_revision(fake_urlopen):
    fetch_manifest(SRC_PRIVATE, token="t", branch_tips=True)
    assert "/tfcollins/tick/main/" in fake_urlopen.url


def test_public_source_sends_no_token(fake_urlopen):
    fetch_manifest(SRC_PUBLIC, token=None)
    assert "Authorization" not in fake_urlopen.headers


def test_render_fails_without_token_for_private_source(tmp_path, monkeypatch, capsys):
    sources = tmp_path / "sources.json"
    sources.write_text(json.dumps({"schema": 1, "sources": {"tick": SRC_PRIVATE}}))
    monkeypatch.delenv("SUPPORT_READ_TOKEN", raising=False)
    with pytest.raises(SystemExit) as exc:
        cli.main(["render", "--sources", str(sources), "--out", str(tmp_path / "out")])
    assert exc.value.code != 0
    assert "SUPPORT_READ_TOKEN" in capsys.readouterr().err


def test_manifests_from_sources_keys_by_repo(tmp_path, fake_urlopen, monkeypatch):
    sources = tmp_path / "sources.json"
    sources.write_text(json.dumps({"schema": 1, "sources": {"hopcap": SRC_PUBLIC}}))
    out = manifests_from_sources(sources, token_env="SUPPORT_READ_TOKEN")
    assert set(out) == {"hopcap"}
