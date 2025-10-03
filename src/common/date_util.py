import datetime


def parse_search_to_date(date_str: str):
    # "2023.06.03." → "2023-06-03"
    try:
        return (datetime.datetime.strptime(
            date_str.strip('.'),
            "%Y.%m.%d")
                .date())
    except Exception:
        return None


def parse_date_to_search(date: str):
    try:
        date_obj = datetime.datetime.strptime(date, "%Y-%m-%d").date()
        return date_obj.strftime("%Y.%m.%d")
    except Exception:
        return None
