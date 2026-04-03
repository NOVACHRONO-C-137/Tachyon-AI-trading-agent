import time

def safe_divide(a, b, default=0):
    if b == 0:
        return default
    return a / b

def format_usd(amount):
    return f"${amount:,.2f}"

def format_percent(value):
    return f"{value:.2f}%"

def extract_symbol(pair):
    return pair.split("/")[0]

def is_market_hours():
    return True

def retry(func, max_attempts=3, delay=2):
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            if attempt < max_attempts - 1:
                time.sleep(delay)
            else:
                raise e