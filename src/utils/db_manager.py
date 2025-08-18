import sqlite3
from typing import Any, List, Optional, Tuple
from src.data.constants import data_file_path


class DbManager:
    def __init__(self, path: str = data_file_path):
        self.path = path
        self.conn: Optional[sqlite3.Connection] = None

    def __enter__(self) -> "DbManager":
        self.conn = sqlite3.connect(self.path)
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

    @staticmethod
    def create_tables(path: str = data_file_path) -> None:
        create_sql = """
        CREATE TABLE IF NOT EXISTS strikes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hash VARCHAR(255) NOT NULL UNIQUE,
            strikes INTEGER NOT NULL,
            first_strike TIMESTAMP NOT NULL
        );
        """
        with DbManager(path) as db:
            db.execute(create_sql)
