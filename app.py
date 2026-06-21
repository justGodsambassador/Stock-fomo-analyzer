#!/usr/bin/env python3
"""
FOMO Stock Companion - Momentum & Growth Tracker
A local Streamlit app to help identify short-term momentum/FOMO opportunities 
and long-term growth stocks with strong rise potential.

Run with: streamlit run app.py
Requires: pip install -r requirements.txt
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

# ------------------ CONFIG & STYLING ------------------
st.set_page_config(
    page_title="FOMO Stock Companion",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better look
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; font-weight: 700; color: #1f77b4; margin-bottom: 0.5rem;}
    .sub-header {font-size: 1.3rem; color: #555; margin-bottom: 1.5rem;}
    .signal-high {background-color: #d4edda; padding: 0.4rem; border-radius: 5px; color: #155724; font-weight: bold;}
    .signal-medium {background-color: #fff3cd; padding: 0.4rem; border-radius: 5px; color: #856404;}
    .signal-low {background-color: #f8d7da; padding: 0.4rem; border-radius: 5px; color: #721c24;}
    .metric-box {background-color: #f8f9fa; padding: 1rem; border-radius: 8px; border-left: 4px solid #1f77b4;}
    .disclaimer {font-size: 0.85rem; color: #666; border: 1px solid #ddd; padding: 1rem; border-radius: 8px; background: #fffbeb;}
    .stTabs [data-baseweb="tab-list"] {gap: 8px;}
</style>
""", unsafe_allow_html=True)

# ------------------ HELPER FUNCTIONS ------------------
@st.cache_data(ttl=300)  # Cache data for 5 minutes to avoid repeated API calls
def get_ticker_data(symbol: str, period: str = "3mo"):
    """Fetch price history and info for a ticker."""
    try:
        ticker = yf.Ticker(symbol.upper().strip())
        hist = ticker.history(period=period, auto_adjust=True)
        if hist.empty or len(hist) < 10:
            return None, None, f"No sufficient data for {symbol}"
        
        info = ticker.info
        return hist, info, None
    except Exception as e:
        return None, None, f"Error fetching {symbol}: {str(e)[:100]}"

