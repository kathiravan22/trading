import yfinance as yf
import numpy as np
from scipy.signal import find_peaks

def get_stock_data(stock_name, timeframe):
    period_map = {
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
            timeout=10
        )
        return data.dropna() if not data.empty else None
    except Exception as e:
        print(f"Error fetching {stock_name}: {str(e)}")
        return None

def calculate_ema(data, window=50):
    return data['Close'].ewm(span=window, adjust=False).mean()

def get_resistance_levels(data, distance=5, prominence=1):
    """Detects swing highs using peak detection on 'High' prices."""
    highs = data['High'].values
    peaks, _ = find_peaks(highs, distance=distance, prominence=prominence)
    return data['High'].iloc[peaks]

def analyze_stock(stock_name, timeframe='1d'):
    data = get_stock_data(stock_name, timeframe)
    if data is None:
        return None

    try:
        last_close = float(data['Close'].iloc[-1])
        ema_50 = calculate_ema(data)
        uptrend = last_close > float(ema_50.iloc[-1])

        # HH-HL simplified check (improved: 3-bar trend)
        highs = data['High'].values[-3:]
        lows = data['Low'].values[-3:]
        hh = highs[-1] > highs[-2] > highs[-3]
        hl = lows[-1] > lows[-2] > lows[-3]
        hh_hl = hh and hl

        # Real resistance detection
        resistance_levels = get_resistance_levels(data)
        near_resistance = False
        if not resistance_levels.empty:
            nearest_resistance = resistance_levels[resistance_levels > last_close].min(initial=np.nan)
            if not np.isnan(nearest_resistance):
                near_resistance = last_close >= nearest_resistance * 0.98  # within 2% of resistance

        # Volume spike
        volumes = data['Volume'].values[-10:]
        volume_spike = volumes[-1] > np.mean(volumes[:-1]) * 1.5

        # ATR(14) calculation
        data['H-L'] = data['High'] - data['Low']
        data['H-PC'] = abs(data['High'] - data['Close'].shift(1))
        data['L-PC'] = abs(data['Low'] - data['Close'].shift(1))
        data['TR'] = data[['H-L', 'H-PC', 'L-PC']].max(axis=1)
        atr = data['TR'].rolling(14).mean().iloc[-1]

        # R/R calculation
        stop_loss = last_close - 2 * atr
        target = last_close + 4 * atr
        rr_ratio = (target - last_close) / (last_close - stop_loss)
        good_rr = rr_ratio >= 2

        return {
            "results": {
                "In uptrend": uptrend,
                "HH/HL pattern": hh_hl,
                "Near resistance": near_resistance,
                "Volume spike": volume_spike,
                "Clear levels": True,
                "Good R/R ratio": good_rr
            },
            "stop_loss": round(stop_loss, 2),
            "target": round(target, 2),
            "rr_ratio": round(rr_ratio, 2),
            "resistance_levels": resistance_levels.tolist(),
            "last_close": last_close,
            "ema_50": round(ema_50.iloc[-1], 2)
        }

    except Exception as e:
        print(f"Analysis error: {str(e)}")
        return None
