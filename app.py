from flask import Flask, render_template, request, redirect, session
import random
import math
from datetime import datetime

app = Flask(__name__)
app.secret_key = "quant_institutional_v4"

USERNAME = "admin"
PASSWORD = "admin123"

capital = 10000
trades = []
equity = [capital]
returns = []


# 📊 metriche istituzionali
def volatility():
    if len(returns) < 2:
        return 0
    mean = sum(returns) / len(returns)
    var = sum((r - mean) ** 2 for r in returns) / len(returns)
    return round(math.sqrt(var), 4)


def var_95():
    if not returns:
        return 0
    sorted_r = sorted(returns)
    index = int(0.05 * len(sorted_r))
    return round(sorted_r[index], 4)


def sharpe():
    if len(returns) < 2:
        return 0
    mean = sum(returns) / len(returns)
    std = math.sqrt(sum((r - mean) ** 2 for r in returns) / len(returns))
    return round(mean / std, 2) if std != 0 else 0


# 🌐 LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("user") == USERNAME and request.form.get("pwd") == PASSWORD:
            session["ok"] = True
            return redirect("/dashboard")
    return render_template("login.html")


# 📊 DASHBOARD ISTITUZIONALE
@app.route("/dashboard")
def dashboard():
    if not session.get("ok"):
        return redirect("/")

    assets = ["AAPL", "TSLA", "MSFT", "AMZN", "BTC", "ETH"]

    data = []

    for a in assets:
        price = round(random.uniform(50, 600), 2)

        # 📉 log-return simulato
        r = random.gauss(0, 0.01)
        signal_score = r * 100

        if signal_score > 1:
            signal = "LONG"
            exposure = 0.02
        elif signal_score < -1:
            signal = "SHORT"
            exposure = -0.02
        else:
            signal = "NEUTRAL"
            exposure = 0

        data.append({
            "asset": a,
            "price": price,
            "return": round(r, 5),
            "signal": signal,
            "exposure": exposure
        })

    return render_template(
        "dashboard.html",
        data=data,
        capital=capital,
        equity=equity[-30:],
        trades=trades[-15:],
        vol=volatility(),
        var=var_95(),
        sharpe=sharpe()
    )


# 🟢 LONG
@app.route("/buy", methods=["POST"])
def buy():
    global capital

    asset = request.form.get("asset")

    r = random.gauss(0.001, 0.01)
    pnl = capital * r

    capital += pnl
    returns.append(r)
    equity.append(capital)

    trades.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "asset": asset,
        "type": "LONG",
        "pnl": round(pnl, 2)
    })

    return redirect("/dashboard")


# 🔴 SHORT
@app.route("/sell", methods=["POST"])
def sell():
    global capital

    asset = request.form.get("asset")

    r = random.gauss(-0.001, 0.01)
    pnl = capital * r

    capital += pnl
    returns.append(r)
    equity.append(capital)

    trades.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "asset": asset,
        "type": "SHORT",
        "pnl": round(pnl, 2)
    })

    return redirect("/dashboard")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
