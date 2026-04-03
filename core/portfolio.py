from utils.logger import log, log_trade
from utils.state import save_state, load_state
from datetime import datetime

STARTING_BALANCE = 10000.00

def get_portfolio():
    state = load_state()
    if "balance" not in state:
        state["balance"] = STARTING_BALANCE
    return state

def update_balance(state, amount):
    state["balance"] = round(state["balance"] + amount, 2)
    save_state(state)
    return state

def open_position(state, pair, action, crypto_amount, price, stop_loss, take_profit, reason):
    position = {
        "id": state["total_trades"] + 1,
        "pair": pair,
        "action": action,
        "amount": crypto_amount,
        "entry_price": price,
        "current_price": price,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "usd_value": round(crypto_amount * price, 2),
        "pnl": 0,
        "reason": reason,
        "opened_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    state["open_positions"].append(position)
    state["total_trades"] += 1
    state["balance"] -= position["usd_value"]
    log_trade(action, pair, crypto_amount, price, reason)
    save_state(state)
    log(f"Position opened: #{position['id']} {action} {crypto_amount} {pair} @ ${price:,.2f}")
    return state, position

def close_position(state, position_id, current_price, reason):
    position = None
    position_index = None
    for i, pos in enumerate(state["open_positions"]):
        if pos["id"] == position_id:
            position = pos
            position_index = i
            break
    if position is None:
        log(f"Position #{position_id} not found", level="ERROR")
        return state, None
    entry_price = position["entry_price"]
    amount = position["amount"]
    if position["action"] == "BUY":
        pnl = (current_price - entry_price) * amount
    else:
        pnl = (entry_price - current_price) * amount
    pnl = round(pnl, 2)
    state["open_positions"].pop(position_index)
    state["balance"] += round(current_price * amount, 2)
    state["closed_trades"] += 1
    state["daily_pnl"] += pnl
    state["total_pnl"] += pnl
    log(f"Position closed: #{position_id} | PnL: ${pnl:.2f} | Reason: {reason}")
    log_trade("CLOSE", position["pair"], amount, current_price, reason)
    save_state(state)
    return state, position