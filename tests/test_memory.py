from pathlib import Path

from packages.jarvis_core.memory import MemoryStore


def test_memory_persists_and_prunes(tmp_path: Path):
    db = tmp_path / "jarvis.db"
    store = MemoryStore(str(db), max_chars=80)
    store.upsert("name", "Prince", importance=10)
    store.upsert("low", "x" * 100, importance=1)

    restarted = MemoryStore(str(db), max_chars=80)
    assert restarted.get("name") is not None
    assert "name: Prince" in restarted.render_context()
    assert len(restarted.render_context()) <= 80
