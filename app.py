from flask import Flask, render_template, request, redirect, session
import yfinance as yf

app = Flask(__name__)
app.secret_key = "real_market"

USERNAME = "admin"
PASSWORD = "admin123"

portfolio = {}

assets = ["AAPL", "TSLA", "MSFT", "AMZN", "NVDA", "BTC-USD", "ETH-USD"]


# 🧠 segnale semplice su prezzo reale
def signal_from_price_change(change):
    if change > 1.5:
        return "BUY"
    elif change < -1.5:
        return "SELL"
    else:
        return "HOLD"


# 🌐 LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("user") == USERNAME and request.form.get("pwd") == PASSWORD:
            session["ok"] = True
            return redirect("/dashboard")
    return render_template("login.html")


# 📊 DASHBOARD REAL MARKET
@app.route("/dashboard")
def dashboard():
    if not session.get("ok"):
        return redirect("/")

    signals = []

    for a in assets:

        ticker = yf.Ticker(a)
        data = ticker.history(period="2d")

        if len(data) < 2:
            continue

        close_today = data["Close"].iloc[-1]
        close_prev = data["Close"].iloc[-2]

        change = ((close_today - close_prev) / close_prev) * 100

        signal = signal_from_price_change(change)

        signals.append({
            "asset": a,
            "price": round(close_today, 2),
            "change": round(change, 2),
            "signal": signal
        })

    return render_template(
        "dashboard.html",
        signals=signals,
        portfolio=portfolio
    )


# 🟢 BUY
@app.route("/buy", methods=["POST"])
def buy():
    asset = request.form.get("asset")
    portfolio[asset] = portfolio.get(asset, 0) + 1
    return redirect("/dashboard")


# 🔴 SELL
@app.route("/sell", methods=["POST"])
def sell():
    asset = request.form.get("asset")
    if asset in portfolio:
        portfolio[asset] -= 1
        if portfolio[asset] <= 0:
            del portfolio[asset]
    return redirect("/dashboard")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
