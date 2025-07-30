import yfinance as yf
import numpy as np
import pandas as pd
from scipy.signal import find_peaks

def get_stock_data(stock_name, timeframe):
    """Fetch stock data with timeframe-specific periods"""
    period_map = {
        '5m': '7d',
        '15m': '15d',
        '1h': '30d',
        '4h': '60d',
        '1d': '3mo',
        '1wk': '1y',
        '1mo': '2y'
    }

    try:
        data = yf.download(
            stock_name,
            period=period_map[timeframe],
            interval=timeframe,
            progress=False,
            timeout=15,
            auto_adjust=True
        )

        # Filter market hours (9:15 to 15:30) for intraday timeframes
        if timeframe in ['5m', '15m', '1h', '4h']:
            data = data.between_time('09:15', '15:30')

        return data.dropna() if not data.empty else None

    except Exception as e:
        print(f"Error fetching {stock_name}: {str(e)}")
        return None

def calculate_ema(data, window=50):
    """Compute EMA"""
    return data['Close'].ewm(span=window, adjust=False).mean()

def get_support_resistance_levels(data, lookback=50):
    """Identify recent support and resistance levels"""
    recent_data = data.iloc[-lookback:]

    lows = recent_data['Low'].to_numpy().squeeze()
    highs = recent_data['High'].to_numpy().squeeze()

    # Ensure 1D array for find_peaks
    lows = np.ravel(lows)
    highs = np.ravel(highs)

    support_idx, _ = find_peaks(-lows, distance=5, prominence=1)
    resistance_idx, _ = find_peaks(highs, distance=5, prominence=1)

    support_levels = lows[support_idx]
    resistance_levels = highs[resistance_idx]

    return {
        'support': sorted(support_levels[-3:].tolist()),
        'resistance': sorted(resistance_levels[-3:].tolist())
    }

def analyze_stock(stock_name, timeframe='1d'):
    """Main stock analysis function"""
    data = get_stock_data(stock_name, timeframe)
    if data is None or len(data) < 20:
        print(f"Insufficient data for {stock_name} ({timeframe})")
        return None

    try:
        last_close = data['Close'].iloc[-1].item()
        ema_50 = calculate_ema(data)
        ema_last = ema_50.iloc[-1].item()

        # Trend direction
        uptrend = last_close > ema_last

        # HH/HL pattern (3-bar)
        highs = data['High'].to_numpy().squeeze()[-3:]
        lows = data['Low'].to_numpy().squeeze()[-3:]
        hh_hl = (highs[-1] > highs[-2] > highs[-3]) and (lows[-1] > lows[-2] > lows[-3])

        # Support/Resistance levels
        levels = get_support_resistance_levels(data)
        near_resistance = any(
            abs(last_close - level) / level < 0.02 for level in levels['resistance']
        )

        # Volume spike detection
        volumes = data['Volume'].to_numpy().squeeze()[-10:]
        volume_spike = volumes[-1] > np.mean(volumes[:-1]) * 1.5

        # ATR (Average True Range)
        prev_close = data['Close'].shift(1).to_numpy().squeeze()
        high = data['High'].to_numpy().squeeze()
        low = data['Low'].to_numpy().squeeze()

        tr = np.maximum.reduce([
            high - low,
            np.abs(high - prev_close),
            np.abs(low - prev_close)
        ])
        atr = pd.Series(tr).rolling(14).mean().iloc[-1]

        # Risk/Reward Calculation
        stop_loss = last_close - 2 * atr
        target = last_close + 4 * atr
        rr_ratio = (target - last_close) / (last_close - stop_loss)

        return {
            "results": {
                "In uptrend": uptrend,
                "HH/HL pattern": hh_hl,
                "Near resistance": near_resistance,
                "Volume spike": volume_spike,
                "Clear levels": True,
                "Good R/R ratio": rr_ratio >= 2
            },
            "levels": levels,
            "stop_loss": round(stop_loss, 2),
            "target": round(target, 2),
            "rr_ratio": round(rr_ratio, 2),
            "data": data,
            "ema_50": ema_50
        }

    except Exception as e:
        print(f"Analysis error: {str(e)}")
        return None
