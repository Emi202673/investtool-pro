from flask import Flask, render_template, request, redirect, session
import yfinance as yf
import ta
import threading
import time

app = Flask(__name__)
app.secret_key = "chiave_segreta"

USERNAME = "admin"
PASSWORD = "admin123"

ASSETS = ["AAPL","MSFT","TSLA","AMZN","BTC-USD","ETH-USD"]

cache = []

def analyze():
    global cache
    results = []

    for a in ASSETS:
        df = yf.download(a, period="6mo")

        if df.empty:
            continue

        df["RSI"] = ta.momentum.RSIIndicator(df["Close"]).rsi()
        last = df.iloc[-1]

        score = 0

        if last["RSI"] < 30:
            score += 2
        elif last["RSI"] < 70:
            score += 1
        else:
            score -= 1

        ma50 = df["Close"].rolling(50).mean().iloc[-1]

        if last["Close"] > ma50:
            score += 1

        if score >= 2:
            decision = "BUY"
        elif score <= 0:
            decision = "SELL"
        else:
            decision = "HOLD"

        results.append({
            "asset": a,
            "price": round(last["Close"],2),
            "rsi": round(last["RSI"],2),
            "decision": decision
        })

    cache = results


def loop():
    while True:
        analyze()
        time.sleep(300)


@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        if request.form["user"] == USERNAME and request.form["pwd"] == PASSWORD:
            session["logged"] = True
            return redirect("/dashboard")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if not session.get("logged"):
        return redirect("/")

    return render_template("dashboard.html", data=cache)


if __name__ == "__main__":
    threading.Thread(target=loop).start()
    app.run(host="0.0.0.0", port=5000)
