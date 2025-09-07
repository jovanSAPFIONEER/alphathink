from typing import Optional
from datetime import datetime, timezone


class Note:
    id: Optional[int]
    title: str
    content: Optional[str]
    created_at: datetime

    def __init__(self, title: str, content: Optional[str] = None, id: Optional[int] = None, created_at: Optional[datetime] = None):
        self.id = id
        self.title = title
        self.content = content
        self.created_at = created_at or datetime.now(timezone.utc)


class Task:
    id: Optional[int]
    title: str
    due_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    def __init__(self, title: str, due_at: Optional[datetime] = None, id: Optional[int] = None, created_at: Optional[datetime] = None, completed_at: Optional[datetime] = None):
        self.id = id
        self.title = title
        self.due_at = due_at
        self.completed_at = completed_at
        self.created_at = created_at or datetime.now(timezone.utc)
