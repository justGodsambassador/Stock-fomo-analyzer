import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="FOMO Stock Companion", page_icon="📈", layout="wide")

st.markdown('<h1 style="color:#1f77b4">📈 FOMO Stock Companion</h1>', unsafe_allow_html=True)

# ==================== HELPER FUNCTIONS ====================

def get_ticker_data(symbol, period="3mo"):
    try:
        ticker = yf.Ticker(symbol.upper().strip())
        hist = ticker.history(period=period, auto_adjust=True)
        info = ticker.info
        if hist is None or len(hist) < 10:
            return None, None, "Not enough price history"
        return hist, info, None
    except Exception as e:
        return None, None, str(e)

def calculate_momentum_signals(hist, info):
    if hist is None or len(hist) < 25:
        return {"error": "Not enough data for analysis"}

    try:
        close = hist['Close']
        current_price = close.iloc[-1]
        pct_today = ((current_price / close.iloc[-2]) - 1) * 100 if len(close) > 1 else 0
        vol_ma = hist['Volume'].rolling(20).mean().iloc[-1]
        vol_ratio = hist['Volume'].iloc[-1] / vol_ma if vol_ma > 0 else 1.0

        sma20 = close.rolling(20).mean().iloc[-1]
        sma50 = close.rolling(50).mean().iloc[-1] if len(close) >= 50 else sma20

        # RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi = 100 - (100 / (1 + gain / loss)).iloc[-1]

        # Simple trend
        trend = "Uptrend" if current_price > sma20 and sma20 > sma50 else \
                "Downtrend" if current_price < sma20 and sma20 < sma50 else "Sideways"

        # FOMO Score
        fomo_score = 0
        signals = []
        if vol_ratio > 1.5 and pct_today > 2:
            fomo_score += 2
            signals.append("High Volume")
        if current_price > sma20:
            fomo_score += 1
            signals.append("Above SMA20")

        return {
            "current_price": round(current_price, 2),
            "pct_today": round(pct_today, 2),
            "vol_ratio": round(vol_ratio, 2),
            "rsi": round(rsi, 1),
            "fomo_score": fomo_score,
            "trend_direction": trend,
            "fomo_signals": signals,
            "error": None
        }
    except Exception as e:
