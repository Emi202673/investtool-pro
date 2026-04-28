from flask import Flask, render_template, request, redirect, session
import yfinance as yf
import pandas as pd
import numpy as np
import threading
import time

from sklearn.ensemble import RandomForestClassifier

app = Flask(__name__)
app.secret_key = "hedge_fund_key"

USERNAME = "admin"
PASSWORD = "admin123"

ASSETS = ["AAPL", "MSFT", "TSLA", "AMZN", "BTC-USD", "ETH-USD"]

capital = 10000
history = []
cache = []
equity_curve = []


# 📊 feature engineering avanzata
def features(df):
    df = df.copy()

    df["return"] = df["Close"].pct_change()
    df["volatility"] = df["return"].rolling(10).std()
    df["ma10"] = df["Close"].rolling(10).mean()
    df["ma30"] = df["Close"].rolling(30).mean()

    df = df.dropna()

    df["target"] = np.where(df["Close"].shift(-1) > df["Close"], 1, 0)

    X = df[["return", "volatility", "ma10", "ma30"]]
    y = df["target"]

    return X, y


# 🤖 modello ML
def train(df):
    X, y = features(df)

    if len(X) < 80:
        return None

    model = RandomForestClassifier(
        n_estimators=150,
        max_depth=7,
        random_state=42
    )

    model.fit(X, y)

    return model


# 📈 analisi asset
def analyze(asset):
    df = yf.download(asset, period="1y")

    if df.empty or len(df) < 100:
        return None

    model = train(df)

    if model is None:
        return None

    last = df.iloc[-1]

    row = pd.DataFrame([{
        "return": df["Close"].pct_change().iloc[-1],
        "volatility": df["Close"].pct_change().rolling(10).std().iloc[-1],
        "ma10": df["Close"].rolling(10).mean().iloc[-1],
        "ma30": df["Close"].rolling(30).mean().iloc[-1]
    }])

    prob = model.predict_proba(row)[0][1]

    price = float(last["Close"])

    if prob > 0.65:
        signal = "BUY"
    elif prob < 0.35:
        signal = "SELL"
    else:
        signal = "HOLD"

    return {
        "asset": asset,
        "price": round(price, 2),
        "prob": round(prob, 2),
        "signal": signal
    }


# ⚖️ portfolio allocation (semi-Markowitz semplificato)
def allocate(signal):
    global capital

    weight = 0.01  # rischio controllato

    if signal == "BUY":
        capital += capital * weight
    elif signal == "SELL":
        capital -= capital * weight

    equity_curve.append(capital)


# ⚠️ Value at Risk (VaR semplificato)
def var():
    if len(equity_curve) < 20:
        return 0

    returns = np.diff(equity_curve) / equity_curve[:-1]

    return np.percentile(returns, 5) * capital


# 📉 Sharpe ratio
def sharpe():
    if len(equity_curve) < 2:
        return 0

    returns = np.diff(equity_curve) / equity_curve[:-1]

    if np.std(returns) == 0:
        return 0

    return np.mean(returns) / np.std(returns)


# 🔁 loop hedge fund
def loop():
    global cache, history

    while True:
        results = []

        for a in ASSETS:
            data = analyze(a)

            if data:
                allocate(data["signal"])

                history.append({
                    "asset": data["asset"],
                    "signal": data["signal"],
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


# 📊 dashboard hedge fund
@app.route("/dashboard")
def dashboard():
    if not session.get("logged"):
        return redirect("/")

    return render_template(
        "dashboard.html",
        data=cache,
        capital=round(capital, 2),
        history=history[-30:],
        sharpe=round(sharpe(), 3),
        var=round(var(), 3)
    )


if __name__ == "__main__":
    threading.Thread(target=loop).start()
    app.run(host="0.0.0.0", port=5000)
