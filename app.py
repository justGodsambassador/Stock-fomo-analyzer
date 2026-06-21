import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="FOMO Stock Companion", page_icon="📈", layout="wide")

st.markdown('<h1 style="color:#1f77b4">📈 FOMO Stock Companion</h1>', unsafe_allow_html=True)

# ==================== MODE SELECTORS ====================
col1, col2 = st.columns(2)
with col1:
    data_mode = st.radio("Data Mode", ["Stock Mode", "Crypto Mode"], horizontal=True)
with col2:
    risk_mode = st.radio("Risk Style", ["Aggressive", "Cautious"], horizontal=True)

st.caption(f"**{data_mode}** | **{risk_mode}** Mode")

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

# ==================== QUICK ANALYSIS + ACTIONABLE COMPANION ====================

st.subheader("⚡ Quick Analysis + Actionable Suggestions")

ticker = st.text_input("Enter Ticker", value="USWR" if data_mode == "Crypto Mode" else "MU").upper().strip()

if ticker:
    if data_mode == "Stock Mode":
        hist, info, err = get_ticker_data(ticker)
        if err or hist is None:
            st.error(err)
        else:
            sig = calculate_signals(hist)
            if sig.get("error"):
                st.error(sig["error"])
            else:
                st.markdown(f"**{ticker}** — ${sig['current_price']} | {sig['pct_today']:+.2f}% today")

                with st.expander("🧠 What Should You Do Right Now?", expanded=True):
                    fomo = sig['fomo_score']
                    trend = sig['trend_direction']

                    if risk_mode == "Aggressive":
                        if fomo >= 4 and trend == "Uptrend":
                            st.success("**Buy / Add on dips** — Strong momentum. Good aggressive setup.")
                        elif fomo >= 3:
                            st.info("**Watch for entry** — Decent momentum. Can take small size.")
                        else:
                            st.warning("**Skip** — Weak signals. Not worth the risk in aggressive mode.")
                    else:  # Cautious
                        if fomo >= 5 and trend == "Uptrend":
                            st.success("**Cautious Buy** — Strong setup with acceptable risk/reward.")
                        elif fomo >= 3:
                            st.info("**Wait** — Not strong enough yet. Better setups likely exist.")
                        else:
                            st.warning("**Avoid** — Weak momentum. Protect capital.")

    else:  # Crypto Mode
        st.warning("Crypto Mode: Data is limited. Focus is on risk management and momentum.")

        with st.expander("🧠 What Should You Do Right Now? (Crypto)", expanded=True):
            st.markdown(f"**Analyzing {ticker}**")

            # Simple heuristic for crypto tokens
            if ticker in ["USWR", "ZERO", "DAEMON", "TROLL"]:
                st.info("This token has already had a very large move. These often pull back sharply after big green days.")

            if risk_mode == "Aggressive":
                st.success("**Aggressive Take:** If you're already in profit, consider taking partial profits (30-50%) and letting the rest run. Adding more here is high risk.")
            else:
                st.warning("**Cautious Take:** These moves are extended. Better to wait for a pullback or clearer structure before adding. Protect your capital.")

# ==================== PORTFOLIO TRACKER ====================

st.subheader("📊 Portfolio Tracker + Live Suggestions")

if "positions" not in st.session_state:
    st.session_state.positions = []

with st.form("add_pos"):
    t = st.text_input("Ticker")
    bp = st.number_input("Buy Price", min_value=0.01)
    sh = st.number_input("Shares / Amount", min_value=0.01)
    if st.form_submit_button("Add / Update Position"):
        st.session_state.positions.append({
            "ticker": t.upper(),
            "buy_price": bp,
            "shares": sh,
            "date": str(datetime.now().date())
        })
        st.rerun()

for pos in st.session_state.positions:
    st.write(f"**{pos['ticker']}** | Buy: ${pos['buy_price']} | Amount: {pos['shares']}")

st.caption("Add your current positions above so the app can give better personalized suggestions.")
