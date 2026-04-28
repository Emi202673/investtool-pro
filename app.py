from flask import Flask, render_template, request, redirect, session
import yfinance as yf
import pandas as pd
import numpy as np
import threading
import time

from sklearn.ensemble import RandomForestClassifier

app = Flask(__name__)
app.secret_key = "chiave_segreta"

USERNAME = "admin"
PASSWORD = "admin123"

ASSETS = ["AAPL", "MSFT", "TSLA", "AMZN", "BTC-USD", "ETH-USD"]

capital = 10000
history = []
cache = []


# 🧠 creazione dataset per AI
def build_dataset(df):
    df = df.copy()
    df["return"] = df["Close"].pct_change()
    df["ma5"] = df["Close"].rolling(5).mean()
    df["ma20"] = df["Close"].rolling(20).mean()
    df["rsi"] = 50  # semplificazione stabile

    df = df.dropna()

    df["target"] = np.where(df["Close"].shift(-1) > df["Close"], 1, 0)

    features = df[["return", "ma5", "ma20", "rsi"]]
    target = df["target"]

    return features, target


# 🤖 modello AI
def train_model(df):
    X, y = build_dataset(df)

    if len(X) < 50:
        return None

    model = RandomForestClassifier(n_estimators=50)
    model.fit(X, y)

    return model


# 📊 analisi asset
def analyze(asset):
    df = yf.download(asset, period="6mo")

    if df.empty or len(df) < 50:
        return None

    model = train_model(df)

    if model is None:
        return None

    last = df.iloc[-1]

    row = pd.DataFrame([{
        "return": df["Close"].pct_change().iloc[-1],
        "ma5": df["Close"].rolling(5).mean().iloc[-1],
        "ma20": df["Close"].rolling(20).mean().iloc[-1],
        "rsi": 50
    }])

    prob = model.predict_proba(row)[0][1]

    price = round(last["Close"], 2)

    if prob > 0.6:
        decision = "BUY"
    elif prob < 0.4:
        decision = "SELL"
    else:
        decision = "HOLD"

    return {
        "asset": asset,
        "price": price,
        "prob": round(prob, 2),
        "decision": decision
    }


# 💰 simulazione capitale
def simulate(decision):
    global capital

    if decision == "BUY":
        capital *= 1.01
    elif decision == "SELL":
        capital *= 0.99


# 🔁 loop
def loop():
    global cache, history

    while True:
        results = []

        for a in ASSETS:
            data = analyze(a)

            if data:
                simulate(data["decision"])

                history.append({
                    "asset": data["asset"],
                    "decision": data["decision"],
                    "price": data["price"],
                    "capital": round(capital, 2)
                })

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
        history=history[-20:]
    )


if __name__ == "__main__":
    threading.Thread(target=loop).start()
    app.run(host="0.0.0.0", port=5000)
