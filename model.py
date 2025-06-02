from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Stock(db.Model):
    __tablename__ = 'stock'
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    buy_price = db.Column(db.Float, nullable=False)##

    def current_price(self):
        import yfinance as yf
        try:
            ticker = yf.Ticker(self.symbol)
            data = ticker.history(period="1d")
            return round(data['Close'].iloc[-1], 2) if not data.empty else 0.0
        except Exception as e:
            print(f"Error fetching price for {self.symbol}: {e}")
            return 0.0

    def gain_loss(self):
        current = self.current_price()
        return round((current - self.buy_price) * self.quantity, 2)

    def gain_loss_percent(self):
        current = self.current_price()
        if self.buy_price == 0:
            return 0.0
        return round(((current - self.buy_price) / self.buy_price) * 100, 2)