def calculate_rsi(close_prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate RSI using Wilder's smoothing method."""
    delta = close_prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_momentum_signals(hist: pd.DataFrame, info: dict) -> dict:
    """Generate short-term FOMO/momentum signals and long-term indicators."""
    if hist is None or len(hist) < 20:
        return {"error": "Insufficient history"}
    
    close = hist['Close']
    volume = hist['Volume']
    current_price = close.iloc[-1]
    prev_close = close.iloc[-2] if len(close) > 1 else current_price
    
    # Price changes
    pct_today = ((current_price / prev_close) - 1) * 100
    pct_5d = ((current_price / close.iloc[-5]) - 1) * 100 if len(close) >= 5 else 0
    pct_20d = ((current_price / close.iloc[-20]) - 1) * 100 if len(close) >= 20 else 0
    
    # Volume
    vol_ma20 = volume.rolling(20).mean().iloc[-1]
    vol_today = volume.iloc[-1]
    vol_ratio = vol_today / vol_ma20 if vol_ma20 > 0 else 1.0
    
    # Moving Averages
    sma20 = close.rolling(20).mean().iloc[-1]
    sma50 = close.rolling(50).mean().iloc[-1] if len(close) >= 50 else sma20
    above_sma20 = current_price > sma20
    sma_trend_up = sma20 > close.rolling(20).mean().iloc[-5] if len(close) >= 25 else False
    
    # RSI
    rsi_series = calculate_rsi(close)
    current_rsi = rsi_series.iloc[-1] if not pd.isna(rsi_series.iloc[-1]) else 50
    
    # Short interest (if available)
    short_pct = info.get('shortPercentOfFloat', 0) or 0
    if isinstance(short_pct, (int, float)) and short_pct > 100:  # Sometimes it's in percent already or raw
        short_pct = short_pct / 100 if short_pct > 1 else short_pct
    
    # --- SHORT-TERM FOMO / MOMENTUM LOGIC ---
    fomo_score = 0
    signals = []
    
    if vol_ratio >= 2.0 and pct_today >= 4:
        fomo_score += 3
        signals.append("🔥 Very High Volume Surge + Strong Price Move")
    elif vol_ratio >= 1.5 and pct_today >= 2.5:
        fomo_score += 2
        signals.append("📈 High Volume + Solid Price Rise")
    elif vol_ratio >= 1.3 and pct_today > 0:
        fomo_score += 1
        signals.append("📊 Elevated Volume with Positive Price Action")
    
    if above_sma20 and sma_trend_up:
        fomo_score += 2
        signals.append("✅ Price above rising SMA20 (uptrend building)")
    elif above_sma20:
        fomo_score += 1
        signals.append("➡️ Price holding above SMA20")
    
    if 35 < current_rsi < 65:
        fomo_score += 1
        signals.append("⚖️ RSI in healthy momentum zone (not overbought)")
    elif current_rsi < 35:
        signals.append("💎 RSI oversold - potential bounce candidate if volume confirms")
    
    # Dip then rip pattern (good for "buy cheap as it rises")
    if pct_5d < -3 and pct_today > 1.5 and vol_ratio > 1.4:
        fomo_score += 2
        signals.append("🔄 Dip-then-rip: Recent pullback + strong recovery volume")
    
    # Short squeeze potential
    squeeze_potential = False
    if short_pct > 8 and vol_ratio > 1.5 and pct_today > 2:
        fomo_score += 2
        signals.append("🚀 Potential short squeeze (high short interest + volume surge)")
        squeeze_potential = True
    
    # Classify signal strength
    if fomo_score >= 5:
        strength = "HIGH"
        action = "Consider buying on strength or small pullback to support. Tight stop below recent low. Target 12-25% or next resistance. Good for 3-10 day swing."
    elif fomo_score >= 3:
        strength = "MEDIUM"
        action = "Watch for confirmation (sustained volume). Possible entry on dip to SMA or VWAP. Target 8-15%. Manage risk tightly."
    else:
        strength = "LOW / Watch"
        action = "No strong momentum yet. Wait for volume spike + price breakout above recent highs or SMA. Or use for longer-term watch."
    
    # --- LONG-TERM GROWTH INDICATORS ---
    market_cap = info.get('marketCap', 'N/A')
    pe_ratio = info.get('trailingPE') or info.get('forwardPE', 'N/A')
    eps_growth = info.get('earningsGrowth', 'N/A')  # quarterly or annual sometimes
    rev_growth = info.get('revenueGrowth', 'N/A')
    
    target_price = info.get('targetMeanPrice')
    upside = None
    if target_price and current_price:
        upside = round(((target_price - current_price) / current_price) * 100, 1)
    
    analyst_rec = info.get('recommendationKey', 'N/A')
    
    long_term_score = 0
    lt_reasons = []
    
    if isinstance(eps_growth, (int, float)) and eps_growth > 0.15:
        long_term_score += 2
        lt_reasons.append(f"Strong EPS growth ({eps_growth*100:.1f}%)")
    if isinstance(rev_growth, (int, float)) and rev_growth > 0.12:
        long_term_score += 2
        lt_reasons.append(f"Solid revenue growth ({rev_growth*100:.1f}%)")
    
    if upside and upside > 15:
        long_term_score += 2
        lt_reasons.append(f"Analyst upside potential ~{upside}%")
    elif upside and upside > 5:
        long_term_score += 1
    
    if analyst_rec in ['buy', 'strong_buy']:
        long_term_score += 2
        lt_reasons.append("Analyst consensus: Buy/Strong Buy")
    
    # Valuation check (rough)
    if isinstance(pe_ratio, (int, float)) and pe_ratio < 40:
        long_term_score += 1
        lt_reasons.append("Reasonable valuation (PE < 40)")
    
    if long_term_score >= 5:
        lt_outlook = "STRONG GROWTH CANDIDATE"
    elif long_term_score >= 3:
        lt_outlook = "GOOD LONG-TERM POTENTIAL"
    else:
        lt_outlook = "MODERATE / NEEDS MORE DATA"
    
    return {
        "current_price": round(current_price, 2),
        "pct_today": round(pct_today, 2),
        "pct_5d": round(pct_5d, 2),
        "pct_20d": round(pct_20d, 2),
        "vol_ratio": round(vol_ratio, 2),
        "rsi": round(current_rsi, 1),
        "sma20": round(sma20, 2),
        "above_sma20": above_sma20,
        "fomo_score": fomo_score,
        "fomo_strength": strength,
        "fomo_signals": signals,
        "short_term_action": action,
        "squeeze_potential": squeeze_potential,
        "short_pct": round(short_pct * 100, 1) if short_pct else "N/A",
        # Long-term
        "market_cap": market_cap,
        "pe_ratio": pe_ratio if isinstance(pe_ratio, (int, float)) else "N/A",
        "eps_growth": eps_growth if isinstance(eps_growth, (int, float)) else "N/A",
        "rev_growth": rev_growth if isinstance(rev_growth, (int, float)) else "N/A",
        "analyst_upside": upside,
        "analyst_rec": analyst_rec,
        "long_term_score": long_term_score,
        "long_term_outlook": lt_outlook,
        "long_term_reasons": lt_reasons if lt_reasons else ["Limited fundamental data available - check latest earnings"],
        "error": None
    }

def create_candlestick_chart(hist: pd.DataFrame, symbol: str, signals: dict):
    """Create interactive Plotly candlestick chart with MAs and volume."""
    hist = hist.copy()
    hist['SMA20'] = hist['Close'].rolling(20).mean()
    hist['SMA50'] = hist['Close'].rolling(50).mean()
    
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3],
        subplot_titles=(f"{symbol} - Price & Momentum", "Volume")
    )
    
    # Candlestick
    fig.add_trace(
        go.Candlestick(
            x=hist.index,
            open=hist['Open'],
            high=hist['High'],
            low=hist['Low'],
            close=hist['Close'],
            name="Price",
            increasing_line_color='#26a69a',
            decreasing_line_color='#ef5350'
        ),
        row=1, col=1
    )
    
    # SMAs
    fig.add_trace(
        go.Scatter(x=hist.index, y=hist['SMA20'], line=dict(color='#ff7f0e', width=1.5), name="SMA 20"),
        row=1, col=1
    )
    if len(hist) >= 50:
        fig.add_trace(
            go.Scatter(x=hist.index, y=hist['SMA50'], line=dict(color='#d62728', width=1.5), name="SMA 50"),
            row=1, col=1
        )
    
    # Volume bars
    colors = ['#26a69a' if hist['Close'].iloc[i] >= hist['Open'].iloc[i] else '#ef5350' for i in range(len(hist))]
    fig.add_trace(
        go.Bar(x=hist.index, y=hist['Volume'], marker_color=colors, name="Volume", showlegend=False),
        row=2, col=1
    )
    
    # Highlight recent high volume if applicable
    if signals.get('vol_ratio', 0) > 1.5:
        last_idx = hist.index[-1]
        fig.add_annotation(
            x=last_idx, y=hist['High'].iloc[-1] * 1.02,
            text=f"High Vol Day ({signals['vol_ratio']}x)",
            showarrow=True, arrowhead=1, ax=0, ay=-40,
            font=dict(color="#d62728", size=11)
        )
    
    fig.update_layout(
        height=550,
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=20, t=60, b=20),
        hovermode="x unified"
    )
    fig.update_yaxes(title_text="Price ($)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    
    return fig

# ------------------ UI SECTIONS ------------------
st.markdown('<h1 class="main-header">📈 FOMO Stock Companion</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Track high-momentum stocks for short-term flips & identify long-term growth opportunities with strong rise potential</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings & Info")
    st.markdown("**Data Source:** Yahoo Finance (free, ~15min delay)")
    st.markdown("**Update Frequency:** Real-time when you click Scan")
    
    risk_level = st.select_slider(
        "Your Risk Tolerance",
        options=["Conservative", "Moderate", "Aggressive"],
        value="Moderate"
    )
    
    st.markdown("---")
    st.markdown("### Quick Tips")
    st.info("""
    **Short-term FOMO:** Focus on vol_ratio >1.5 + price rise. Buy early strength, sell into momentum (days-weeks). 
    **Long-term:** Prioritize earnings/revenue growth + analyst support over hype.
    """)
    
    st.markdown("---")
    st.caption("⚠️ **IMPORTANT DISCLAIMER**")
    st.caption("This is an educational analysis tool only. NOT financial advice. Short-term trading carries high risk of loss. Most retail traders lose money. Always do your own research (DYOR), consider news, macro events, position sizing, and risk management. Past performance does not predict future results. Micro-cap/high-gainer stocks are especially volatile and can reverse sharply.")

# Main Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    "🔥 Short-Term FOMO Scanner", 
    "📈 Long-Term Growth Analyzer", 
    "📋 Discover & Watchlists", 
    "📖 How to Use & Strategy"
])

