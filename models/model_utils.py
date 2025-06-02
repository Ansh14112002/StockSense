import yfinance as yf
import pandas as pd
import numpy as np
from ta.trend import SMAIndicator, EMAIndicator, MACD
from ta.momentum import RSIIndicator

def fetch_stock_data(symbol, period='180d', interval='1d'):
    """
    Fetch historical daily data for `symbol` over the past `period`.
    auto_adjust=True adjusts for splits/dividends.
    """
    data = yf.download(symbol, period=period, interval=interval, auto_adjust=True)
    data.dropna(inplace=True)
    return data

def engineer_features(data):
    """
    Compute SMA, EMA, RSI, MACD on `data['Close']`.
    Require at least 15 rows to compute a 14-day SMA/EMA/RSI.
    Return an empty DataFrame if data is too short or indicators fail.
    """
    if data is None or data.empty or len(data) < 15:
        # Must have at least 15 rows (14-day lookback + 1)
        return pd.DataFrame()

    # Ensure we’re working with a 1D Series
    close_prices = data['Close']
    if isinstance(close_prices, pd.DataFrame):
        close_prices = close_prices.squeeze()

    try:
        data['SMA'] = SMAIndicator(close=close_prices, window=14).sma_indicator()
        data['EMA'] = EMAIndicator(close=close_prices, window=14).ema_indicator()
        data['RSI'] = RSIIndicator(close=close_prices, window=14).rsi()
        macd = MACD(close=close_prices)
        data['MACD'] = macd.macd()
    except Exception as e:
        print(f"[ERROR] Indicator calculation failure: {e}")
        return pd.DataFrame()

    # Drop any rows where indicators are NaN (first 14 rows)
    data.dropna(inplace=True)
    return data

def label_target(data):
    """
    Create a binary 'Target' column: 1 if next day's close > today's close, else 0.
    Drop last row (no next-day close).
    """
    data['Target'] = np.where(data['Close'].shift(-1) > data['Close'], 1, 0)
    data.dropna(inplace=True)
    return data

def get_features_and_labels(data):
    """
    Split into feature matrix X and labels y.
    Features: ['SMA', 'EMA', 'RSI', 'MACD']
    Labels:   ['Target']
    """
    features = data[['SMA', 'EMA', 'RSI', 'MACD']]
    labels = data['Target']
    return features, labels
