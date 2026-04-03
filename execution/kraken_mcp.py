import subprocess
import json
from utils.logger import log

# The command is now just 'kraken' since it's in our Linux PATH
KRAKEN_CLI_PATH = "kraken" 
PAPER_MODE = True

def run_kraken_command(args):
    """
    Executes a command using the official Kraken CLI and returns the parsed JSON.
    """
    try:
        # Force the CLI to output JSON so our Python script can read it easily
        if "-o" not in args and "--output" not in args:
            args.extend(["-o", "json"])
            
        cmd = [KRAKEN_CLI_PATH] + args
        log(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                log(f"Failed to parse JSON. Raw: {result.stdout}", level="WARN")
                return {"raw_output": result.stdout}
        else:
            log(f"Kraken CLI error: {result.stderr}", level="ERROR")
            return None
            
    except FileNotFoundError:
        log("Kraken CLI not found. Are you running this inside WSL?", level="ERROR")
        return None
    except Exception as e:
        log(f"Kraken execution failed: {e}", level="ERROR")
        return None

def get_balance():
    """
    Fetches the account balance and flattens it for the bot to read.
    """
    if PAPER_MODE:
        result = run_kraken_command(["paper", "balance"])
        if result and "balances" in result:
            # Flattens {"balances": {"USD": {"available": 10000.0}}} -> {"USD": 10000.0}
            flat_balance = {}
            for asset, data in result["balances"].items():
                flat_balance[asset] = data.get("available", 0.0)
            return flat_balance
        return {"USD": 0.0}
    else:
        # Live mode (We will update this when you switch to real money)
        return run_kraken_command(["balance"])

def get_ticker(pair="BTC/USD"):
    """
    Gets the live market ticker for the asset.
    """
    kraken_pair = pair.replace("/", "")
    # Ticker works the same in paper and live mode
    return run_kraken_command(["ticker", kraken_pair])

def place_market_order(action, pair, volume, current_price=None):
    """
    Sends the official execution command to the Kraken engine.
    """
    kraken_pair = pair.replace("/", "")
    side = action.lower() # Converts "BUY" to "buy"
    
    if PAPER_MODE:
        log(f"Submitting official Paper {action} order to Kraken for {volume} {kraken_pair}...")
        result = run_kraken_command(["paper", side, kraken_pair, str(volume)])
        
        if result:
            log(f"Paper {action} SUCCESS! Kraken confirmed the trade.")
            return result
        else:
            log(f"Paper {action} FAILED. Kraken rejected the trade.", level="ERROR")
            return None


    log(f"Submitting LIVE {action} order to Kraken for {volume} {kraken_pair}...")
    return run_kraken_command([
        "order",
        "--pair", kraken_pair,
        "--type", side,
        "--ordertype", "market",
        "--volume", str(volume)
    ])

def get_paper_summary():
    """
    Fetches the official PnL and status directly from Kraken.
    """
    if PAPER_MODE:
        return run_kraken_command(["paper", "status"])
    return None