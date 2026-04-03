from config.settings import DATA_SOURCE
from data.indicators import add_price, get_all_indicators
from utils.logger import log

# Import the right client based on settings
if DATA_SOURCE == "coingecko":
    from data.coingecko_client import generate_signals as _get_signals
    from data.coingecko_client import generate_risk_data as _get_risk
    from data.coingecko_client import get_price_history
else:
    from data.prism_client import get_signals as _get_signals
    from data.prism_client import get_risk as _get_risk

# Cache risk data to save API calls
cached_risk_data = None
risk_call_count = 0
RISK_CHECK_EVERY = 4
history_loaded = False


def extract_signal_data(signals_data):
    if signals_data is None:
        return None
    try:
        data_list = signals_data.get("data", [])
        if len(data_list) > 0:
            return data_list[0]
        return None
    except:
        return None


def extract_price_from_signals(signals_data):
    signal = extract_signal_data(signals_data)
    if signal:
        return signal.get("current_price", 0)
    return 0


def calculate_prism_score(signals_data):
    signal = extract_signal_data(signals_data)
    if signal is None:
        return 0
    try:
        overall = signal.get("overall_signal", "").lower()
        strength = signal.get("strength", "").lower()
        net_score = signal.get("net_score", 0)

        if "bull" in overall or "buy" in overall or "long" in overall:
            direction = 1
        elif "bear" in overall or "sell" in overall or "short" in overall:
            direction = -1
        else:
            direction = 0

        if "strong" in strength:
            multiplier = 90
        elif "moderate" in strength:
            multiplier = 60
        elif "weak" in strength:
            multiplier = 30
        else:
            multiplier = 50

        score = direction * multiplier

        if net_score != 0:
            score = score * 0.7 + (net_score * 30) * 0.3

        return max(-100, min(100, int(score)))
    except Exception as e:
        log(f"Error calculating PRISM score: {e}", level="ERROR")
        return 0


def calculate_indicator_score(indicators):
    score = 0
    current_price = indicators.get("current_price")
    if current_price is None:
        return 0

    rsi = indicators.get("rsi_14")
    if rsi is not None:
        if rsi < 30:
            score += 40
        elif rsi > 70:
            score -= 40
        elif rsi < 45:
            score += 15
        elif rsi > 55:
            score -= 15

    sma = indicators.get("sma_20")
    if sma is not None and sma > 0:
        if current_price > sma * 1.02:
            score += 30
        elif current_price < sma * 0.98:
            score -= 30
        elif current_price > sma:
            score += 10
        else:
            score -= 10

    change = indicators.get("price_change_pct", 0)
    if change > 3:
        score += 30
    elif change > 1:
        score += 15
    elif change < -3:
        score -= 30
    elif change < -1:
        score -= 15

    return max(-100, min(100, score))


def calculate_risk_score(risk_data):
    if risk_data is None:
        return 0
    try:
        volatility = risk_data.get("daily_volatility", 0.5)
        sharpe = risk_data.get("sharpe_ratio", 0)
        drawdown = risk_data.get("current_drawdown", 0)

        score = 0

        if volatility > 0.8:
            score -= 40
        elif volatility > 0.6:
            score -= 20
        elif volatility < 0.3:
            score += 30
        elif volatility < 0.5:
            score += 10

        if sharpe > 1:
            score += 30
        elif sharpe > 0:
            score += 15
        elif sharpe < -1:
            score -= 30
        elif sharpe < 0:
            score -= 15

        if drawdown > 20:
            score -= 30
        elif drawdown > 10:
            score -= 15
        elif drawdown < 5:
            score += 10

        return max(-100, min(100, score))
    except Exception as e:
        log(f"Error calculating risk score: {e}", level="ERROR")
        return 0


def get_prism_indicators(signals_data):
    signal = extract_signal_data(signals_data)
    if signal is None:
        return {}
    return signal.get("indicators", {})


def load_history_once(symbol):
    global history_loaded
    if not history_loaded and DATA_SOURCE == "coingecko":
        log("Loading price history for indicators...")
        try:
            prices = get_price_history(symbol, days=30)
            for price in prices:
                add_price(price)
            log(f"Loaded {len(prices)} historical prices")
            history_loaded = True
        except Exception as e:
            log(f"Could not load history: {e}", level="WARN")


def get_combined_signal(symbol="BTC"):
    global cached_risk_data, risk_call_count

    log(f"Analyzing {symbol} (source: {DATA_SOURCE})...")

    # Load historical prices on first run
    load_history_once(symbol)

    # Get signals (works with both PRISM and CoinGecko)
    signals_data = _get_signals(symbol)

    if signals_data is None:
        log("No signal data received", level="ERROR")
        return None

    current_price = extract_price_from_signals(signals_data)

    if current_price <= 0:
        log("Could not get price", level="ERROR")
        return None

    add_price(current_price)

    # Get risk data (cached)
    risk_call_count += 1
    if risk_call_count >= RISK_CHECK_EVERY or cached_risk_data is None:
        log("Fetching fresh risk data...")
        cached_risk_data = _get_risk(symbol)
        risk_call_count = 0
    else:
        log(f"Using cached risk data (next refresh in {RISK_CHECK_EVERY - risk_call_count} cycles)")

    # Calculate scores
    prism_score = calculate_prism_score(signals_data)

    prism_indicators = get_prism_indicators(signals_data)
    our_indicators = get_all_indicators()

    if our_indicators.get("rsi_14") is None and "rsi" in prism_indicators:
        our_indicators["rsi_14"] = prism_indicators["rsi"]
        log(f"Using PRISM RSI: {prism_indicators['rsi']}")

    indicator_score = calculate_indicator_score(our_indicators)
    risk_score = calculate_risk_score(cached_risk_data)

    combined_score = (
        prism_score * 0.40 +
        indicator_score * 0.30 +
        risk_score * 0.20
    )
    combined_score = round(combined_score)
    combined_score = max(-100, min(100, combined_score))

    if combined_score >= 60:
        action = "BUY"
    elif combined_score <= -60:
        action = "SELL"
    else:
        action = "HOLD"

    confidence = abs(combined_score)

    result = {
        "symbol": symbol,
        "score": combined_score,
        "action": action,
        "confidence": confidence,
        "current_price": current_price,
        "breakdown": {
            "prism_score": prism_score,
            "indicator_score": indicator_score,
            "risk_score": risk_score,
            "rsi": our_indicators.get("rsi_14"),
            "sma_20": our_indicators.get("sma_20"),
            "price_change_pct": our_indicators.get("price_change_pct"),
            "history_length": our_indicators.get("history_length"),
            "prism_indicators": prism_indicators
        }
    }

    log(f"Signal: {action} | Score: {combined_score} | Price: ${current_price:,.2f} | PRISM: {prism_score} | Indicators: {indicator_score} | Risk: {risk_score}")

    return result