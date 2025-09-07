from pathlib import Path
import tempfile
import unittest

from quickcapture.services import (
    add_note,
    add_task,
    complete_task,
    export_all,
    init_db,
    list_notes,
    list_tasks,
)


class ServicesTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "t.db"
        self.db = init_db(self.db_path)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_add_and_list_note(self):
        nid = add_note(self.db, "Note A", "Hello")
        self.assertIsInstance(nid, int)
        notes = list_notes(self.db)
        self.assertTrue(any(n.title == "Note A" for n in notes))

    def test_add_complete_task(self):
        tid = add_task(self.db, "Task A")
        self.assertIsInstance(tid, int)
        tasks_open = list_tasks(self.db, completed=False)
        self.assertTrue(any(t.id == tid for t in tasks_open))
        ok = complete_task(self.db, tid)
        self.assertTrue(ok)
        tasks_done = list_tasks(self.db, completed=True)
        self.assertTrue(any(t.id == tid for t in tasks_done))

    def test_export(self):
        add_note(self.db, "N1")
        add_task(self.db, "T1")
        data = export_all(self.db)
        self.assertIn("notes", data)
        self.assertIn("tasks", data)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
