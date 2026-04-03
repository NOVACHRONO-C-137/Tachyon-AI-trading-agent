import subprocess
import json
from utils.logger import log

KRAKEN_CLI_PATH = "kraken-cli"
PAPER_MODE = True

simulated_balance = {
    "USD": 10000.00,
    "BTC": 0.0,
    "ETH": 0.0,
    "SOL": 0.0
}

simulated_orders = []
order_counter = 0

def run_kraken_command(args):
    try:
        cmd = [KRAKEN_CLI_PATH] + args
        log(f"Running Kraken CLI: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
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
        log(f"Paper balance: {simulated_balance}")
        return simulated_balance.copy()
    result = run_kraken_command(["balance"])
    if result:
        return result
    return simulated_balance.copy()

def get_ticker(pair="BTC/USD"):
    if PAPER_MODE:
        return None
    kraken_pair = pair.replace("/", "")
    result = run_kraken_command(["ticker", "--pair", kraken_pair])
    return result

def place_market_order(action, pair, volume):
    global order_counter
    if PAPER_MODE:
        order_counter += 1
        order_id = f"PAPER-{order_counter:05d}"
        symbol = pair.split("/")[0]
        if action == "BUY":
            simulated_balance["USD"] -= volume
            price_estimate = volume
            simulated_balance[symbol] = simulated_balance.get(symbol, 0) + volume
        elif action == "SELL":
            simulated_balance[symbol] = simulated_balance.get(symbol, 0) - volume
            simulated_balance["USD"] += volume
        order = {
            "order_id": order_id,
            "status": "filled",
            "action": action,
            "pair": pair,
            "volume": volume,
            "mode": "paper"
        }
        simulated_orders.append(order)
        log(f"Paper order placed: {action} {volume} {pair} | ID: {order_id}")
        return order
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
    log("Live order failed, falling back to paper", level="WARN")
    return place_market_order(action, pair, volume)

def place_limit_order(action, pair, volume, price):
    global order_counter
    if PAPER_MODE:
        order_counter += 1
        order_id = f"PAPER-LMT-{order_counter:05d}"
        order = {
            "order_id": order_id,
            "status": "pending",
            "action": action,
            "pair": pair,
            "volume": volume,
            "price": price,
            "mode": "paper"
        }
        simulated_orders.append(order)
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
    if result:
        return result
    return None

def get_open_orders():
    if PAPER_MODE:
        return [o for o in simulated_orders if o.get("status") == "pending"]
    result = run_kraken_command(["open-orders"])
    return result

def get_trade_history():
    if PAPER_MODE:
        return simulated_orders.copy()
    result = run_kraken_command(["trades"])
    return result