# Stock-fomo-analyzer
FOMO Stock Companion - Momentum scanner, backtester, and smart entry optimizer
# FOMO Stock Companion 📈

A powerful local desktop app to track high-momentum "FOMO" stocks for short-term trading opportunities and analyze long-term growth stocks with strong rise potential.

## Features
- **Short-Term FOMO Scanner**: Detects early momentum with high volume surges, price action, RSI, moving averages, and even short-squeeze potential. Perfect for spotting stocks "right as they rise" so you can buy dips/breakouts and sell within days to weeks for big payouts.
- **Long-Term Growth Analyzer**: Evaluates fundamentals (earnings/revenue growth, analyst targets/upside, PE, recommendations) to find stocks positioned for sustained multi-month/year rises (e.g. AI infrastructure leaders).
- **Interactive Charts**: Candlestick + volume + moving averages (SMA20/50) with Plotly for deep analysis.
- **Curated Watchlists**: Suggestions based on current June 2026 market momentum (AI/memory plays like MU, volatile recent gainers like BFLY/CAST, established growth names).
- **Smart Signals**: Color-coded strength (HIGH/MEDIUM/LOW), specific trade ideas, and risk notes.

## Quick Start (5 minutes)
1. Make sure you have Python 3.9+ installed.
2. Open terminal / command prompt in this folder.
3. Run:
   ```
   pip install -r requirements.txt
   ```
4. Launch the app:
   ```
   streamlit run app.py
   ```
5. The app opens in your browser. Start scanning!

## Recommended Usage
- **For quick flips (short-term)**: Use Short-Term tab. Focus on HIGH FOMO Strength + Vol Ratio >1.5-2x. Enter on confirmation, exit into strength. Small position sizes!
- **For investing (long-term)**: Use Long-Term tab. Look for strong EPS/Rev growth + positive analyst upside + reasonable valuation.
- **Pro move**: Scan AI-related names (MU, NVDA, PLTR, DELL, AVGO) during market pullbacks for the best "buy cheap as it rises" entries that can also work as longer holds.

## Current Market Context (June 2026)
- AI infrastructure (chips, memory, servers, software) remains a dominant theme with strong momentum.
- Watch names like **MU** (earnings buzz, memory demand), **NVDA/AVGO/DELL** for sustained moves.
- Recent volatile gainers (BFLY, CAST, etc.) show classic FOMO pumps — high reward but **very high risk** of sharp reversals. Use tiny size and quick exits only.
- Always cross-check with news, earnings calendar, and macro events (rates, geopolitics).

## Important Warnings & Disclaimer
**THIS IS NOT FINANCIAL ADVICE.**  
This tool is for educational and informational purposes only.  

- Short-term momentum trading is high-risk. The majority of retail day/swing traders lose money.
- Stocks with massive single-day gains (especially micro/small caps) frequently reverse hard.
- Data has ~15-minute delay and comes from Yahoo Finance. Always verify with multiple sources.
- Past performance, volume spikes, or analyst targets do **not** guarantee future results.
- Use proper risk management: position sizing (risk only 0.5-2% of portfolio per idea), stop losses, and never trade with money you can't afford to lose.
- Do your own research (DYOR). Consider full fundamentals, news flow, sector trends, and your personal financial situation.

## Customization
- Edit `app.py` to add your own watchlists, change default tickers, adjust signal logic, or add new indicators.
- The code is well-commented for easy modification.

## Support & Feedback
Run it locally for full privacy and speed. No data is sent anywhere.

Enjoy hunting those momentum setups responsibly! 🚀

*Companion v1.0 | June 2026*
