#!/usr/bin/env python3
"""SQLite-backed model registry for WebUI model/test artifacts."""

from __future__ import annotations

import json
import os
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional


MODEL_EXTENSIONS = {".h5", ".keras", ".pt", ".pth", ".onnx", ".joblib", ".pkl", ".pickle"}
SKIP_PATH_PARTS = {".venv", ".venv_test", "site-packages", "__pycache__", "node_modules", "TrashDump"}


def _iso_from_ts(ts: float) -> str:
    return datetime.utcfromtimestamp(ts).isoformat()


class ModelRegistryDB:
    def __init__(self, db_path: Path, project_root: Path):
        self.db_path = db_path
        self.project_root = project_root
        self.registry_root = self.db_path.parent
        self.artifacts_root = self.registry_root / "artifacts"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.artifacts_root.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS model_registry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    model_name TEXT NOT NULL,
                    path TEXT NOT NULL UNIQUE,
                    model_format TEXT,
                    size_bytes INTEGER,
                    created_at TEXT,
                    modified_at TEXT,
                    source TEXT,
                    notes TEXT,
                    metrics_json TEXT,
                    test_artifact INTEGER NOT NULL DEFAULT 1,
                    last_seen_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_model_registry_seen
                ON model_registry(last_seen_at DESC)
                """
            )
            conn.commit()

    def _to_rel_path(self, file_path: Path) -> str:
        try:
            return str(file_path.resolve().relative_to(self.project_root.resolve()))
        except Exception:
            return str(file_path)

    def _normalize_model_row(self, row: sqlite3.Row) -> Dict:
        item = dict(row)
        raw_metrics = item.get("metrics_json")
        if raw_metrics:
            try:
                item["metrics"] = json.loads(raw_metrics)
            except json.JSONDecodeError:
                item["metrics"] = None
        else:
            item["metrics"] = None
        item.pop("metrics_json", None)
        item["test_artifact"] = bool(item.get("test_artifact", 1))
        return item

    def _is_relative_to(self, path: Path, base: Path) -> bool:
        try:
            path.resolve().relative_to(base.resolve())
            return True
        except Exception:
            return False

    def _stage_model_file(self, source_path: Path) -> tuple[Path, str | None]:
        resolved = source_path.resolve()
        registry_root_resolved = self.registry_root.resolve()
        if self._is_relative_to(resolved, registry_root_resolved):
            return resolved, None

        try:
            rel = resolved.relative_to(self.project_root.resolve())
            stage_rel = rel
            origin_rel = str(rel)
        except Exception:
            stage_rel = Path("external") / resolved.name
            origin_rel = str(resolved)

        staged_path = (self.artifacts_root / stage_rel).resolve()
        staged_path.parent.mkdir(parents=True, exist_ok=True)

        should_copy = True
        if staged_path.exists():
            try:
                src_stat = resolved.stat()
                dst_stat = staged_path.stat()
                should_copy = (src_stat.st_size != dst_stat.st_size) or (int(src_stat.st_mtime) != int(dst_stat.st_mtime))
            except OSError:
                should_copy = True

        if should_copy:
            shutil.copy2(resolved, staged_path)

        return staged_path, origin_rel

    def register_model(
        self,
        path: Path,
        source: str = "manual",
        notes: str = "",
        metrics: Optional[Dict] = None,
        test_artifact: bool = True,
    ) -> Dict:
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Model path not found: {path}")

        staged_path, origin_rel = self._stage_model_file(path)
        stat = staged_path.stat()
        rel_path = self._to_rel_path(staged_path)
        now = datetime.utcnow().isoformat()
        merged_notes = notes
        if origin_rel and origin_rel != rel_path and "origin=" not in merged_notes:
            merged_notes = f"{merged_notes} | origin={origin_rel}".strip(" |")
        payload = {
            "model_name": staged_path.name,
            "path": rel_path,
            "model_format": staged_path.suffix.lower().lstrip("."),
            "size_bytes": int(stat.st_size),
            "created_at": _iso_from_ts(stat.st_ctime),
            "modified_at": _iso_from_ts(stat.st_mtime),
            "source": source,
            "notes": merged_notes,
            "metrics_json": json.dumps(metrics) if metrics else None,
            "test_artifact": 1 if test_artifact else 0,
            "last_seen_at": now,
        }

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO model_registry (
                    model_name, path, model_format, size_bytes,
                    created_at, modified_at, source, notes,
                    metrics_json, test_artifact, last_seen_at
                ) VALUES (
                    :model_name, :path, :model_format, :size_bytes,
                    :created_at, :modified_at, :source, :notes,
                    :metrics_json, :test_artifact, :last_seen_at
                )
                ON CONFLICT(path) DO UPDATE SET
                    model_name=excluded.model_name,
                    model_format=excluded.model_format,
                    size_bytes=excluded.size_bytes,
                    created_at=excluded.created_at,
                    modified_at=excluded.modified_at,
                    source=excluded.source,
                    notes=CASE
                        WHEN excluded.notes IS NOT NULL AND excluded.notes != '' THEN excluded.notes
                        ELSE model_registry.notes
                    END,
                    metrics_json=COALESCE(excluded.metrics_json, model_registry.metrics_json),
                    test_artifact=excluded.test_artifact,
                    last_seen_at=excluded.last_seen_at
                """,
                payload,
            )
            conn.commit()

        return self.get_model_by_path(rel_path) or payload

    def get_model_by_path(self, rel_path: str) -> Optional[Dict]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM model_registry WHERE path = ?", (rel_path,)).fetchone()
        return self._normalize_model_row(row) if row else None

    def get_model(self, model_id: int) -> Optional[Dict]:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM model_registry WHERE id = ?", (int(model_id),)).fetchone()
        return self._normalize_model_row(row) if row else None

    def list_models(self, limit: int = 100) -> List[Dict]:
        capped = max(1, min(int(limit), 1000))
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM model_registry ORDER BY modified_at DESC, id DESC LIMIT ?",
                (capped,),
            ).fetchall()
        return [self._normalize_model_row(row) for row in rows]

    def count_models(self) -> int:
        with self._connect() as conn:
            row = conn.execute("SELECT COUNT(*) AS c FROM model_registry").fetchone()
        return int(row["c"] if row else 0)

    def sync_from_directories(self, directories: Iterable[Path], source: str = "autosync") -> Dict:
        seen = 0
        updated = 0
        errors: List[str] = []

        for directory in directories:
            if not directory.exists() or not directory.is_dir():
                continue
            # Use os.walk with followlinks=False to avoid symlink loops on Python 3.10.
            for root, dirs, files in os.walk(directory, followlinks=False):
                root_path = Path(root)
                # Skip hidden/virtual env/cache directories in-place.
                dirs[:] = [
                    d for d in dirs
                    if d not in SKIP_PATH_PARTS and not d.startswith(".")
                ]
                if any(part in SKIP_PATH_PARTS for part in root_path.parts):
                    continue
                for fname in files:
                    file_path = root_path / fname
                    if not file_path.is_file():
                        continue
                    if any(part in SKIP_PATH_PARTS for part in file_path.parts):
                        continue
                    if file_path.suffix.lower() not in MODEL_EXTENSIONS:
                        continue
                seen += 1
                try:
                    self.register_model(file_path, source=source, test_artifact=True)
                    updated += 1
                except Exception as exc:
                    errors.append(f"{file_path}: {exc}")

        return {
            "scanned": seen,
            "updated": updated,
            "errors": errors,
            "total_models": self.count_models(),
        }

    def migrate_registry_paths_to_server(self) -> Dict:
        migrated = 0
        skipped = 0
        errors: List[str] = []

        with self._connect() as conn:
            rows = conn.execute("SELECT id, path, source, notes, test_artifact FROM model_registry ORDER BY id ASC").fetchall()

        for row in rows:
            stored_path = str(row["path"])
            stored_obj = Path(stored_path)
            if stored_obj.is_absolute():
                source_path = stored_obj
            else:
                source_path = (self.project_root / stored_obj).resolve()

            if self._is_relative_to(source_path, self.registry_root):
                skipped += 1
                continue

            if not source_path.exists() or not source_path.is_file():
                skipped += 1
                continue

            try:
                self.register_model(
                    source_path,
                    source=str(row["source"] or "migration"),
                    notes=str(row["notes"] or ""),
                    test_artifact=bool(row["test_artifact"]),
                )
                with self._connect() as conn:
                    conn.execute("DELETE FROM model_registry WHERE id = ?", (int(row["id"]),))
                    conn.commit()
                migrated += 1
            except Exception as exc:
                errors.append(f"{stored_path}: {exc}")

        return {"migrated": migrated, "skipped": skipped, "errors": errors, "total_models": self.count_models()}
