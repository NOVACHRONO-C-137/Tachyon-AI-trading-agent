import os
import json
from datetime import datetime

def get_timestamp():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log(message, level="INFO"):
    timestamp = get_timestamp()
    log_line = f"[{timestamp}] [{level}] {message}"
    print(log_line)
    os.makedirs("logs", exist_ok=True)
    with open("logs/trades.log", "a") as f:
        f.write(log_line + "\n")

def log_trade(action, pair, amount, price, reason):
    trade_record = {
        "timestamp": get_timestamp(),
        "action": action,
        "pair": pair,
        "amount": amount,
        "price": price,
        "usd_value": amount * price,
        "reason": reason
    }
    log(f"TRADE: {action} {amount} {pair} @ ${price:,.2f} | Reason: {reason}", level="TRADE")
    os.makedirs("logs", exist_ok=True)
    with open("logs/trade_history.json", "a") as f:
        f.write(json.dumps(trade_record) + "\n")
    return trade_record
