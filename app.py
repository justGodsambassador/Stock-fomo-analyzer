import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="FOMO Stock Companion", page_icon="📈", layout="wide")

st.markdown('<h1 style="color:#1f77b4">📈 FOMO Stock Companion</h1>', unsafe_allow_html=True)
st.markdown("**Strong analysis. Clear decisions. Real risk awareness.**")

# ==================== MODE SELECTORS ====================
with st.sidebar:
    st.header("Modes")
    data_mode = st.radio("Data Mode", ["Stock Mode", "Crypto Mode"], index=1)
    risk_mode = st.radio("Risk Style", ["Aggressive", "Cautious"], index=0)
    st.caption(f"**{data_mode}** • **{risk_mode}**")

# ==================== HELPER FUNCTIONS ====================

def get_ticker_data(symbol, period="3mo"):
    try:
        ticker = yf.Ticker(symbol.upper().strip())
        hist = ticker.history(period=period, auto_adjust=True)
        info = ticker.info
        if hist is None or len(hist) < 15:
            return None, None, "Not enough data"
        return hist, info, None
    except Exception as e:
        return None, None, str(e)

def calculate_signals(hist):
    if hist is None or len(hist) < 20:
        return {"error": "Not enough data"}

    close = hist['Close']
    current_price = close.iloc[-1]
    pct_today = ((current_price / close.iloc[-2]) - 1) * 100 if len(close) > 1 else 0
    vol_ratio = hist['Volume'].iloc[-1] / hist['Volume'].rolling(20).mean().iloc[-1]

    sma20 = close.rolling(20).mean().iloc[-1]
    trend = "Uptrend" if current_price > sma20 else "Downtrend"

    fomo_score = 0
    if vol_ratio > 1.5 and pct_today > 2:
        fomo_score += 2
    if current_price > sma20:
        fomo_score += 1

    return {
        "current_price": round(current_price, 2),
        "pct_today": round(pct_today, 2),
        "vol_ratio": round(vol_ratio, 2),
        "fomo_score": fomo_score,
        "trend_direction": trend,
        "error": None
    }

# ==================== QUICK ANALYSIS + ACTIONABLE RECOMMENDATIONS ====================

st.subheader("⚡ Quick Analysis + Decision Engine")

ticker = st.text_input("Enter Ticker", value="USWR" if data_mode == "Crypto Mode" else "MU").upper().strip()

if ticker:
    if data_mode == "Stock Mode":
        hist, info, err = get_ticker_data(ticker)
        if err or hist is None:
            st.error(err)
        else:
