from datetime import datetime, timedelta

def format_date(date_obj: datetime, format_str: str = "%Y-%m-%d") -> str:
    return date_obj.strftime(format_str)

def parse_date(date_str: str, format_str: str = "%Y-%m-%d") -> datetime:
    return datetime.strptime(date_str, format_str)

def get_week_range(date: datetime = None) -> tuple:
    if date is None:
        date = datetime.now()
    start_of_week = date - timedelta(days=date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    return (start_of_week, end_of_week)

def get_month_range(date: datetime = None) -> tuple:
    if date is None:
        date = datetime.now()
    start_of_month = date.replace(day=1)
    if date.month == 12:
        end_of_month = date.replace(year=date.year + 1, month=1, day=1) - timedelta(days=1)
    else:
        end_of_month = date.replace(month=date.month + 1, day=1) - timedelta(days=1)
    return (start_of_month, end_of_month)

def is_same_day(date1: datetime, date2: datetime) -> bool:
    return date1.date() == date2.date()