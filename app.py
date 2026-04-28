from flask import Flask, render_template, request, redirect, session
import yfinance as yf
import pandas as pd
import ta

app = Flask(__name__)
app.secret_key = "tech_desk"

USERNAME = "admin"
PASSWORD = "admin123"

portfolio = {}

assets = ["AAPL", "TSLA", "MSFT", "AMZN", "NVDA"]


# 🧠 indicatori tecnici
def compute_indicators(df):
    df["rsi"] = ta.momentum.RSIIndicator(df["Close"]).rsi()
    macd = ta.trend.MACD(df["Close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    return df


# 📊 segnale
def signal(rsi, macd, macd_signal):
    if rsi < 30 and macd > macd_signal:
        return "BUY"
    elif rsi > 70 and macd < macd_signal:
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


# 📊 DASHBOARD TECNICO
@app.route("/dashboard")
def dashboard():
    if not session.get("ok"):
        return redirect("/")

    signals = []

    for a in assets:

        df = yf.download(a, period="3mo", interval="1d")
        df = compute_indicators(df)

        latest = df.iloc[-1]

        sig = signal(
            latest["rsi"],
            latest["macd"],
            latest["macd_signal"]
        )

        signals.append({
            "asset": a,
            "price": round(latest["Close"], 2),
            "rsi": round(latest["rsi"], 2),
            "macd": round(latest["macd"], 2),
            "signal": sig
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
