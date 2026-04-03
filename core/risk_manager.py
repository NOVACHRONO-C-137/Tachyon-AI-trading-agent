from config.settings import (
    MAX_TRADE_USD, MAX_RISK_PERCENT, DAILY_LOSS_LIMIT_USD,
    MAX_OPEN_POSITIONS, STOP_LOSS_PERCENT, TAKE_PROFIT_PERCENT
)
from utils.logger import log

def check_trade(decision, portfolio_state):
    action = decision.get("action", "HOLD")
    price = decision.get("price", 0)
    if action == "HOLD":
        return {"approved": False, "reason": "Action is HOLD"}
    if price <= 0:
        log("BLOCKED: Invalid price", level="WARN")
        return {"approved": False, "reason": "Invalid price data"}
    daily_loss = portfolio_state.get("daily_loss", 0)
    if daily_loss >= DAILY_LOSS_LIMIT_USD:
        log(f"BLOCKED: Daily loss limit hit (${daily_loss:.2f})", level="WARN")
        return {"approved": False, "reason": f"Daily loss limit reached: ${daily_loss:.2f}"}
    open_positions = portfolio_state.get("open_positions", [])
    if action == "BUY" and len(open_positions) >= MAX_OPEN_POSITIONS:
        log(f"BLOCKED: Max positions reached ({len(open_positions)})", level="WARN")
        return {"approved": False, "reason": "Max open positions reached"}
    if action == "SELL" and len(open_positions) == 0:
        log("BLOCKED: No positions to sell", level="WARN")
        return {"approved": False, "reason": "No open positions to sell"}
    balance = portfolio_state.get("balance", 0)
    max_by_percent = balance * MAX_RISK_PERCENT
    trade_amount_usd = min(MAX_TRADE_USD, max_by_percent)
    if trade_amount_usd < 1:
        log("BLOCKED: Trade amount too small", level="WARN")
        return {"approved": False, "reason": "Insufficient balance"}
    if action == "BUY":
        stop_loss_price = price * (1 - STOP_LOSS_PERCENT)
        take_profit_price = price * (1 + TAKE_PROFIT_PERCENT)
    else:
        stop_loss_price = None
        take_profit_price = None
    crypto_amount = trade_amount_usd / price
    result = {
        "approved": True,
        "reason": "All risk checks passed",
        "trade_amount_usd": round(trade_amount_usd, 2),
        "crypto_amount": round(crypto_amount, 8),
        "stop_loss_price": round(stop_loss_price, 2) if stop_loss_price else None,
        "take_profit_price": round(take_profit_price, 2) if take_profit_price else None
    }
    log(f"APPROVED: ${trade_amount_usd:.2f} | SL: {stop_loss_price} | TP: {take_profit_price}")
    return result