from flask import Flask, render_template, request, redirect, session
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = "hedge_fund_v2"

# 👤 login
USERNAME = "admin"
PASSWORD = "admin123"

# 💰 capitale iniziale
capital = 10000

# 📊 storico trade
trades = []

# 📈 equity curve
equity_curve = []


# 🌐 LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("user")
        pwd = request.form.get("pwd")

        if user == USERNAME and pwd == PASSWORD:
            session["ok"] = True
            return redirect("/dashboard")

    return render_template("login.html")


# 📊 DASHBOARD
@app.route("/dashboard")
def dashboard():
    if not session.get("ok"):
        return redirect("/")

    assets = ["AAPL", "TSLA", "MSFT", "AMZN", "BTC", "ETH"]

    data = []

    for a in assets:
        price = round(random.uniform(50, 600), 2)

        # 🧠 pseudo-segnale quant
        score = random.uniform(-1, 1)
        if score > 0.3:
            signal = "BUY"
        elif score < -0.3:
            signal = "SELL"
        else:
            signal = "HOLD"

        data.append({
            "asset": a,
            "price": price,
            "signal": signal,
            "score": round(score, 2)
        })

    return render_template(
        "dashboard.html",
        data=data,
        capital=capital,
        trades=trades[-10:],
        equity=equity_curve[-20:]
    )


# 🟢 BUY
@app.route("/buy", methods=["POST"])
def buy():
    global capital

    asset = request.form.get("asset")
    pnl = capital * 0.01

    capital += pnl

    trades.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "type": "BUY",
        "asset": asset,
        "pnl": round(pnl, 2)
    })

    equity_curve.append(capital)

    return redirect("/dashboard")


# 🔴 SELL
@app.route("/sell", methods=["POST"])
def sell():
    global capital

    asset = request.form.get("asset")
    pnl = capital * 0.01

    capital -= pnl

    trades.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "type": "SELL",
        "asset": asset,
        "pnl": round(-pnl, 2)
    })

    equity_curve.append(capital)

    return redirect("/dashboard")


# 🚀 RUN
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
