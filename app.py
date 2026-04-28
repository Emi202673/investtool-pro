from flask import Flask, render_template, request, redirect, session
import yfinance as yf
import ta
import threading
import time

app = Flask(__name__)
app.secret_key = "chiave_segreta_super_sicura"

# 🔐 login base
USERNAME = "admin"
PASSWORD = "admin123"

# 📊 asset monitorati
ASSETS = ["AAPL", "MSFT", "TSLA", "AMZN", "BTC-USD", "ETH-USD"]

# 💰 simulazione capitale hedge fund
capital = 10000
history = []
cache = []


# 🧠 funzione di analisi e decisione
def analyze_asset(asset):
    df = yf.download(asset, period="6mo")

    if df.empty:
        return None

    df["RSI"] = ta.momentum.RSIIndicator(df["Close"]).rsi()
    last = df.iloc[-1]

    rsi = last["RSI"]
    price = round(last["Close"], 2)

    # 🎯 logica decisionale (semplice ma efficace)
    if rsi < 30:
        decision = "BUY"
        score = 2
    elif rsi > 70:
        decision = "SELL"
        score = -1
    else:
        decision = "HOLD"
        score = 0

    return {
        "asset": asset,
        "price": price,
        "rsi": round(rsi, 2),
        "decision": decision,
        "score": score
    }


# 💰 simulazione hedge fund
def simulate_trade(asset, decision, price):
    global capital

    if decision == "BUY":
        capital *= 1.01
    elif decision == "SELL":
        capital *= 0.99

    history.append({
        "asset": asset,
        "decision": decision,
        "price": price,
        "capital": round(capital, 2)
    })


# 🔁 loop continuo (aggiornamento ogni 5 min)
def loop():
    global cache

    while True:
        results = []

        for a in ASSETS:
            data = analyze_asset(a)

            if data:
                simulate_trade(data["asset"], data["decision"], data["price"])
                results.append(data)

        cache = results
        time.sleep(300)


# 🌐 login
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["user"] == USERNAME and request.form["pwd"] == PASSWORD:
            session["logged"] = True
            return redirect("/dashboard")

    return render_template("login.html")


# 📊 dashboard
@app.route("/dashboard")
def dashboard():
    if not session.get("logged"):
        return redirect("/")

    return render_template(
        "dashboard.html",
        data=cache,
        capital=round(capital, 2),
        history=history[-20:]  # ultimi 20 movimenti
    )


# 🚀 avvio sistema
if __name__ == "__main__":
    threading.Thread(target=loop).start()
    app.run(host="0.0.0.0", port=5000)
