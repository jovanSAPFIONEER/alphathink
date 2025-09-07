from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from .services import (
    add_note,
    add_task,
    complete_task,
    export_all_json,
    init_db,
    list_notes,
    list_tasks,
)

logger = logging.getLogger(__name__)


def _parse_date(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value)
    except Exception as exc:  # noqa: BLE001
        raise argparse.ArgumentTypeError(f"Invalid date format (use YYYY-MM-DD or ISO8601): {value}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="quickcapture", description="Capture notes and tasks into SQLite.")
    parser.add_argument("--db", type=Path, default=None, help="Path to SQLite DB (defaults to ~/.quickcapture/quickcapture.db)")

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_add_note = sub.add_parser("add-note", help="Add a new note")
    p_add_note.add_argument("title")
    p_add_note.add_argument("--content", default=None)

    p_add_task = sub.add_parser("add-task", help="Add a new task")
    p_add_task.add_argument("title")
    p_add_task.add_argument("--due", type=_parse_date, default=None, help="Due date (YYYY-MM-DD or ISO8601)")

    p_list = sub.add_parser("list", help="List notes and tasks")
    p_list.add_argument("--type", choices=["notes", "tasks", "all"], default="all")
    p_list.add_argument("--completed", choices=["true", "false"], default=None, help="For tasks: filter by completion")

    p_complete = sub.add_parser("complete-task", help="Mark a task completed")
    p_complete.add_argument("id", type=int)

    p_export = sub.add_parser("export", help="Export all items to JSON")
    p_export.add_argument("--out", type=Path, default=None, help="Output file (defaults to stdout)")

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    argv = list(argv) if argv is not None else sys.argv[1:]
    parser = build_parser()
    args = parser.parse_args(argv)

    db = init_db(args.db)

    if args.cmd == "add-note":
        note_id = add_note(db, args.title, args.content)
        logger.info("Added note %s", note_id)
        print(note_id)
        return 0

    if args.cmd == "add-task":
        task_id = add_task(db, args.title, args.due)
        logger.info("Added task %s", task_id)
        print(task_id)
        return 0

    if args.cmd == "list":
        t = args.type
        completed_opt = None
        if args.completed == "true":
            completed_opt = True
        elif args.completed == "false":
            completed_opt = False

        if t in ("all", "notes"):
            for n in list_notes(db):
                print(f"NOTE #{n.id}: {n.title} -- {n.content or ''} ({n.created_at.isoformat()})")

        if t in ("all", "tasks"):
            for k in list_tasks(db, completed=completed_opt):
                status = "done" if k.completed_at else "open"
                due = k.due_at.date().isoformat() if k.due_at else "-"
                print(f"TASK #{k.id} [{status}] (due {due}): {k.title}")
        return 0

    if args.cmd == "complete-task":
        ok = complete_task(db, args.id)
        print("OK" if ok else "NOT-CHANGED")
        return 0 if ok else 1

    if args.cmd == "export":
        content = export_all_json(db)
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(content, encoding="utf-8")
            print(str(args.out))
        else:
            print(content)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
