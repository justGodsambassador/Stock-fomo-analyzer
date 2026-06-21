import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="FOMO Stock Companion", page_icon="📈", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; font-weight: 700; color: #1f77b4;}
    .stTabs [data-baseweb="tab-list"] {gap: 8px;}
</style>
""", unsafe_allow_html=True)

# ==================== HELPER FUNCTIONS ====================

def calculate_rsi(close_prices, period=14):
    delta = close_prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_momentum_signals(hist, info):
    if hist is None or len(hist) < 30:
        return {"error": "Insufficient history"}

    close = hist['Close']
    volume = hist['Volume']
    high = hist['High']
    low = hist['Low']
    current_price = close.iloc[-1]

    # Basic metrics
    pct_today = ((current_price / close.iloc[-2]) - 1) * 100 if len(close) > 1 else 0
    pct_5d = ((current_price / close.iloc[-5]) - 1) * 100 if len(close) >= 5 else 0
    vol_ma20 = volume.rolling(20).mean().iloc[-1]
    vol_ratio = volume.iloc[-1] / vol_ma20 if vol_ma20 > 0 else 1.0

    sma20 = close.rolling(20).mean().iloc[-1]
    sma50 = close.rolling(50).mean().iloc[-1] if len(close) >= 50 else sma20
    rsi = calculate_rsi(close).iloc[-1]

    # MACD
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd = ema12 - ema26
    macd_signal = macd.ewm(span=9, adjust=False).mean()
    macd_bullish = macd.iloc[-1] > macd_signal.iloc[-1]

    # ADX (simplified)
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm < 0] = 0
    tr = pd.concat([high-low, abs(high-close.shift()), abs(low-close.shift())], axis=1).max(axis=1)
    atr = tr.rolling(14).mean()
    plus_di = 100 * (plus_dm.rolling(14).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(14).mean() / atr)
    dx = (abs(plus_di - minus_di) / (plus_di + minus_di + 0.0001)) * 100
    adx = dx.rolling(14).mean().iloc[-1]

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

def get_ticker_data(symbol, period="3mo"):
    try:
        ticker = yf.Ticker(symbol.upper().strip())
        hist = ticker.history(period=period, auto_adjust=True)
        info = ticker.info
        return hist, info, None
    except Exception as e:
        return None, None, str(e)

# ==================== UI ====================

st.markdown('<h1 class="main-header">📈 FOMO Stock Companion</h1>', unsafe_allow_html=True)
st.markdown("Track momentum, get smart suggestions, manage multiple accounts, and discover new opportunities.")

# ========== QUICK BUY/SELL + COMPANION ==========
st.subheader("⚡ Quick Buy/Sell + In-Site Companion")

quick_ticker = st.text_input("Enter Ticker", value="MU").upper().strip()

if quick_ticker:
    hist, info, err = get_ticker_data(quick_ticker)
    if err or hist is None:
        st.error(f"Could not load {quick_ticker}")
    else:
        sig = calculate_momentum_signals(hist, info or {})
        price = sig["current_price"]

        st.markdown(f"**{quick_ticker}** — ${price}")
        st.markdown(f"**Trend:** {sig['trend_direction']} | **ADX:** {sig['adx']} | **MACD Bullish:** {sig['macd_bullish']}")
        st.markdown(f"**FOMO Score:** {sig['fomo_score']} | **Signals:** {', '.join(sig['fomo_signals'])}")

        # In-Site Companion Advice
        with st.expander("🧠 Companion Advice", expanded=True):
            if sig['fomo_score'] >= 5 and sig['trend_direction'] == "Uptrend":
                st.success("**Strong Buy Signal** — Good momentum. Consider buying on dips.")
            elif sig['fomo_score'] >= 3:
                st.info("**Watch & Prepare** — Decent setup. Wait for confirmation.")
            else:
                st.warning("**Weak Momentum** — Better to wait or look elsewhere.")

# ========== MULTI-ACCOUNT PORTFOLIO TRACKER ==========
st.subheader("📊 Multi-Account FOMO Portfolio Tracker")

if "fomo_accounts" not in st.session_state:
    st.session_state.fomo_accounts = {"Main FOMO Account": []}

selected_account = st.selectbox("Select Account", list(st.session_state.fomo_accounts.keys()))

# Show positions + recommendations (simplified for mobile)
positions = st.session_state.fomo_accounts[selected_account]
for pos in positions:
    st.write(f"**{pos['ticker']}** | Buy: ${pos['buy_price']} | Shares: {pos['shares']}")

# Add new position
with st.form("add_position"):
    t = st.text_input("Ticker")
    bp = st.number_input("Buy Price", min_value=0.01)
    sh = st.number_input("Shares", min_value=0.01)
    bd = st.date_input("Buy Date")
    if st.form_submit_button("Add Position"):
        st.session_state.fomo_accounts[selected_account].append({
            "ticker": t.upper(),
            "buy_price": bp,
            "shares": sh,
            "buy_date": str(bd)
        })
        st.rerun()

# ========== FOMO LEADERBOARD ==========
st.subheader("🏆 FOMO Momentum Leaderboard")

watchlist = ["MU", "NVDA", "PLTR", "BFLY", "AMD", "AVGO", "DELL", "SOFI"]
lb_data = []
for t in watchlist:
    h, inf, e = get_ticker_data(t, "2mo")
    if e or h is None: continue
    s = calculate_momentum_signals(h, inf or {})
    lb_data.append({
        "Ticker": t,
        "Price": s["current_price"],
        "FOMO Score": s["fomo_score"],
        "Trend": s["trend_direction"],
        "Rec": "Strong Buy" if s["fomo_score"] >= 5 else "Watch"
    })

if lb_data:
    st.dataframe(pd.DataFrame(lb_data).sort_values("FOMO Score", ascending=False), use_container_width=True)

st.caption("Update the code on GitHub and reboot the app to see full features.")
