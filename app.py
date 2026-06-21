# ==================== AUTO FOMO SCANNER ====================

st.subheader("🚀 Auto FOMO Scanner — Best Opportunities Right Now")

st.markdown("This scanner automatically analyzes stocks and shows where the **best profit opportunities** currently are.")

# Watchlist (mix of large + smaller names)
base_watchlist = [
    "MU", "NVDA", "PLTR", "AMD", "AVGO", "DELL", "SOFI", "BFLY", "CAST", 
    "WOLF", "RIOT", "MARA", "HUT", "COIN", "TQQQ", "SQQQ", "SPY", "QQQ"
]

user_extra = st.text_input("Add more tickers to scan (comma separated)", placeholder="e.g. ZERO, TROLL, PENGU")
if user_extra:
    extra_tickers = [t.strip().upper() for t in user_extra.split(",") if t.strip()]
    base_watchlist = list(set(base_watchlist + extra_tickers))

if st.button("🔄 Refresh Scanner"):
    st.rerun()

scanner_data = []

for ticker in base_watchlist:
    hist, info, err = get_ticker_data(ticker, period="2mo")
    if err or hist is None or len(hist) < 25:
        continue

    sig = calculate_momentum_signals(hist, info or {})
    if sig.get("error"):
        continue

    # Profit Potential Score (custom logic)
    profit_potential = sig["fomo_score"] * 1.5 + (sig.get("adx", 0) / 5)
    if sig["trend_direction"] == "Uptrend":
        profit_potential += 2

    # Recommendation logic
    if sig["fomo_score"] >= 5 and sig["trend_direction"] == "Uptrend":
        action = "🔥 Day Trade / Strong Buy"
        category = "Day Trading"
    elif sig["fomo_score"] >= 4 and sig.get("adx", 0) > 20:
        action = "📈 Swing Trade"
        category = "Investment"
    elif sig["fomo_score"] >= 3:
        action = "👀 Watch"
        category = "Investment"
    else:
        action = "⏸️ Avoid / Wait"
        category = "Avoid"

    scanner_data.append({
        "Ticker": ticker,
        "Price": sig["current_price"],
        "FOMO Score": sig["fomo_score"],
        "Trend": sig["trend_direction"],
        "ADX": sig.get("adx", 0),
        "Profit Potential": round(profit_potential, 1),
        "Action": action,
        "Category": category
    })

if scanner_data:
    df = pd.DataFrame(scanner_data)
    df = df.sort_values("Profit Potential", ascending=False)

    # Show top opportunities
    st.markdown("### 🔥 Highest Profit Potential Right Now")
    st.dataframe(df.head(10), use_container_width=True, hide_index=True)

    # Day Trading Picks
    day_trade_df = df[df["Category"] == "Day Trading"].head(5)
    if not day_trade_df.empty:
        st.markdown("### ⚡ Best for Day Trading / Short-term Flips")
        st.dataframe(day_trade_df, use_container_width=True, hide_index=True)

    # Investment Picks
    invest_df = df[df["Category"] == "Investment"].head(5)
    if not invest_df.empty:
        st.markdown("### 📈 Best for Longer-term Investment")
        st.dataframe(invest_df, use_container_width=True, hide_index=True)

else:
    st.warning("Could not load scanner data. Try refreshing.")
