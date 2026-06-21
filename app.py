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
            sig = calculate_signals(hist)
            if sig.get("error"):
                st.error(sig["error"])
            else:
                st.markdown(f"**{ticker}** — ${sig['current_price']} | {sig['pct_today']:+.2f}% today | FOMO: {sig['fomo_score']}")

                with st.expander("🎯 What Should You Do Right Now?", expanded=True):
                    fomo = sig['fomo_score']
                    trend = sig['trend_direction']

                    if risk_mode == "Aggressive":
                        if fomo >= 5 and trend == "Uptrend":
                            rec = "**BUY / ADD** — Strong momentum. Good aggressive setup."
                        elif fomo >= 3:
                            rec = "**WATCH / SMALL SIZE** — Decent setup. Can take small position."
                        else:
                            rec = "**SKIP** — Weak signals. Not worth aggressive risk."
                    else:  # Cautious
                        if fomo >= 5 and trend == "Uptrend":
                            rec = "**CAUTIOUS BUY** — Strong setup. Acceptable risk/reward."
                        elif fomo >= 3:
                            rec = "**WAIT** — Not strong enough yet for cautious style."
                        else:
                            rec = "**AVOID** — Weak momentum. Protect capital."

                    st.markdown(rec)

    else:  # Crypto Mode
        st.warning("Crypto Mode — Limited data. Focus on risk management.")

        with st.expander("🎯 What Should You Do Right Now? (Crypto)", expanded=True):
            investment = st.number_input("How much are you considering putting in? ($)", min_value=5, value=10, step=5)

            st.markdown(f"**Analyzing {ticker} with ${investment} entry**")

            if ticker in ["USWR", "ZERO", "DAEMON", "TROLL"]:
                st.warning("This token has already had a very large move. These often reverse hard after big green days.")

            if risk_mode == "Aggressive":
                st.success("**Aggressive Recommendation:** Small size is acceptable if momentum is strong. Plan to take partial profits (30-50%) after big moves. High risk of sharp pullbacks.")
            else:
                st.warning("**Cautious Recommendation:** These extended moves are dangerous. Waiting for a pullback or clearer structure is usually smarter. Protect your small capital.")

# ==================== SCENARIO PLANNER ====================

st.subheader("📊 Scenario Planner — What If I Put In Money Right Now?")

with st.expander("Open Scenario Planner", expanded=False):
    invest_amount = st.number_input("Investment Amount ($)", min_value=5, value=10, step=5)
    target_mult = st.slider("Target Multiple (how many times your money)", 1.5, 10.0, 3.0, 0.5)

    st.markdown("**Realistic Outcomes:**")
    st.write(f"- If it goes **{target_mult}x**: You make ~${invest_amount * (target_mult - 1):.2f}")
    st.write(f"- If it drops **50%**: You lose ~${invest_amount * 0.5:.2f}")
    st.write(f"- If it goes to **zero** (common in low-cap tokens): You lose **${invest_amount:.2f}**")

    st.caption("Low-cap tokens can easily drop 70-90%. Only risk what you can afford to lose completely.")

# ==================== PORTFOLIO TRACKER ====================

st.subheader("📁 Portfolio Tracker + Suggestions")

if "positions" not in st.session_state:
    st.session_state.positions = []

with st.form("portfolio"):
    t = st.text_input("Ticker")
    bp = st.number_input("Buy Price", min_value=0.01)
    amt = st.number_input("Amount Invested ($)", min_value=1.0)
    if st.form_submit_button("Add Position"):
        st.session_state.positions.append({
            "ticker": t.upper(),
            "buy_price": bp,
            "amount": amt,
            "date": str(datetime.now().date())
        })
        st.rerun()

for pos in st.session_state.positions:
    st.write(f"**{pos['ticker']}** | Buy: ${pos['buy_price']} | Invested: ${pos['amount']}")

if st.session_state.positions:
    st.info("Add your current positions above so future analysis can give better personalized suggestions.")

st.caption("This version focuses on clear decisions and realistic risk. Social trend tracking remains limited in free Streamlit.")
