from data.signals import get_combined_signal
from config.settings import BUY_THRESHOLD, SELL_THRESHOLD, TRADING_PAIR
from utils.logger import log
from utils.helpers import extract_symbol

def analyze_market():
    symbol = extract_symbol(TRADING_PAIR)
    signal = get_combined_signal(symbol)
    if signal is None:
        log("Could not get market signal. Skipping.", level="WARN")
        return {"action": "HOLD", "reason": "No data available"}
    score = signal["score"]
    breakdown = signal["breakdown"]
    reasons = []
    if breakdown["prism_score"] > 30:
        reasons.append("PRISM bullish")
    elif breakdown["prism_score"] < -30:
        reasons.append("PRISM bearish")
    rsi = breakdown.get("rsi")
    if rsi is not None:
        if rsi < 30:
            reasons.append(f"RSI oversold ({rsi:.0f})")
        elif rsi > 70:
            reasons.append(f"RSI overbought ({rsi:.0f})")
    if breakdown["risk_score"] > 20:
        reasons.append("low volatility")
    elif breakdown["risk_score"] < -20:
        reasons.append("high volatility")
    pct = breakdown.get("price_change_pct", 0)
    if pct > 2:
        reasons.append(f"momentum up ({pct:.1f}%)")
    elif pct < -2:
        reasons.append(f"momentum down ({pct:.1f}%)")
    reason = " + ".join(reasons) if reasons else "neutral signals"
    decision = {
        "action": signal["action"],
        "pair": TRADING_PAIR,
        "symbol": symbol,
        "score": score,
        "confidence": signal["confidence"],
        "price": signal["current_price"],
        "reason": reason,
        "breakdown": breakdown
    }
    log(f"Decision: {decision['action']} | Score: {score} | Reason: {reason}")
    return decision