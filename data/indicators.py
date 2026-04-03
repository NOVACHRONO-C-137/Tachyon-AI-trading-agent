price_history = []
MAX_HISTORY = 100

def add_price(price):
    price_history.append(price)
    if len(price_history) > MAX_HISTORY:
        price_history.pop(0)

def get_sma(period=20):
    if len(price_history) < period:
        return None
    return sum(price_history[-period:]) / period

def get_ema(period=20):
    if len(price_history) < period:
        return None
    multiplier = 2 / (period + 1)
    ema = price_history[0]
    for price in price_history[1:]:
        ema = (price * multiplier) + (ema * (1 - multiplier))
    return ema

def get_rsi(period=14):
    if len(price_history) < period + 1:
        return None
    gains = []
    losses = []
    recent = price_history[-(period + 1):]
    for i in range(1, len(recent)):
        change = recent[i] - recent[i-1]
        if change > 0:
            gains.append(change)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(change))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_price_change_percent():
    if len(price_history) < 2:
        return 0
    old_price = price_history[-min(10, len(price_history))]
    current_price = price_history[-1]
    if old_price == 0:
        return 0
    return ((current_price - old_price) / old_price) * 100

def get_all_indicators():
    return {
        "sma_20": get_sma(20),
        "ema_20": get_ema(20),
        "rsi_14": get_rsi(14),
        "price_change_pct": get_price_change_percent(),
        "current_price": price_history[-1] if price_history else None,
        "history_length": len(price_history)
    }