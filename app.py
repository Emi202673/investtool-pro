from flask import Flask, render_template, request, redirect, session
import random

app = Flask(__name__)
app.secret_key = "signal_desk"

USERNAME = "admin"
PASSWORD = "admin123"

# 💼 portafoglio utente
portfolio = {}

# 📊 universi titoli
assets = ["AAPL", "TSLA", "MSFT", "AMZN", "NVDA", "BTC", "ETH"]


# 🧠 generatore segnali (momentum + mean reversion semplificato)
def generate_signal(price_change, volatility):
    score = price_change / (volatility + 1e-6)

    if score > 1:
        return "BUY"
    elif score < -1:
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


# 📊 DASHBOARD OPERATIVA
@app.route("/dashboard")
def dashboard():
    if not session.get("ok"):
        return redirect("/")

    signals = []
    recommendations = []

    for a in assets:

        price = random.uniform(50, 600)

        # simulazione variazione prezzo
        price_change = random.gauss(0, 2)
        volatility = random.uniform(0.5, 3)

        signal = generate_signal(price_change, volatility)

        signals.append({
            "asset": a,
            "price": round(price, 2),
            "change": round(price_change, 2),
            "vol": round(volatility, 2),
            "signal": signal
        })

        # 🧠 logica operativa consigliata
        if signal == "BUY":
            recommendations.append(f"📈 BUY {a}")
        elif signal == "SELL":
            recommendations.append(f"📉 SELL {a}")

    return render_template(
        "dashboard.html",
        signals=signals,
        portfolio=portfolio,
        recommendations=recommendations
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
