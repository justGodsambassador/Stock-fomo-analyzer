import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="FOMO Stock Companion", page_icon="📈", layout="wide")

st.markdown('<h1 style="color:#1f77b4">📈 FOMO Stock Companion</h1>', unsafe_allow_html=True)

# ==================== HELPER FUNCTIONS ====================

def get_ticker_data(symbol, period="3mo"):
    try:
        ticker = yf.Ticker(symbol.upper().strip())
        hist = ticker.history(period=period, auto_adjust=True)
        info = ticker.info
        if hist is None or len(hist) < 20:
            return None, None, "Not enough price history"
        return hist, info, None
    except Exception as e:
        return None, None, str(e)

def calculate_momentum_signals(hist, info):
    if hist is None or len(hist) < 30:
        return {"error": "Not enough data for analysis"}

    try:
        close = hist['Close']
        high = hist['High']
        low = hist['Low']
        volume = hist['Volume']
        current_price = close.iloc[-1]

        pct_today = ((current_price / close.iloc[-2]) - 1) * 100 if len(close) > 1 else 0
        vol_ma20 = volume.rolling(20).mean().iloc[-1]
        vol_ratio = volume.iloc[-1] / vol_ma20 if vol_ma20 > 0 else 1.0

        sma20 = close.rolling(20).mean().iloc[-1]
        sma50 = close.rolling(50).mean().iloc[-1] if len(close) >= 50 else sma20

        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs)).iloc[-1]

        # MACD
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        macd_signal = macd.ewm(span=9, adjust=False).mean()
        macd_bullish = macd.iloc[-1] > macd_signal.iloc[-1]

        # ADX
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        tr = pd.concat([high-low, abs(high-close.shift()), abs(low-close.shift())], axis=1).max(axis=1)
        atr = tr.rolling(window=14).mean()
        plus_di = 100 * (plus_dm.rolling(window=14).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(window=14).mean() / atr)
        dx = (abs(plus_di - minus_di) / (plus_di + minus_di + 0.0001)) * 100
        adx = dx.rolling(window=14).mean().iloc[-1]

        trend_direction = "Uptrend" if (current_price > sma20 and sma20 > sma50 and macd_bullish) else \
                          "Downtrend" if (current_price < sma20 and sma20 < sma50) else "Sideways"

        # FOMO Score
        fomo_score = 0
        signals = []
        if vol_ratio >= 1.5 and pct_today >= 2.5:
            fomo_score += 2
            signals.append("High Volume Surge")
        if current_price > sma20 and sma20 > sma50:
            fomo_score += 2
            signals.append("Strong Uptrend")
        if macd_bullish:
            fomo_score += 1
            signals.append("MACD Bullish")

        return {
            "current_price": round(current_price, 2),
            "pct_today": round(pct_today, 2),
            "vol_ratio": round(vol_ratio, 2),
            "rsi": round(rsi, 1),
            "fomo_score": fomo_score,
            "trend_direction": trend_direction,
            "adx": round(adx, 1),
            "macd_bullish": macd_bullish,
            "fomo_signals": signals,
            "error": None
        }
    except Exception as e:
        return {"error": f"Analysis error: {str(e)}"}

# ==================== QUICK BUY/SELL + COMPANION ====================

st.subheader("⚡ Quick Buy/Sell + In-Site Companion")

quick_ticker = st.text_input("Enter Ticker", value="MU").upper().strip()

if quick_ticker:
    hist, info, err = get_ticker_data(quick_ticker)
    if err or hist is None:
        st.error(f"Could not load data for '{quick_ticker}'. Try a valid ticker.")
    else:
        sig = calculate_momentum_signals(hist, info or {})
        if sig.get("error"):
            st.error(sig["error"])
        else:
            st.markdown(f"**{quick_ticker}** — ${sig['current_price']}")
            st.markdown(f"**Trend:** {sig['trend_direction']} | **ADX:** {sig['adx']} | **MACD Bullish:** {sig['macd_bullish']}")
            st.markdown(f"**FOMO Score:** {sig['fomo_score']} | **Signals:** {', '.join(sig['fomo_signals'])}")

            with st.expander("🧠 Companion Advice", expanded=True):
                if sig['fomo_score'] >= 5 and sig['trend_direction'] == "Uptrend":
                    st.success("**Strong Buy** — Good momentum. Buy on dips.")
                elif sig['fomo_score'] >= 3:
                    st.info("**Watch & Prepare** — Decent setup.")
                else:
                    st.warning("**Weak Momentum** — Better to wait.")

# ==================== AUTO FOMO SCANNER ====================

st.subheader("🚀 Auto FOMO Scanner — Best Opportunities Right Now")

st.markdown("Automatically scans stocks and shows where the **best profit** currently is.")

base_watchlist = ["MU", "NVDA", "PLTR", "AMD", "AVGO", "DELL", "SOFI", "BFLY", "CAST", "WOLF", "RIOT", "MARA", "COIN"]

user_extra = st.text_input("Add extra tickers (comma separated)")
if user_extra:
    extra = [t.strip().upper() for t in user_extra.split(",") if t.strip()]
    base_watchlist = list(set(base_watchlist + extra))

if st.button("🔄 Refresh Scanner"):
    st.rerun()

scanner_data = []
for ticker in base_watchlist:
    hist, info, err = get_ticker_data(ticker, "2mo")
    if err or hist is None or len(hist) < 25: continue
    sig = calculate_momentum_signals(hist, info or {})
    if sig.get("error"): continue

    profit_potential = sig["fomo_score"] * 1.5 + (sig.get("adx", 0) / 5)
    if sig["trend_direction"] == "Uptrend":
        profit_potential += 2

    if sig["fomo_score"] >= 5 and sig["trend_direction"] == "Uptrend":
        action = "🔥 Day Trade"
    elif sig["fomo_score"] >= 4:
        action = "📈 Swing Trade"
    else:
        action = "⏸️ Avoid"

    scanner_data.append({
        "Ticker": ticker,
        "Price": sig["current_price"],
        "FOMO Score": sig["fomo_score"],
        "Trend": sig["trend_direction"],
        "Profit Potential": round(profit_potential, 1),
        "Action": action
    })

if scanner_data:
    df = pd.DataFrame(scanner_data).sort_values("Profit Potential", ascending=False)
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.warning("Could not load scanner data.")

st.caption("Update on GitHub → Reboot app to see changes.")
