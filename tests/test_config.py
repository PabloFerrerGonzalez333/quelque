from pathlib import Path

from quelque.config import AppConfig


def test_config_reads_env(monkeypatch):
    monkeypatch.setenv("QUELQUE_CHUNK_DURATION_SECONDS", "600")
    monkeypatch.setenv("QUELQUE_CACHE_DIR", "tmp-cache")
    config = AppConfig()
    assert config.chunk_duration_seconds == 600
    assert config.cache_dir == Path("tmp-cache")
