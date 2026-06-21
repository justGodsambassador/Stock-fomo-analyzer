import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
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
        if hist is None or len(hist) < 15:
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
        gain = delta.where(delta > 0
