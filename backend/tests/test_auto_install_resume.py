"""Tests du téléchargement HTTP reprenable du corpus."""

import hashlib
from io import BytesIO

import pytest

from app.services import auto_install


class FakeResponse:
    def __init__(self, status, content, headers=None):
        self.status = status
        self.headers = headers or {}
        self.stream = BytesIO(content)

    def read(self, size):
        return self.stream.read(size)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.stream.close()


def configure_hash(monkeypatch, content):
    expected = hashlib.sha256(content).hexdigest()
    monkeypatch.setattr(auto_install, "ARCHIVE_SHA256", expected)


def test_download_complet(tmp_path, monkeypatch):
    data = b"corpus-gutenberg-complet"
    destination = tmp_path / "corpus.part"
    configure_hash(monkeypatch, data)

    def fake_urlopen(request, timeout):
        assert request.get_header("Range") is None
        return FakeResponse(
            200, data, {"Content-Length": str(len(data))}
        )

    monkeypatch.setattr(
        auto_install.urllib.request, "urlopen", fake_urlopen
    )

    auto_install.download_archive(
        "https://example.org/corpus.tar.gz", destination
    )

    assert destination.read_bytes() == data


def test_reprise_http_206(tmp_path, monkeypatch):
    data = b"abcdefghijklmnopqrstuvwxyz"
    destination = tmp_path / "corpus.part"
    destination.write_bytes(data[:10])
    configure_hash(monkeypatch, data)

    def fake_urlopen(request, timeout):
        assert request.get_header("Range") == "bytes=10-"
        return FakeResponse(
            206,
            data[10:],
            {
                "Content-Range": "bytes 10-25/26",
                "Content-Length": "16",
            },
        )

    monkeypatch.setattr(
        auto_install.urllib.request, "urlopen", fake_urlopen
    )

    auto_install.download_archive(
        "https://example.org/corpus.tar.gz", destination
    )

    assert destination.read_bytes() == data


def test_serveur_sans_reprise(tmp_path, monkeypatch):
    data = b"archive-correcte"
    destination = tmp_path / "corpus.part"
    destination.write_bytes(b"ancienne-partie")
    configure_hash(monkeypatch, data)

    def fake_urlopen(request, timeout):
        assert request.get_header("Range") is not None
        return FakeResponse(
            200, data, {"Content-Length": str(len(data))}
        )

    monkeypatch.setattr(
        auto_install.urllib.request, "urlopen", fake_urlopen
    )

    auto_install.download_archive(
        "https://example.org/corpus.tar.gz", destination
    )

    assert destination.read_bytes() == data


def test_interruption_puis_reprise(tmp_path, monkeypatch):
    data = b"abcdefghijklmnopqrstuvwxyz"
    destination = tmp_path / "corpus.part"
    configure_hash(monkeypatch, data)

    calls = []

    def fake_urlopen(request, timeout):
        calls.append(request.get_header("Range"))

        if len(calls) == 1:
            return FakeResponse(
                200,
                data[:10],
                {"Content-Length": str(len(data))},
            )

        return FakeResponse(
            206,
            data[10:],
            {
                "Content-Range": "bytes 10-25/26",
                "Content-Length": "16",
            },
        )

    monkeypatch.setattr(
        auto_install.urllib.request, "urlopen", fake_urlopen
    )

    with pytest.raises(RuntimeError, match="interrompu"):
        auto_install.download_archive(
            "https://example.org/corpus.tar.gz", destination
        )

    assert destination.read_bytes() == data[:10]

    auto_install.download_archive(
        "https://example.org/corpus.tar.gz", destination
    )

    assert destination.read_bytes() == data
    assert calls == [None, "bytes=10-"]
