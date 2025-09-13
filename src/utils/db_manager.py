import sqlite3
from typing import Any, List, Optional, Tuple

from src.data.constants import DATA_FILE_PATH


class DbManager:
    def __init__(self):
        self.conn: Optional[sqlite3.Connection] = None

    def __enter__(self) -> "DbManager":
        self.conn = sqlite3.connect(DATA_FILE_PATH)
        self.conn.row_factory = sqlite3.Row
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if not self.conn:
            return
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        self.conn.close()
        self.conn = None

    def execute(self, query: str, params: Tuple[Any, ...] = ()) -> None:
        if not self.conn:
            raise RuntimeError("DbManager must be used as a context manager (with DbManager() as db).")
        cur = self.conn.execute(query, params)
        cur.close()

    def execute_fetchall(self, query: str, params: Tuple[Any, ...] = ()) -> List[sqlite3.Row]:
        if not self.conn:
            raise RuntimeError("DbManager must be used as a context manager.")
        cur = self.conn.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        return rows

    def execute_fetchone(self, query: str, params: Tuple[Any, ...] = ()) -> Optional[sqlite3.Row]:
        if not self.conn:
            raise RuntimeError("DbManager must be used as a context manager.")
        cur = self.conn.execute(query, params)
        row = cur.fetchone()
        cur.close()
        return row
