import time
from datetime import datetime
from config.settings import CHECK_INTERVAL, TRADING_PAIR, STOP_LOSS_PERCENT, TAKE_PROFIT_PERCENT
from core.strategy import analyze_market
from core.risk_manager import check_trade
from core.portfolio import get_portfolio, open_position, close_position
from execution.order_manager import execute_trade
from utils.logger import log
from utils.state import save_state

def check_stop_loss_take_profit(state, current_price):
    positions_to_close = []
    for position in state["open_positions"]:
        entry_price = position["entry_price"]
        if position["action"] == "BUY":
            pnl_percent = (current_price - entry_price) / entry_price
            if pnl_percent <= -STOP_LOSS_PERCENT:
                positions_to_close.append((position["id"], "STOP LOSS triggered"))
            elif pnl_percent >= TAKE_PROFIT_PERCENT:
                positions_to_close.append((position["id"], "TAKE PROFIT triggered"))
    for position_id, reason in positions_to_close:
        state, closed = close_position(state, position_id, current_price, reason)
        if closed:
            log(f"Auto-closed position #{position_id}: {reason}")
    return state

def run_single_cycle():
    log("=" * 50)
    log("Starting new trading cycle...")
    state = get_portfolio()
    if not state.get("is_running", True):
        log("Bot is stopped. Not trading.", level="WARN")
        return state
    decision = analyze_market()
    if decision is None:
        log("No decision made. Skipping cycle.", level="WARN")
        return state
    current_price = decision.get("price", 0)
    if current_price > 0 and len(state["open_positions"]) > 0:
        state = check_stop_loss_take_profit(state, current_price)
    risk_check = check_trade(decision, state)
    if not risk_check["approved"]:
        log(f"Trade blocked: {risk_check['reason']}")
        state["last_check_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_state(state)
        return state
    action = decision["action"]
    pair = decision["pair"]
    crypto_amount = risk_check["crypto_amount"]
    price = decision["price"]
    reason = decision.get("reason", "strategy signal")
    order_result = execute_trade(action, pair, crypto_amount, price)
    if order_result is None:
        log("Order execution failed", level="ERROR")
        return state
    if action == "BUY":
        state, position = open_position(
            state=state,
            pair=pair,
            action=action,
            crypto_amount=crypto_amount,
            price=price,
            stop_loss=risk_check["stop_loss_price"],
            take_profit=risk_check["take_profit_price"],
            reason=reason
        )
    elif action == "SELL":
        if len(state["open_positions"]) > 0:
            oldest_position = state["open_positions"][0]
            state, closed = close_position(
                state=state,
                position_id=oldest_position["id"],
                current_price=price,
                reason=reason
            )
    state["last_check_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_state(state)
    log(f"Cycle complete. Balance: ${state['balance']:,.2f} | Open positions: {len(state['open_positions'])} | Total PnL: ${state['total_pnl']:,.2f}")
    return state

def run_bot():
    log("=" * 60)
    log("KRAKEN AI TRADING AGENT - STARTING")
    log(f"Trading pair: {TRADING_PAIR}")
    log(f"Check interval: {CHECK_INTERVAL} seconds")
    log(f"Mode: PAPER TRADING")
    log("=" * 60)
    state = get_portfolio()
    log(f"Starting balance: ${state['balance']:,.2f}")
    cycle_count = 0
    while True:
        try:
            cycle_count += 1
            log(f"--- Cycle #{cycle_count} ---")
            state = run_single_cycle()
            log(f"Next check in {CHECK_INTERVAL} seconds...")
            time.sleep(CHECK_INTERVAL)
        except KeyboardInterrupt:
            log("Bot stopped by user (Ctrl+C)")
            state["is_running"] = False
            save_state(state)
            break
        except Exception as e:
            log(f"Unexpected error: {e}", level="ERROR")
            log("Retrying in 60 seconds...")
            time.sleep(60)

if __name__ == "__main__":
    run_bot()