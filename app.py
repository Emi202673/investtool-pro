from flask import Flask, render_template, request, redirect, session
import random
from datetime import datetime
import math

app = Flask(__name__)
app.secret_key = "quant_v3"

USERNAME = "admin"
PASSWORD = "admin123"

capital = 10000
trades = []
equity = []


# 📊 metriche
def sharpe():
    if len(equity) < 2:
        return 0
    returns = [equity[i] - equity[i-1] for i in range(1, len(equity))]
    mean = sum(returns) / len(returns)
    std = math.sqrt(sum((x - mean) ** 2 for x in returns) / len(returns))
    return round(mean / std, 2) if std != 0 else 0


# 🌐 LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("user") == USERNAME and request.form.get("pwd") == PASSWORD:
            session["ok"] = True
            return redirect("/dashboard")
    return render_template("login.html")


# 📊 DASHBOARD QUANT
@app.route("/dashboard")
def dashboard():
    if not session.get("ok"):
        return redirect("/")

    assets = ["AAPL", "TSLA", "MSFT", "AMZN", "BTC", "ETH"]

    data = []

    for a in assets:
        price = round(random.uniform(50, 600), 2)

        # 🧠 signal model (z-score fake quant)
        z = random.gauss(0, 1)

        if z > 0.8:
            signal = "LONG"
            exposure = 0.02
        elif z < -0.8:
            signal = "SHORT"
            exposure = -0.02
        else:
            signal = "NEUTRAL"
            exposure = 0

        data.append({
            "asset": a,
            "price": price,
            "z": round(z, 2),
            "signal": signal,
            "exposure": exposure
        })

    return render_template(
        "dashboard.html",
        data=data,
        capital=capital,
        trades=trades[-15:],
        equity=equity[-30:],
        sharpe=sharpe()
    )


# 🟢 BUY (LONG)
@app.route("/buy", methods=["POST"])
def buy():
    global capital

    asset = request.form.get("asset")
    pnl = capital * 0.01

    capital += pnl
    equity.append(capital)

    trades.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "asset": asset,
        "type": "LONG",
        "pnl": round(pnl, 2)
    })

    return redirect("/dashboard")


# 🔴 SELL (SHORT)
@app.route("/sell", methods=["POST"])
def sell():
    global capital

    asset = request.form.get("asset")
    pnl = capital * 0.01

    capital -= pnl
    equity.append(capital)

    trades.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "asset": asset,
        "type": "SHORT",
        "pnl": round(-pnl, 2)
    })

    return redirect("/dashboard")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
