from data.prism_client import get_price, get_signals, get_risk
from data.indicators import add_price, get_all_indicators
from utils.logger import log

def calculate_prism_score(signals_data):
    if signals_data is None:
        return 0
    try:
        signal = signals_data.get("signal", "").lower()
        strength = signals_data.get("strength", 50)
        if "bull" in signal or "buy" in signal or "long" in signal:
            return min(strength, 100)
        elif "bear" in signal or "sell" in signal or "short" in signal:
            return max(-strength, -100)
        else:
            return 0
    except:
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
        volatility = risk_data.get("volatility", 0.5)
        if volatility > 0.8:
            return -60
        elif volatility > 0.6:
            return -30
        elif volatility < 0.3:
            return 40
        elif volatility < 0.5:
            return 20
        else:
            return 0
    except:
        return 0

def get_combined_signal(symbol="BTC"):
    log(f"Analyzing {symbol}...")
    price_data = get_price(symbol)
    signals_data = get_signals(symbol)
    risk_data = get_risk(symbol)
    current_price = 0
    if price_data:
        current_price = price_data.get("price", 0)
        if current_price > 0:
            add_price(current_price)
    prism_score = calculate_prism_score(signals_data)
    indicators = get_all_indicators()
    indicator_score = calculate_indicator_score(indicators)
    risk_score = calculate_risk_score(risk_data)
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
            "rsi": indicators.get("rsi_14"),
            "sma_20": indicators.get("sma_20"),
            "price_change_pct": indicators.get("price_change_pct"),
            "history_length": indicators.get("history_length")
        }
    }
    log(f"Signal: {action} | Score: {combined_score} | Confidence: {confidence}% | Price: ${current_price:,.2f}")
    return result