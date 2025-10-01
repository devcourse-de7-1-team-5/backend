import datetime


def parse_date(date_str: str):
    # "2023.06.03." → "2023-06-03"
    try:
        return (datetime.datetime.strptime(
            date_str.strip('.'),
            "%Y.%m.%d")
                .date())
    except Exception:
        return None
