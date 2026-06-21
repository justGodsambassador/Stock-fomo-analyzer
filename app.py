import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="FOMO Stock Companion", page_icon="📈", layout="wide")

st.markdown('<h1 style="color:#1f77b4">📈 FOMO Stock Companion</h1>', unsafe_allow_html=True)

# ==================== MODE SELECTOR ====================
st.sidebar.header("Analysis Mode")
mode = st.sidebar.radio(
    "Choose your style:",
    ["Aggressive", "Cautious"],
    index=0,
    help="Aggressive = Higher risk, chase bigger moves. Cautious = Protect capital, better risk/reward."
)
st.sidebar.caption(f"**Current Mode:** {mode}")

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
        return {"error": "Not enough data"}

    try:
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
    except Exception as e:
        return {"error": str(e)}

# ==================== QUICK BUY/SELL + COMPANION (MODE AWARE) ====================

st.subheader("⚡ Quick Buy/Sell + In-Site Companion")

quick_ticker = st.text_input("Enter Ticker", value="MU").upper().strip()

if quick_ticker:
    hist, info, err = get_ticker_data(quick_ticker)
    if err or hist is None:
        st.error(f"Could not load data for '{quick_ticker}'")
    else:
        sig = calculate_momentum_signals(hist, info or {})
        if sig.get("error"):
            st.error(sig["error"])
        else:
            price = sig["current_price"]
            st.markdown(f"**{quick_ticker}** — ${price}")
            st.markdown(f"**Trend:** {sig['trend_direction']} | **FOMO Score:** {sig['fomo_score']}")

            # Mode-aware advice
            with st.expander("🧠 Companion Advice", expanded=True):
                fomo = sig['fomo_score']
                trend = sig['trend_direction']

                if mode == "Aggressive":
                    if fomo >= 4 and trend == "Uptrend":
                        st.success("**Aggressive Buy** — Strong momentum. Good for higher risk/reward plays.")
                    elif fomo >= 3:
                        st.info("**Aggressive Watch** — Decent setup. Can take small size.")
                    else:
                        st.warning("**Skip or Small Size** — Weak signals. Not ideal for aggressive style.")

                else:  # Cautious mode
                    if fomo >= 5 and trend == "Uptrend":
                        st.success("**Cautious Buy** — Strong setup with decent risk/reward.")
                    elif fomo >= 3:
                        st.info("**Wait for Better Setup** — Not strong enough for cautious style.")
                    else:
                        st.warning("**Avoid** — Weak momentum. Better opportunities exist.")

# ==================== MULTI-ACCOUNT PORTFOLIO TRACKER ====================

st.subheader("📊 Multi-Account FOMO Portfolio Tracker")

if "fomo_accounts" not in st.session_state:
    st.session_state.fomo_accounts = {"Main Account": []}

account = st.selectbox("Select Account", list(st.session_state.fomo_accounts.keys()))
positions = st.session_state.fomo_accounts[account]

for pos in positions:
    st.write(f"**{pos['ticker']}** | Buy: ${pos['buy_price']} | Shares: {pos['shares']}")

with st.form("add_pos"):
    t = st.text_input("Ticker")
    bp = st.number_input("Buy Price", min_value=0.01)
    sh = st.number_input("Shares", min_value=0.01)
    if st.form_submit_button("Add Position"):
        st.session_state.fomo_accounts[account].append({
            "ticker": t.upper(),
            "buy_price": bp,
            "shares": sh,
            "buy_date": str(datetime.now().date())
        })
        st.rerun()

# ==================== AUTO FOMO SCANNER ====================

st.subheader("🚀 Auto FOMO Scanner")

base_watchlist = ["MU", "NVDA", "PLTR", "AMD", "AVGO", "BFLY", "SOFI"]
data = []
for t in base_watchlist:
    h, inf, e = get_ticker_data(t, "2mo")
    if e or h is None: continue
    s = calculate_momentum_signals(h, inf or {})
    if s.get("error"): continue
    data.append({
        "Ticker": t,
        "Price": s["current_price"],
        "FOMO Score": s["fomo_score"],
        "Trend": s["trend_direction"]
    })

if data:
    st.dataframe(pd.DataFrame(data).sort_values("FOMO Score", ascending=False), use_container_width=True)
