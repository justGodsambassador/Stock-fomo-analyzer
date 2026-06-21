import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="FOMO Stock Companion", page_icon="📈", layout="wide")

st.markdown('<h1 style="color:#1f77b4">📈 FOMO Stock Companion</h1>', unsafe_allow_html=True)

# ==================== MODE SELECTOR ====================
mode = st.radio(
    "Select Mode:",
    ["Stock Mode", "Crypto Mode"],
    horizontal=True,
    help="Stock Mode = Traditional stocks. Crypto Mode = Meme coins & low-cap tokens (like TROLL, ZERO, Daemon)"
)

st.caption(f"**Current Mode:** {mode}")

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

def calculate_basic_signals(hist):
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

# ==================== QUICK ANALYSIS (MODE AWARE) ====================

st.subheader("⚡ Quick Analysis + Companion")

ticker = st.text_input("Enter Ticker", value="MU" if mode == "Stock Mode" else "ZERO").upper().strip()

if ticker:
    if mode == "Stock Mode":
        hist, info, err = get_ticker_data(ticker)
        if err or hist is None:
            st.error(err)
        else:
            sig = calculate_basic_signals(hist)
            if sig.get("error"):
                st.error(sig["error"])
            else:
                st.markdown(f"**{ticker}** — ${sig['current_price']}")
                st.markdown(f"**Trend:** {sig['trend_direction']} | **FOMO Score:** {sig['fomo_score']}")

                with st.expander("🧠 Companion Advice", expanded=True):
                    if sig['fomo_score'] >= 4 and sig['trend_direction'] == "Uptrend":
                        st.success("**Good momentum** — Solid setup for entry on dips.")
                    elif sig['fomo_score'] >= 2:
                        st.info("**Moderate setup** — Wait for clearer confirmation.")
                    else:
                        st.warning("**Weak signals** — Better opportunities likely exist.")

    else:  # Crypto Mode
        st.warning("⚠️ Crypto Mode is limited. Data for low-cap tokens is less reliable.")
        st.markdown(f"**Analyzing {ticker} in Crypto Mode**")

        with st.expander("🧠 Companion Advice (Crypto)", expanded=True):
            st.markdown("""
            **General Guidance for tokens like this:**
            - These tokens are extremely volatile.
            - Big green days (+100%+) are often followed by sharp pullbacks.
            - **Risk Management Rule**: Never risk more than you can afford to lose completely.
            - Consider taking partial profits after big runs (e.g. sell 30-50% when up 2x+).
            """)

            if ticker in ["ZERO", "TROLL", "DAEMON", "GLIPPY"]:
                st.info("This looks like a high-risk meme coin. Strong moves can reverse very quickly.")

# ==================== MULTI-ACCOUNT PORTFOLIO TRACKER ====================

st.subheader("📊 Multi-Account FOMO Portfolio Tracker")

if "fomo_accounts" not in st.session_state:
    st.session_state.fomo_accounts = {"Main Account": []}

account = st.selectbox("Select Account", list(st.session_state.fomo_accounts.keys()))
positions = st.session_state.fomo_accounts[account]

for pos in positions:
    st.write(f"**{pos['ticker']}** | Buy: ${pos['buy_price']} | Shares: {pos['shares']}")

with st.form("add_position"):
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

st.caption("Note: Crypto Mode gives more general advice. Stock Mode uses full technical analysis.")
