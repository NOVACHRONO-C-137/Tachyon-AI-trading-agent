import requests
from utils.logger import log

BASE_URL = "https://api.coingecko.com/api/v3"

# CoinGecko uses different IDs than symbols
SYMBOL_TO_ID = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "XRP": "ripple",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "AVAX": "avalanche-2",
    "DOT": "polkadot",
    "MATIC": "matic-network",
    "LINK": "chainlink"
}


def get_coin_id(symbol):
    return SYMBOL_TO_ID.get(symbol.upper(), symbol.lower())


def get_price(symbol="BTC"):
    try:
        coin_id = get_coin_id(symbol)
        url = f"{BASE_URL}/simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_24hr_vol": "true",
            "include_market_cap": "true"
        }
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if coin_id in data:
            coin_data = data[coin_id]
            price = coin_data.get("usd", 0)
            change_24h = coin_data.get("usd_24h_change", 0)
            volume = coin_data.get("usd_24h_vol", 0)

            log(f"{symbol} price: ${price:,.2f} | 24h change: {change_24h:.2f}%")

            return {
                "price": price,
                "change_24h": change_24h,
                "volume_24h": volume,
                "market_cap": coin_data.get("usd_market_cap", 0)
            }
        return None

    except Exception as e:
        log(f"CoinGecko price failed for {symbol}: {e}", level="ERROR")
        return None


def get_market_data(symbol="BTC"):
    try:
        coin_id = get_coin_id(symbol)
        url = f"{BASE_URL}/coins/{coin_id}"
        params = {
            "localization": "false",
            "tickers": "false",
            "community_data": "false",
            "developer_data": "false"
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        market = data.get("market_data", {})

        result = {
            "price": market.get("current_price", {}).get("usd", 0),
            "high_24h": market.get("high_24h", {}).get("usd", 0),
            "low_24h": market.get("low_24h", {}).get("usd", 0),
            "price_change_24h": market.get("price_change_percentage_24h", 0),
            "price_change_7d": market.get("price_change_percentage_7d", 0),
            "price_change_14d": market.get("price_change_percentage_14d", 0),
            "price_change_30d": market.get("price_change_percentage_30d", 0),
            "market_cap": market.get("market_cap", {}).get("usd", 0),
            "total_volume": market.get("total_volume", {}).get("usd", 0),
            "ath": market.get("ath", {}).get("usd", 0),
            "ath_change": market.get("ath_change_percentage", {}).get("usd", 0),
        }

        log(f"{symbol} market: ${result['price']:,.2f} | 24h: {result['price_change_24h']:.1f}% | 7d: {result['price_change_7d']:.1f}%")
        return result

    except Exception as e:
        log(f"CoinGecko market data failed for {symbol}: {e}", level="ERROR")
        return None


def get_price_history(symbol="BTC", days=14):
    try:
        coin_id = get_coin_id(symbol)
        url = f"{BASE_URL}/coins/{coin_id}/market_chart"
        params = {
            "vs_currency": "usd",
            "days": days,
            "interval": "daily"
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        prices = [p[1] for p in data.get("prices", [])]
        log(f"{symbol} history: {len(prices)} price points loaded")
        return prices

    except Exception as e:
        log(f"CoinGecko history failed for {symbol}: {e}", level="ERROR")
        return []


def generate_signals(symbol="BTC"):
    market = get_market_data(symbol)
    if market is None:
        return None

    change_24h = market.get("price_change_24h", 0)
    change_7d = market.get("price_change_7d", 0)
    change_30d = market.get("price_change_30d", 0)

    # Simple signal generation based on price momentum
    score = 0

    # 24h momentum
    if change_24h > 5:
        score += 3
    elif change_24h > 2:
        score += 2
    elif change_24h > 0:
        score += 1
    elif change_24h < -5:
        score -= 3
    elif change_24h < -2:
        score -= 2
    elif change_24h < 0:
        score -= 1

    # 7d trend
    if change_7d > 10:
        score += 2
    elif change_7d > 3:
        score += 1
    elif change_7d < -10:
        score -= 2
    elif change_7d < -3:
        score -= 1

    # 30d trend
    if change_30d > 15:
        score += 1
    elif change_30d < -15:
        score -= 1

    # Determine overall signal
    if score >= 3:
        overall = "bullish"
        strength = "strong"
    elif score >= 1:
        overall = "bullish"
        strength = "moderate"
    elif score <= -3:
        overall = "bearish"
        strength = "strong"
    elif score <= -1:
        overall = "bearish"
        strength = "moderate"
    else:
        overall = "neutral"
        strength = "weak"

    result = {
        "data": [
            {
                "symbol": symbol,
                "overall_signal": overall,
                "strength": strength,
                "net_score": score,
                "bullish_score": max(0, score),
                "bearish_score": abs(min(0, score)),
                "current_price": market["price"],
                "indicators": {
                    "price_change_24h": change_24h,
                    "price_change_7d": change_7d,
                    "price_change_30d": change_30d,
                    "high_24h": market.get("high_24h", 0),
                    "low_24h": market.get("low_24h", 0)
                }
            }
        ]
    }

    log(f"{symbol} generated signal: {overall} ({strength}) | score: {score}")
    return result


def generate_risk_data(symbol="BTC"):
    history = get_price_history(symbol, days=30)
    if not history or len(history) < 2:
        return None

    # Calculate daily returns
    returns = []
    for i in range(1, len(history)):
        if history[i-1] > 0:
            daily_return = (history[i] - history[i-1]) / history[i-1]
            returns.append(daily_return)

    if not returns:
        return None

    import statistics

    avg_return = statistics.mean(returns)
    volatility = statistics.stdev(returns) if len(returns) > 1 else 0

    # Calculate max drawdown
    peak = history[0]
    max_drawdown = 0
    current_drawdown = 0
    for price in history:
        if price > peak:
            peak = price
        dd = ((peak - price) / peak) * 100
        if dd > max_drawdown:
            max_drawdown = dd
        current_drawdown = dd

    # Simple Sharpe (annualized)
    if volatility > 0:
        sharpe = (avg_return * 365) / (volatility * (365 ** 0.5))
    else:
        sharpe = 0

    positive_days = len([r for r in returns if r > 0])
    positive_pct = (positive_days / len(returns)) * 100

    result = {
        "daily_volatility": round(volatility, 4),
        "annual_volatility": round(volatility * (365 ** 0.5), 4),
        "sharpe_ratio": round(sharpe, 3),
        "max_drawdown": round(max_drawdown, 2),
        "current_drawdown": round(current_drawdown, 2),
        "avg_daily_return": round(avg_return * 100, 4),
        "positive_days_pct": round(positive_pct, 1)
    }

    log(f"{symbol} risk: vol={result['daily_volatility']} | sharpe={result['sharpe_ratio']} | drawdown={result['current_drawdown']}%")
    return result