import subprocess
import json
import random
from datetime import datetime
from utils.logger import log

KRAKEN_CLI_PATH = "kraken-cli"
PAPER_MODE = True

# Simulated exchange state (like a devnet)
paper_account = {
    "balance": {
        "USD": 10000.00,
        "BTC": 0.0,
        "ETH": 0.0,
        "SOL": 0.0
    },
    "orders": [],
    "trade_history": [],
    "order_counter": 0
}


def get_slippage():
    """
    Simulate real-world slippage
    When you buy/sell on a real exchange, the price you get
    is slightly different from the price you saw.
    This simulates that reality.
    """
    return random.uniform(-0.002, 0.002)  # -0.2% to +0.2%


def get_trading_fee():
    """
    Kraken charges 0.16% maker / 0.26% taker fees
    We simulate taker fees (market orders)
    """
    return 0.0026  # 0.26%


def simulate_fill_price(price, action):
    """
    In real exchanges, buy orders fill slightly ABOVE market price
    and sell orders fill slightly BELOW market price (slippage)
    """
    slippage = get_slippage()
    if action == "BUY":
        # You pay slightly more than market price
        fill_price = price * (1 + abs(slippage))
    else:
        # You receive slightly less than market price
        fill_price = price * (1 - abs(slippage))
    return round(fill_price, 2)


def run_kraken_command(args):
    try:
        cmd = [KRAKEN_CLI_PATH] + args
        log(f"Running Kraken CLI: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"raw_output": result.stdout}
        else:
            log(f"Kraken CLI error: {result.stderr}", level="ERROR")
            return None
    except FileNotFoundError:
        log("Kraken CLI not found. Using paper trading mode.", level="WARN")
        return None
    except Exception as e:
        log(f"Kraken CLI failed: {e}", level="ERROR")
        return None


def get_balance():
    if PAPER_MODE:
        log(f"Paper balance: USD=${paper_account['balance']['USD']:,.2f} | BTC={paper_account['balance']['BTC']:.6f}")
        return paper_account["balance"].copy()
    result = run_kraken_command(["balance"])
    if result:
        return result
    return paper_account["balance"].copy()


def get_ticker(pair="BTC/USD"):
    if PAPER_MODE:
        return None
    kraken_pair = pair.replace("/", "")
    result = run_kraken_command(["ticker", "--pair", kraken_pair])
    return result


def place_market_order(action, pair, volume, current_price=None):
    global paper_account

    if PAPER_MODE:
        paper_account["order_counter"] += 1
        order_id = f"PAPER-{paper_account['order_counter']:05d}"
        symbol = pair.split("/")[0]

        if current_price is None:
            log("No price provided for paper order", level="ERROR")
            return None

        # Simulate realistic fill price (with slippage)
        fill_price = simulate_fill_price(current_price, action)

        # Calculate fee
        fee_rate = get_trading_fee()
        usd_value = volume * fill_price
        fee = usd_value * fee_rate

        if action == "BUY":
            total_cost = usd_value + fee
            if total_cost > paper_account["balance"]["USD"]:
                log(f"REJECTED: Not enough USD. Need ${total_cost:.2f}, have ${paper_account['balance']['USD']:.2f}", level="WARN")
                return None
            paper_account["balance"]["USD"] -= total_cost
            paper_account["balance"][symbol] = paper_account["balance"].get(symbol, 0) + volume

        elif action == "SELL":
            if volume > paper_account["balance"].get(symbol, 0):
                log(f"REJECTED: Not enough {symbol}. Need {volume}, have {paper_account['balance'].get(symbol, 0)}", level="WARN")
                return None
            paper_account["balance"][symbol] -= volume
            paper_account["balance"]["USD"] += (usd_value - fee)

        order = {
            "order_id": order_id,
            "status": "filled",
            "action": action,
            "pair": pair,
            "volume": volume,
            "requested_price": current_price,
            "fill_price": fill_price,
            "slippage": round((fill_price - current_price) / current_price * 100, 4),
            "fee": round(fee, 2),
            "fee_rate": fee_rate,
            "usd_value": round(usd_value, 2),
            "net_cost": round(usd_value + fee, 2) if action == "BUY" else round(usd_value - fee, 2),
            "mode": "paper",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

        paper_account["orders"].append(order)
        paper_account["trade_history"].append(order)

        log(f"Paper {action}: {volume:.6f} {symbol} @ ${fill_price:,.2f} (slippage: {order['slippage']:.3f}%) | Fee: ${fee:.2f} | ID: {order_id}")
        log(f"Balance after: USD=${paper_account['balance']['USD']:,.2f} | {symbol}={paper_account['balance'][symbol]:.6f}")

        return order

    # Live trading (when PAPER_MODE = False)
    side = "buy" if action == "BUY" else "sell"
    kraken_pair = pair.replace("/", "")
    result = run_kraken_command([
        "order",
        "--pair", kraken_pair,
        "--type", side,
        "--ordertype", "market",
        "--volume", str(volume)
    ])
    if result:
        log(f"Live order placed: {action} {volume} {pair}")
        return result
    return None


def place_limit_order(action, pair, volume, price):
    global paper_account

    if PAPER_MODE:
        paper_account["order_counter"] += 1
        order_id = f"PAPER-LMT-{paper_account['order_counter']:05d}"
        order = {
            "order_id": order_id,
            "status": "pending",
            "action": action,
            "pair": pair,
            "volume": volume,
            "price": price,
            "mode": "paper",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        paper_account["orders"].append(order)
        log(f"Paper limit order: {action} {volume} {pair} @ ${price:,.2f} | ID: {order_id}")
        return order

    side = "buy" if action == "BUY" else "sell"
    kraken_pair = pair.replace("/", "")
    result = run_kraken_command([
        "order",
        "--pair", kraken_pair,
        "--type", side,
        "--ordertype", "limit",
        "--price", str(price),
        "--volume", str(volume)
    ])
    return result


def get_open_orders():
    if PAPER_MODE:
        return [o for o in paper_account["orders"] if o.get("status") == "pending"]
    result = run_kraken_command(["open-orders"])
    return result


def get_trade_history():
    if PAPER_MODE:
        return paper_account["trade_history"].copy()
    result = run_kraken_command(["trades"])
    return result


def get_paper_summary():
    """Get a summary of paper trading performance"""
    balance = paper_account["balance"]
    history = paper_account["trade_history"]
    total_fees = sum(t.get("fee", 0) for t in history)
    total_buys = len([t for t in history if t["action"] == "BUY"])
    total_sells = len([t for t in history if t["action"] == "SELL"])

    return {
        "balance": balance,
        "total_trades": len(history),
        "total_buys": total_buys,
        "total_sells": total_sells,
        "total_fees_paid": round(total_fees, 2),
        "orders": history
    }