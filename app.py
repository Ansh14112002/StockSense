import os
import time
import json
import yfinance as yf

from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy

from utils.news_fetcher import fetch_news
from utils.sentiment_analyzer import analyze_sentiment
from model import db, Stock
from models.model_utils import fetch_stock_data, engineer_features

# === Flask / DB Setup ===
app = Flask(__name__, instance_relative_config=True)
os.makedirs(app.instance_path, exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'portfolio.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# === INDEX CACHE ===
# Simple in-memory cache: stores last fetch timestamp and data
index_cache = {
    'timestamp': 0,
    'data': None
}
CACHE_INTERVAL = 60  # seconds

# Tickers for indices
INDICES = {
    'Sensex': '^BSESN',
    'Nifty': '^NSEI',
    'DJIA': '^DJI',
    'Nasdaq': '^IXIC'
}

def fetch_indices():
    """
    Fetch current value and percent change for each index. Cache results for CACHE_INTERVAL.
    Also fetch intraday history for Sensex (for chart).
    Returns a dict:
      {
        'indices': {
           'Sensex': {'current': 61000.23, 'previous_close': 60500.12, 'change_pct': 0.827},
           'Nifty': { … },
           …
        },
        'sensex_history': [
           {'time': '09:15', 'value': 60200.11}, …  # list of dicts for intraday
        ],
        'timestamp': 1671234567
      }
    """
    global index_cache
    now = time.time()
    if index_cache['data'] and (now - index_cache['timestamp'] < CACHE_INTERVAL):
        return index_cache['data']

    # Fetch fresh data
    indices_data = {}
    for name, ticker_sym in INDICES.items():
        try:
            ticker = yf.Ticker(ticker_sym)
            # Use info dict for current price and previous close
            info = ticker.info
            current = info.get('regularMarketPrice')
            prev_close = info.get('regularMarketPreviousClose')
            if current is None or prev_close is None:
                # Fallback: fetch via history
                hist = ticker.history(period='2d', interval='1d', auto_adjust=True)
                if len(hist) >= 2:
                    prev_close = hist['Close'][-2]
                    current = hist['Close'][-1]
                elif len(hist) == 1:
                    prev_close = hist['Close'][-1]
                    current = hist['Close'][-1]
                else:
                    prev_close = current = None
            change_pct = round(((current - prev_close) / prev_close) * 100, 2) if (current and prev_close and prev_close != 0) else None
            indices_data[name] = {
                'ticker': ticker_sym,
                'current': round(current, 2) if current is not None else None,
                'previous_close': round(prev_close, 2) if prev_close is not None else None,
                'change_pct': change_pct
            }
        except Exception as e:
            indices_data[name] = {
                'ticker': ticker_sym,
                'current': None,
                'previous_close': None,
                'change_pct': None
            }

    # For Sensex intraday chart: fetch today's 1-minute history
    sensex_hist = []
    try:
        sx = yf.Ticker(INDICES['Sensex'])
        df = sx.history(period='1d', interval='1m', auto_adjust=True)
        # df index is a DatetimeIndex—extract time and close
        for timestamp, row in df.iterrows():
            time_label = timestamp.strftime('%H:%M')
            sensex_hist.append({
                'time': time_label,
                'value': round(row['Close'], 2)
            })
    except Exception:
        sensex_hist = []

    payload = {
        'indices': indices_data,
        'sensex_history': sensex_hist,
        'timestamp': now
    }
    index_cache['data'] = payload
    index_cache['timestamp'] = now
    return payload

# === HOME / INDEX PAGE ===
@app.route('/')
def index():
    return render_template('index.html')

# === LIVE DATA API ===
@app.route('/live_data')
def live_data():
    payload = fetch_indices()
    return jsonify(payload)

# === NEWS SENTIMENT ===
@app.route('/analyze', methods=['POST'])
def analyze():
    stock_symbol = request.form['symbol'].upper()
    headlines = fetch_news(stock_symbol)

    if not headlines:
        return render_template(
            'news.html',
            symbol=stock_symbol,
            results=[],
            final_sentiment="No headlines found or API limit reached."
        )

    results, final_sentiment = analyze_sentiment(headlines)
    return render_template(
        'news.html',
        symbol=stock_symbol,
        results=results,
        final_sentiment=final_sentiment
    )

# === PORTFOLIO ===
@app.route('/portfolio')
def portfolio():
    stocks = Stock.query.all()
    fx_rate = None
    try:
        fx = yf.Ticker("USDINR=X")
        hist = fx.history(period="1d", interval="1d", auto_adjust=True)
        if not hist.empty:
            fx_rate = hist['Close'].iloc[-1]
    except Exception:
        fx_rate = None

    for stock in stocks:
        is_indian = stock.symbol.upper().endswith(".NS")
        current_price_native = stock.current_price()

        if is_indian:
            stock.current_currency = "INR"
            stock.current_price_display = f"₹{current_price_native:.2f}"
            stock.buy_price_display = f"₹{stock.buy_price:.2f}"

            stock.current_price_in_inr = current_price_native
            stock.buy_price_in_inr = stock.buy_price

            inv_inr = stock.buy_price * stock.quantity
            curr_val_inr = current_price_native * stock.quantity
            stock.gain_loss_inr = round(curr_val_inr - inv_inr, 2)
            stock.gain_loss_percent = round(((curr_val_inr - inv_inr) / inv_inr) * 100, 2) if inv_inr else 0

            stock.current_value_display = f"₹{curr_val_inr:.2f}"
            stock.gain_loss_display = f"₹{stock.gain_loss_inr:.2f}"
            stock.gain_loss_percent_display = f"{stock.gain_loss_percent:.2f}%"

            stock.current_price_usd = None
            stock.buy_price_usd = None
            stock.current_value_usd = None
            stock.gain_loss_usd = None
            stock.current_value_inr_display = None
            stock.gain_loss_usd_display = None

        else:
            stock.current_currency = "USD"
            stock.current_price_display = f"${current_price_native:.2f}"
            stock.buy_price_display = f"${stock.buy_price:.2f}"

            inv_usd = stock.buy_price * stock.quantity
            curr_val_usd = current_price_native * stock.quantity
            stock.gain_loss_usd = round(curr_val_usd - inv_usd, 2)
            stock.gain_loss_percent = round(((curr_val_usd - inv_usd) / inv_usd) * 100, 2) if inv_usd else 0

            stock.current_value_display = f"${curr_val_usd:.2f}"
            stock.gain_loss_display = f"${stock.gain_loss_usd:.2f}"
            stock.gain_loss_percent_display = f"{stock.gain_loss_percent:.2f}%"

            if fx_rate:
                stock.current_price_in_inr = round(current_price_native * fx_rate, 2)
                stock.buy_price_in_inr = round(stock.buy_price * fx_rate, 2)
                stock.current_value_inr = round(curr_val_usd * fx_rate, 2)
                stock.gain_loss_inr = round(stock.gain_loss_usd * fx_rate, 2)

                stock.current_value_inr_display = f"₹{stock.current_value_inr:.2f}"
                stock.gain_loss_inr_display = f"₹{stock.gain_loss_inr:.2f}"
            else:
                stock.current_price_in_inr = None
                stock.buy_price_in_inr = None
                stock.current_value_inr = None
                stock.gain_loss_inr = None
                stock.current_value_inr_display = None
                stock.gain_loss_inr_display = None

    total_value_inr = 0.0
    total_gain_loss_inr = 0.0
    for stock in stocks:
        if stock.current_price_in_inr is not None:
            total_value_inr += stock.quantity * stock.current_price_in_inr
            total_gain_loss_inr += stock.gain_loss_inr if stock.gain_loss_inr is not None else 0.0

    return render_template(
        'portfolio.html',
        stocks=stocks,
        total_value_inr=round(total_value_inr, 2),
        total_gain_loss_inr=round(total_gain_loss_inr, 2)
    )

# === ADD STOCK ===
@app.route('/add_stock', methods=['POST'])
def add_stock():
    symbol = request.form['symbol'].upper()
    quantity = float(request.form['quantity'])
    buy_price = float(request.form['buy_price'])
    new_stock = Stock(symbol=symbol, quantity=quantity, buy_price=buy_price)
    db.session.add(new_stock)
    db.session.commit()
    return redirect(url_for('portfolio'))

# === DELETE STOCK ===
@app.route('/delete_stock/<int:id>')
def delete_stock(id):
    stock = Stock.query.get_or_404(id)
    db.session.delete(stock)
    db.session.commit()
    return redirect(url_for('portfolio'))

# === EDIT STOCK ===
@app.route('/edit_stock/<int:id>', methods=['GET', 'POST'])
def edit_stock(id):
    stock = Stock.query.get_or_404(id)
    if request.method == 'POST':
        stock.symbol = request.form['symbol'].upper()
        stock.quantity = float(request.form['quantity'])
        stock.buy_price = float(request.form['buy_price'])
        db.session.commit()
        return redirect(url_for('portfolio'))
    return render_template('edit.html', stock=stock)

# === FORECAST ===
@app.route('/forecast', methods=['GET', 'POST'])
def forecast():
    if request.method == 'POST':
        symbol = request.form['symbol'].upper()
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period='30d', interval='1d', auto_adjust=True)
            if df.empty:
                raise ValueError("No historical data returned.")

            dates = df.index.strftime('%Y-%m-%d').tolist()
            prices = df['Close'].round(2).tolist()
            trend = "Uptrend 📈" if prices[-1] > prices[0] else "Downtrend 📉"
            chart_data = {'dates': dates, 'prices': prices}

            return render_template(
                'forecast.html',
                symbol=symbol,
                trend=trend,
                chart_data=json.dumps(chart_data)
            )
        except Exception as e:
            print(f"[ERROR] Forecast error for {symbol}: {e}")
            return render_template(
                'forecast.html',
                symbol=symbol,
                trend="Error fetching data.",
                chart_data=None
            )
    return render_template('forecast.html', symbol=None, trend=None, chart_data=None)

# === LEARN ===
@app.route('/learn')
def learn():
    return render_template('learn.html')

# === RUN APP ===
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
