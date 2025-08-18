from src.utils.db_manager import DbManager
from src.utils.strike_utils import StrikeType
from src.data.constants import data_file_path


class DbScripts:
    def create_tables(self, path: str = data_file_path) -> None:
        for strike_type in StrikeType:
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS {strike_type.value}_strikes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hash VARCHAR(255) NOT NULL UNIQUE,
                strikes INTEGER NOT NULL,
                first_strike TIMESTAMP NOT NULL
            );
            """
            with DbManager(path) as db:
                db.execute(create_sql)
