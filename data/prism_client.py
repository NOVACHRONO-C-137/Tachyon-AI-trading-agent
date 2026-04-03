import requests
from config.settings import PRISM_API_KEY, PRISM_BASE_URL
from utils.logger import log

def get_headers():
    return {"X-API-Key": PRISM_API_KEY}

def get_price(symbol="BTC"):
    try:
        url = f"{PRISM_BASE_URL}/crypto/{symbol}/price"
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()
        data = response.json()
        log(f"{symbol} price: ${data.get('price', 0):,.2f}")
        return data
    except Exception as e:
        log(f"Failed to get price for {symbol}: {e}", level="ERROR")
        return None

def get_signals(symbol="BTC"):
    try:
        url = f"{PRISM_BASE_URL}/signals/{symbol}"
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()
        data = response.json()
        log(f"{symbol} signal: {data}")
        return data
    except Exception as e:
        log(f"Failed to get signals for {symbol}: {e}", level="ERROR")
        return None

def get_risk(symbol="BTC"):
    try:
        url = f"{PRISM_BASE_URL}/risk/{symbol}"
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()
        data = response.json()
        log(f"{symbol} risk: {data}")
        return data
    except Exception as e:
        log(f"Failed to get risk for {symbol}: {e}", level="ERROR")
        return None

def get_asset_info(symbol="BTC"):
    try:
        url = f"{PRISM_BASE_URL}/resolve/{symbol}"
        response = requests.get(url, headers=get_headers())
        response.raise_for_status()
        data = response.json()
        log(f"{symbol} info: {data}")
        return data
    except Exception as e:
        log(f"Failed to resolve {symbol}: {e}", level="ERROR")
        return None
