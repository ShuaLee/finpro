from datetime import datetime
from decimal import Decimal


def parse_decimal(value):
    try:
        return Decimal(str(value)) if value is not None else None
    except:
        return None


def parse_date(value):
    try:
        return datetime.fromtimestamp(value).date() if value else None
    except:
        return None
