import os
import json

STATE_FILE = "logs/bot_state.json"

def get_default_state():
    return {
        "open_positions": [],
        "total_trades": 0,
        "total_pnl": 0.0,
        "daily_loss": 0.0,
        "last_check_time": None,
        "is_running": True
    }

def save_state(state):
    os.makedirs("logs", exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return get_default_state()
