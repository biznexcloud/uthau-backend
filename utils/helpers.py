import random
import string
from core.config import settings


def generate_crn() -> str:
    return "UTH-" + "".join(random.choices(string.digits, k=8))


def format_currency(amount: float) -> str:
    return f"{settings.CURRENCY_SYMBOL} {amount:,.2f}"
