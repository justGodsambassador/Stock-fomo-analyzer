import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="FOMO Stock Companion", page_icon="📈", layout="wide")

st.markdown('<h1 style="color:#1f77b4">📈 FOMO Stock Companion</h1>', unsafe_allow_html=True)
st.markdown("Momentum scanner, smart suggestions, portfolio tracker, and FOMO leaderboard.")

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
        pct_5d = ((current_price / close.iloc[-5]) - 1) * 100 if len(close) >= 5 else 0

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

        # ADX (Trend Strength)
        plus_dm = high.diff()
        minus_dm = -low.diff()
        plus_dm[plus_dm < 0] = 0
        minus_dm[minus_dm < 0] = 0
        tr = pd.concat([high - low, abs(high - close.shift()), abs(low - close.shift())], axis=1).max(axis=1)
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

# ==================== QUICK BUY/SELL + IN-SITE COMPANION ====================

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
            price = sig["current_price"]
            st.markdown(f"**{quick_ticker}** — ${price}")
            st.markdown(f"**Trend:** {sig['trend_direction']} | **ADX:** {sig['adx']} | **MACD Bullish:** {sig['macd_bullish']}")
            st.markdown(f"**FOMO Score:** {sig['fomo_score']} | **Signals:** {', '.join(sig['fomo_signals'])}")

            with st.expander("🧠 Companion Advice — Smart Move Right Now", expanded=True):
                if sig['fomo_score'] >= 5 and sig['trend_direction'] == "Uptrend":
                    st.success("**Strong Buy** — Good momentum. Buy on dips or breakout.")
                elif sig['fomo_score'] >= 3:
                    st.info("**Watch & Prepare** — Decent setup. Wait for confirmation.")
                else:
                    st.warning("**Weak Momentum** — Better to wait or look elsewhere.")

# ==================== MULTI-ACCOUNT PORTFOLIO TRACKER ====================

st.subheader("📊 Multi-Account FOMO Portfolio Tracker")

if "fomo_accounts" not in st.session_state:
    st.session_state.fomo_accounts = {"Aggressive FOMO": [], "Swing Account": []}

selected_account = st.selectbox("Select Account", list(st.session_state.fomo_accounts.keys()))

positions = st.session_state.fomo_accounts[selected_account]

for i, pos in enumerate(positions):
    ticker = pos["ticker"]
    buy_price = pos["buy_price"]
    shares = pos["shares"]
    buy_date = pos.get("buy_date")

    hist, info, err = get_ticker_data(ticker)
    if err or hist is none:
    st.error(f"Could not load data for '{ticker_input}'. Try a valid ticker.")
else:
    sig = calculate_momentum_signals(hist, info or {})
