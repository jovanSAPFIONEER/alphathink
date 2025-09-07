from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .db import Database, default_db_path
from .models import Note, Task


def init_db(db_path: Optional[Path] = None) -> Database:
    return Database(db_path or default_db_path())


def add_note(db: Database, title: str, content: Optional[str] = None) -> int:
    note = Note(title=title, content=content)
    with db.connect() as conn:
        cur = conn.execute(
            "INSERT INTO notes(title, content, created_at) VALUES (?, ?, ?)",
            (note.title, note.content, note.created_at.isoformat()),
        )
        last_id = cur.lastrowid if cur.lastrowid is not None else 0
        return int(last_id)


def add_task(db: Database, title: str, due_at: Optional[datetime] = None) -> int:
    task = Task(title=title, due_at=due_at)
    with db.connect() as conn:
        cur = conn.execute(
            "INSERT INTO tasks(title, due_at, completed_at, created_at) VALUES (?, ?, ?, ?)",
            (
                task.title,
                task.due_at.isoformat() if task.due_at else None,
                None,
                task.created_at.isoformat(),
            ),
        )
        last_id = cur.lastrowid if cur.lastrowid is not None else 0
        return int(last_id)


def list_notes(db: Database) -> List[Note]:
    with db.connect() as conn:
        rows = conn.execute("SELECT * FROM notes ORDER BY created_at DESC").fetchall()
        return [
            Note(
                id=row["id"],
                title=row["title"],
                content=row["content"],
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]


def list_tasks(db: Database, completed: Optional[bool] = None) -> List[Task]:
    query = "SELECT * FROM tasks"
    params: Tuple[object, ...] = ()
    if completed is True:
        query += " WHERE completed_at IS NOT NULL"
    elif completed is False:
        query += " WHERE completed_at IS NULL"
    query += " ORDER BY created_at DESC"

    with db.connect() as conn:
        rows = conn.execute(query, params).fetchall()
        return [
            Task(
                id=row["id"],
                title=row["title"],
                due_at=datetime.fromisoformat(row["due_at"]) if row["due_at"] else None,
                completed_at=(
                    datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None
                ),
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]


def complete_task(db: Database, task_id: int) -> bool:
    with db.connect() as conn:
        now = datetime.now(timezone.utc).isoformat()
        cur = conn.execute(
            "UPDATE tasks SET completed_at=? WHERE id=? AND completed_at IS NULL",
            (now, task_id),
        )
        return cur.rowcount > 0


def export_all(db: Database) -> Dict[str, object]:
    notes = list_notes(db)
    tasks = list_tasks(db)
    return {
        "notes": [
            {
                "id": n.id,
                "title": n.title,
                "content": n.content,
                "created_at": n.created_at.isoformat(),
            }
            for n in notes
        ],
        "tasks": [
            {
                "id": t.id,
                "title": t.title,
                "due_at": t.due_at.isoformat() if t.due_at else None,
                "completed_at": t.completed_at.isoformat() if t.completed_at else None,
                "created_at": t.created_at.isoformat(),
            }
            for t in tasks
        ],
    }


def export_all_json(db: Database, indent: int = 2) -> str:
    return json.dumps(export_all(db), indent=indent)
