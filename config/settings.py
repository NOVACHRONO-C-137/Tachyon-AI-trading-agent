import os
from dotenv import load_dotenv

load_dotenv()

# API KEYS
PRISM_API_KEY = os.getenv("PRISM_API_KEY")
KRAKEN_API_KEY = os.getenv("KRAKEN_API_KEY")
KRAKEN_API_SECRET = os.getenv("KRAKEN_API_SECRET")

# DATA SOURCE: "coingecko" for free development, "prism" for competition
DATA_SOURCE = "coingecko"

# TRADING
TRADING_PAIR = "SOL/USD"
CHECK_INTERVAL = 30  # Changed from 0.5minute

# RISK MANAGEMENT
MAX_TRADE_USD = 100
MAX_RISK_PERCENT = 0.02
DAILY_LOSS_LIMIT_USD = 50
MAX_OPEN_POSITIONS = 3
STOP_LOSS_PERCENT = 0.05
TAKE_PROFIT_PERCENT = 0.10

# STRATEGY
BUY_THRESHOLD = 60
SELL_THRESHOLD = -60

# PRISM
PRISM_BASE_URL = "https://api.prismapi.ai"

# COINGECKO (free, no key needed)
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

# LOGGING
LOG_FILE = "logs/trades.log"