import subprocess
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def log(message, level="INFO"):
    getattr(logger, level.lower())(message)


class KrakenExecutionEngine:
    def __init__(self):
        log("Initializing Kraken Paper Engine...")
        self._run_cli("paper init --balance 10000")

    def _run_cli(self, command_string):
        full_command = f"kraken {command_string} -o json"
        try:
            result = subprocess.run(
                full_command.split(),
                capture_output=True,
                text=True,
                timeout=15
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                log(f"CLI error: {result.stderr}", level="ERROR")
                return None
        except subprocess.TimeoutExpired:
            log("CLI command timed out", level="ERROR")
            return None
        except Exception as e:
            log(f"CLI execution failed: {e}", level="ERROR")
            return None

    def get_market_price(self, pair):
        result = self._run_cli(f"ticker {pair}")
        if result and "c" in result:
            return float(result["c"][0])
        return None

    def execute_trade(self, action, pair, amount):
        result = self._run_cli(f"paper {action.lower()} {pair} {amount}")
        if result and result.get("status") == "success":
            return True
        return False

    def get_portfolio_status(self):
        return self._run_cli("paper status")