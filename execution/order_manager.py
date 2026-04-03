from execution.kraken_mcp import (
    place_market_order,
    place_limit_order,
    get_balance,
    get_open_orders
)
from utils.logger import log

def execute_buy(pair, crypto_amount, price):
    log(f"Executing BUY: {crypto_amount} {pair} @ ${price:,.2f}")
    usd_amount = crypto_amount * price
    balance = get_balance()
    usd_available = balance.get("USD", 0)
    if usd_amount > usd_available:
        log(f"Not enough USD. Need ${usd_amount:.2f}, have ${usd_available:.2f}", level="WARN")
        return None
    result = place_market_order("BUY", pair, crypto_amount)
    if result:
        log(f"BUY order success: {result.get('order_id', 'unknown')}")
    return result

def execute_sell(pair, crypto_amount, price):
    log(f"Executing SELL: {crypto_amount} {pair} @ ${price:,.2f}")
    symbol = pair.split("/")[0]
    balance = get_balance()
    crypto_available = balance.get(symbol, 0)
    if crypto_amount > crypto_available:
        log(f"Not enough {symbol}. Need {crypto_amount}, have {crypto_available}", level="WARN")
        return None
    result = place_market_order("SELL", pair, crypto_amount)
    if result:
        log(f"SELL order success: {result.get('order_id', 'unknown')}")
    return result

def execute_trade(action, pair, crypto_amount, price):
    if action == "BUY":
        return execute_buy(pair, crypto_amount, price)
    elif action == "SELL":
        return execute_sell(pair, crypto_amount, price)
    else:
        log(f"Unknown action: {action}", level="ERROR")
        return None