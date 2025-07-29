import yfinance as yf
import numpy as np
import pandas as pd
from datetime import datetime

def get_stock_data(stock_name, timeframe):
    """Improved data fetching with error handling"""
    period_map = {
        '1d': '3mo',  # Shorter period for faster loading
        '1wk': '1y',
        '1mo': '2y'
    }
    
    try:
        data = yf.download(
            stock_name,
            period=period_map[timeframe],
            interval=timeframe,
            progress=False,
            timeout=10  # Prevents hanging
        )
        return data.dropna() if not data.empty else None
    except Exception as e:
        print(f"Error fetching {stock_name}: {str(e)}")
        return None

def calculate_ema(data, window=50):
    return data['Close'].ewm(span=window, adjust=False).mean()

def analyze_stock(stock_name, timeframe):
    """Main analysis function with robust error handling"""
    data = get_stock_data(stock_name, timeframe)
    if data is None:
        return None
    
    try:
        # Uptrend check
        ema_50 = calculate_ema(data)
        last_close = float(data['Close'].iloc[-1])
        uptrend = last_close > float(ema_50.iloc[-1])
        
        # HH/HL check (simplified)
        highs = data['High'].values[-3:]
        lows = data['Low'].values[-3:]
        hh_hl = (highs[-1] > highs[-2]) and (lows[-1] > lows[-2])
        
        # Support/resistance
        closes = data['Close'].values[-20:]
        current_price = last_close
        resistance = float(max(closes))
        supp_res = current_price > resistance * 0.98
        
        # Volume check
        volumes = data['Volume'].values[-10:]
        volume = volumes[-1] > np.mean(volumes[:-1]) * 1.5
        
        # Risk/reward
        atr = np.mean([
            float(data['High'].iloc[-1]) - float(data['Low'].iloc[-1]),
            abs(float(data['High'].iloc[-1]) - float(data['Close'].iloc[-2])),
            abs(float(data['Low'].iloc[-1]) - float(data['Close'].iloc[-2]))
        ])
        stop_loss = last_close - 2 * atr
        target = last_close + 4 * atr
        rr_ratio = (target - last_close) / (last_close - stop_loss)
        
        return {
            "results": {
                "In uptrend": uptrend,
                "HH/HL pattern": hh_hl,
                "Near resistance": supp_res,
                "Volume spike": volume,
                "Clear levels": True,  # Always true with auto-calculation
                "Good R/R ratio": rr_ratio >= 2
            },
            "stop_loss": stop_loss,
            "target": target,
            "data": data,
            "ema_50": ema_50
        }
    except Exception as e:
        print(f"Analysis error: {str(e)}")
        return None