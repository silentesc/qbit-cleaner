from datetime import datetime


class DateTimeUtils:
    def get_datetime_readable(self, dt: datetime) -> str:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
