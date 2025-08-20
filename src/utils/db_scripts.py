from src.utils.db_manager import DbManager
from src.utils.strike_utils import StrikeType


class DbScripts:
    def create_tables(self) -> None:
        for strike_type in StrikeType:
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS {strike_type.value}_strikes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hash VARCHAR(255) NOT NULL,
                timestamp TIMESTAMP NOT NULL
            );
            """
            with DbManager() as db:
                db.execute(create_sql)
