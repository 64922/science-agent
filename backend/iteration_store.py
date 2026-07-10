import json
from datetime import datetime, timezone
from pathlib import Path


class IterationStore:
    def __init__(self):
        self.storage_dir = (
            Path(__file__).resolve().parent.parent / "data" / "iterations"
        )
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _file_path(self, turn_key: str) -> Path:
        safe = turn_key.replace("/", "_").replace("\\", "_")
        return self.storage_dir / f"{safe}.json"

    def save(self, turn_key: str, record: dict) -> None:
        path = self._file_path(turn_key)
        existing: list[dict] = []
        if path.exists():
            existing = json.loads(path.read_text(encoding="utf-8"))
        record["saved_at"] = datetime.now(timezone.utc).isoformat()
        existing.append(record)
        path.write_text(
            json.dumps(existing, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def get(self, turn_key: str) -> list[dict]:
        path = self._file_path(turn_key)
        if not path.exists():
            return []
        return json.loads(path.read_text(encoding="utf-8"))

    def get_demo(self, demo_id: str) -> dict | None:
        demo_path = (
            Path(__file__).resolve().parent.parent
            / "data" / "demo" / "demo-iterations.json"
        )
        if not demo_path.exists():
            return None
        demos = json.loads(demo_path.read_text(encoding="utf-8"))
        return demos.get(demo_id)