# ========== TAB 1: SHORT-TERM FOMO SCANNER ==========
with tab1:
    st.header("🔥 Short-Term Momentum & FOMO Scanner")
    st.markdown("Detect stocks showing **early signs of rising momentum** with high volume (the classic FOMO setup). Ideal for spotting potential quick moves to sell within days to a couple weeks.")
    
    col_input, col_examples = st.columns([2, 1])
    
    with col_input:
        ticker_input = st.text_input(
            "Tickers to analyze (comma-separated)",
            value="MU, BFLY, CAST, NVDA, PLTR, DELL",
            help="Examples from recent movers: MU (memory/AI), BFLY & CAST (recent high % gainers), NVDA/PLTR/DELL (established momentum)"
        )
    
    with col_examples:
        st.markdown("**Quick Load Examples:**")
        if st.button("🚀 Recent Volatile Gainers (High Risk/High Reward)"):
            ticker_input = "BFLY, CAST, LNKS, HQ, WOLF"
            st.rerun()
        if st.button("🤖 AI & Memory Momentum"):
            ticker_input = "MU, NVDA, AMD, AVGO, SNDK, DELL"
            st.rerun()
        if st.button("📊 Balanced Watchlist"):
            ticker_input = "MU, PLTR, NVDA, BFLY, GOOGL"
            st.rerun()
    
    tickers = [t.strip().upper() for t in ticker_input.split(",") if t.strip()]
    
    if st.button("🚀 SCAN FOR MOMENTUM SIGNALS", type="primary", use_container_width=True):
        if not tickers:
            st.error("Please enter at least one ticker symbol.")
        else:
            results = []
            progress = st.progress(0, text="Fetching data and calculating signals...")
            
            for i, sym in enumerate(tickers):
                hist, info, err = get_ticker_data(sym)
                if err:
                    results.append({"Ticker": sym, "Error": err})
                else:
                    sig = calculate_momentum_signals(hist, info or {})
                    if sig.get("error"):
                        results.append({"Ticker": sym, "Error": sig["error"]})
                    else:
                        results.append({
                            "Ticker": sym,
                            "Price": sig["current_price"],
                            "Today %": sig["pct_today"],
                            "5D %": sig["pct_5d"],
                            "Vol Ratio": sig["vol_ratio"],
                            "RSI": sig["rsi"],
                            "FOMO Strength": sig["fomo_strength"],
                            "Short Interest %": sig.get("short_pct", "N/A"),
                            "Signal Summary": " | ".join(sig["fomo_signals"][:2]) if sig["fomo_signals"] else "No strong signals"
                        })
                progress.progress((i + 1) / len(tickers), text=f"Processed {sym}...")
            
            progress.empty()
            
            # Results Table
            df = pd.DataFrame(results)
            if "Error" in df.columns:
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                # Color code strength
                def color_strength(val):
                    if "HIGH" in str(val):
                        return "background-color: #d4edda; color: #155724; font-weight: bold"
                    elif "MEDIUM" in str(val):
                        return "background-color: #fff3cd; color: #856404"
                    else:
                        return "background-color: #f8d7da; color: #721c24"
                
                styled_df = df.style.applymap(color_strength, subset=["FOMO Strength"])
                st.dataframe(styled_df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.subheader("📊 Deep Dive Analysis")
            selected = st.selectbox("Select a ticker for detailed chart & trade ideas:", 
                                    options=[r["Ticker"] for r in results if "Error" not in r])
            
            if selected:
                hist, info, _ = get_ticker_data(selected)
                sig = calculate_momentum_signals(hist, info or {})
                
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Current Price", f"${sig['current_price']}")
                c2.metric("Today's Change", f"{sig['pct_today']:+.2f}%", delta_color="normal")
                c3.metric("Volume Ratio (vs 20d avg)", f"{sig['vol_ratio']}x")
                c4.metric("RSI (14)", f"{sig['rsi']}")
                
                st.markdown(f"**FOMO Strength: {sig['fomo_strength']}**")
                for s in sig["fomo_signals"]:
                    st.markdown(f"- {s}")
                
                st.info(f"**Short-Term Action Idea:** {sig['short_term_action']}")
                
                if sig.get("squeeze_potential"):
                    st.warning("⚠️ Short squeeze candidate — monitor closely, these can move fast both ways.")
                
                # Chart
                st.plotly_chart(create_candlestick_chart(hist, selected, sig), use_container_width=True)
                
                st.caption("Chart shows last 3 months. Green/Red candles = up/down days. Orange = SMA20, Red = SMA50. High volume bars highlighted in context.")

# ========== TAB 2: LONG-TERM GROWTH ==========
with tab2:
    st.header("📈 Long-Term Growth Stock Analyzer")
    st.markdown("Evaluate stocks for **multi-month to multi-year** holding with strong fundamental rise potential (earnings growth, analyst support, sector tailwinds like AI).")
    
    lt_input = st.text_input(
        "Tickers for long-term analysis",
        value="NVDA, MU, PLTR, AVGO, MSFT, GOOGL, DELL",
        key="lt_tickers"
    )
    lt_tickers = [t.strip().upper() for t in lt_input.split(",") if t.strip()]
    
    if st.button("📊 ANALYZE LONG-TERM POTENTIAL", type="primary"):
        if not lt_tickers:
            st.error("Enter tickers.")
        else:
            lt_results = []
            prog = st.progress(0)
            for idx, sym in enumerate(lt_tickers):
                hist, info, err = get_ticker_data(sym, period="6mo")
                if err or not info:
                    lt_results.append({"Ticker": sym, "Status": err or "No data"})
                else:
                    sig = calculate_momentum_signals(hist, info)
                    mcap = sig.get("market_cap")
                    if isinstance(mcap, (int, float)):
                        mcap_str = f"${mcap/1e9:.1f}B" if mcap < 1e12 else f"${mcap/1e12:.2f}T"
                    else:
                        mcap_str = str(mcap)
                    
                    lt_results.append({
                        "Ticker": sym,
                        "Price": sig["current_price"],
                        "Market Cap": mcap_str,
                        "PE Ratio": sig["pe_ratio"],
                        "EPS Growth": f"{sig['eps_growth']*100:.1f}%" if isinstance(sig['eps_growth'], (int,float)) else "N/A",
                        "Rev Growth": f"{sig['rev_growth']*100:.1f}%" if isinstance(sig['rev_growth'], (int,float)) else "N/A",
                        "Analyst Upside": f"+{sig['analyst_upside']}%" if sig['analyst_upside'] else "N/A",
                        "Outlook": sig["long_term_outlook"],
                        "Key Reasons": "; ".join(sig["long_term_reasons"][:2])
                    })
                prog.progress((idx+1)/len(lt_tickers))
            prog.empty()
            
            lt_df = pd.DataFrame(lt_results)
            st.dataframe(lt_df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.subheader("Individual Long-Term Thesis")
            sel_lt = st.selectbox("Select ticker for full breakdown:", options=[r["Ticker"] for r in lt_results if "Status" not in r])
            
            if sel_lt:
                hist, info, _ = get_ticker_data(sel_lt, "6mo")
                sig = calculate_momentum_signals(hist, info or {})
                
                st.markdown(f"### {sel_lt} — {sig['long_term_outlook']}")
                
                cols = st.columns(3)
                cols[0].metric("Market Cap", sig.get("market_cap", "N/A"))
                cols[1].metric("Trailing/Forward PE", sig["pe_ratio"])
                cols[2].metric("Analyst Mean Target Upside", f"+{sig['analyst_upside']}%" if sig['analyst_upside'] else "N/A")
                
                st.markdown("**Why this could have a good multi-year rise:**")
                for reason in sig["long_term_reasons"]:
                    st.markdown(f"- {reason}")
                
                if sig["analyst_rec"] not in ["N/A", None]:
                    st.markdown(f"- Analyst consensus: **{sig['analyst_rec'].replace('_', ' ').title()}**")
                
                st.caption("Note: Growth metrics come from latest available data (may be quarterly/TTM). Always verify with latest 10-Q/10-K and earnings call.")

# ========== TAB 3: DISCOVER & WATCHLISTS ==========
with tab3:
    st.header("📋 Discover Trending & Curated Watchlists")
    st.markdown("Based on current market momentum (June 2026 data), here are relevant starting points. Use these in the Scanner tabs above.")
    
    st.subheader("🔥 Current High-Momentum / Recent Gainers (FOMO-prone)")
    st.markdown("""
    - **BFLY** (Butterfly Network) — Recent +55%+ day moves, healthcare tech
    - **CAST** (FreeCast) — Massive multi-day gains reported
    - **MU** (Micron) — AI memory demand, earnings buzz, often compared to NVDA momentum
    - **WOLF** (Wolfspeed), **HQ**, **LNKS** — Volatile recent movers
    - **Warning:** Many micro/small-cap gainers are extremely risky and can crash just as fast. Suitable only for very small position sizes and quick exits.
    """)
    
    st.subheader("🤖 Strong AI Infrastructure & Growth Names (Better for swings + long-term)")
    st.markdown("""
    - **NVDA, AVGO, AMD** — AI chip leaders
    - **MU, SNDK, STX, DELL** — Memory, storage, servers benefiting from AI buildout
    - **PLTR** — AI software platforms, strong growth narrative
    - These often show sustained volume on dips and have more institutional backing.
    """)
    
    st.subheader("📈 Broader Long-Term Growth Ideas")
    st.markdown("""
    - **MSFT, GOOGL, AMZN** — Cloud + AI integration
    - **LLY** or other healthcare growth if interested in non-tech
    - Focus on companies with proven earnings beats, expanding margins, and large addressable markets.
    """)
    
    st.info("💡 **Pro Tip:** Run the Short-Term Scanner on the AI names during market dips for better 'buy cheap as it rises' entries. Use Long-Term tab to check if fundamentals support holding through volatility.")

# ========== TAB 4: HOW TO USE & STRATEGY ==========
with tab4:
    st.header("📖 How to Use This Companion + Recommended Strategy")
    
    st.markdown("""
    ### Quick Start
    1. Go to **Short-Term FOMO Scanner** tab
    2. Enter or load tickers (start with 4-8 names)
    3. Click **Scan**
    4. Look for **HIGH** or **MEDIUM** FOMO Strength + high Vol Ratio
    5. Click into deep dive for chart + specific trade idea
    6. For longer holds, switch to **Long-Term Growth Analyzer**
    
    ### Short-Term Flip Strategy (Days to ~3 Weeks)
    - **Entry:** When you see rising volume + price breaking above recent consolidation or SMA20, especially after a small dip ("buy the dip in an uptrend").
    - **Confirmation:** Vol ratio >1.5x average + positive price action + RSI not extremely overbought.
    - **Position Size:** Very small (0.5-2% of portfolio per trade). These moves can reverse violently.
    - **Exit Rules:** 
      - Take partial profits at +10-15%
      - Trail stop or sell most if volume dries up and price stalls
      - Hard stop if breaks key support (e.g. below SMA20 or recent swing low)
    - **Best setups:** Liquid mid/large caps with real news/flow (earnings, contracts, sector rotation). Avoid pure low-float pumps unless you have experience.
    
    ### Long-Term Growth Strategy
    - Use when you want to hold 6+ months.
    - Prioritize **earnings growth + revenue growth + reasonable valuation + analyst support**.
    - AI infrastructure theme (chips, memory, data centers, software) has strong secular tailwinds in 2026.
    - Add on dips to 50/200-day MA or after earnings beats.
    - Re-evaluate fundamentals quarterly.
    
    ### Combining Both
    Many traders use the short-term scanner to find names that are "working" right now, then check the long-term tab to see if it also has fundamental support for a bigger position / longer hold.
    
    ### Risk Management (Critical)
    - Never risk more than you can afford to lose on any single idea.
    - Use stop losses always.
    - Be extra cautious with names showing 50%+ single-day moves — they are often reversing soon after.
    - Macro events (interest rates, geopolitics, earnings season) can override technicals.
    """)
    
    st.markdown("---")
    st.caption("Built with ❤️ for curious investors | Data via Yahoo Finance | Not affiliated with any broker or exchange | Verify all information independently")

# Footer
st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Companion v1.0 | Run locally for privacy & speed")
