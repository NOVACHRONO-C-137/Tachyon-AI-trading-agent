import time
from datetime import datetime
from config.settings import CHECK_INTERVAL, TRADING_PAIR, STOP_LOSS_PERCENT, TAKE_PROFIT_PERCENT
from core.strategy import analyze_market
from core.risk_manager import check_trade
from execution.kraken_mcp import KrakenExecutionEngine
from utils.logger import log
from utils.state import save_state

CHECK_AMOUNT = 100

def check_stop_loss_take_profit(open_positions, current_price):
    positions_to_close = []
    for position in open_positions:
        entry_price = position["entry_price"]
        if position["action"] == "BUY":
            pnl_percent = (current_price - entry_price) / entry_price
            if pnl_percent <= -STOP_LOSS_PERCENT:
                positions_to_close.append((position["id"], "STOP LOSS triggered"))
            elif pnl_percent >= TAKE_PROFIT_PERCENT:
                positions_to_close.append((position["id"], "TAKE PROFIT triggered"))
    return positions_to_close

def run_bot():
    log("=" * 60)
    log("KRAKEN AI TRADING AGENT - STARTING")
    log(f"Trading pair: {TRADING_PAIR}")
    log(f"Check interval: {CHECK_INTERVAL} seconds")
    log(f"Mode: PAPER TRADING")
    log("=" * 60)
    
    engine = KrakenExecutionEngine()
    portfolio = engine.get_portfolio_status()
    log(f"Starting balance: ${portfolio.get('balance', 'N/A')}")
    
    cycle_count = 0
    while True:
        try:
            cycle_count += 1
            log(f"--- Cycle #{cycle_count} ---")
            
            portfolio = engine.get_portfolio_status()
            if portfolio:
                log(f"Wallet: {portfolio}")
            
            current_price = engine.get_market_price("SOLUSD")
            if current_price is None:
                log("Could not get market price. Skipping cycle.", level="WARN")
                time.sleep(CHECK_INTERVAL)
                continue
            
            log(f"Current SOLUSD price: ${current_price}")
            
            decision = analyze_market()
            if decision is None or decision.get("action") == "HOLD":
                log("No trade signal. Holding.")
                time.sleep(CHECK_INTERVAL)
                continue
            
            action = decision["action"]
            pair = decision["pair"]
            
            if action in ["BUY", "SELL"]:
                trade_amount = CHECK_AMOUNT / current_price
                log(f"Executing {action} for {trade_amount:.4f} SOL at ${current_price}")
                result = engine.execute_trade(action, "SOLUSD", trade_amount)
                if result:
                    log(f"{action} order executed successfully")
                else:
                    log(f"{action} order failed", level="ERROR")
            
            log(f"Next check in {CHECK_INTERVAL} seconds...")
            time.sleep(CHECK_INTERVAL)
            
        except KeyboardInterrupt:
            log("Bot stopped by user (Ctrl+C)")
            break
        except Exception as e:
            log(f"Unexpected error: {e}", level="ERROR")
            log("Retrying in 60 seconds...")
            time.sleep(60)

if __name__ == "__main__":
    run_bot()