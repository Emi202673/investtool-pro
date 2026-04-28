from flask import Flask, render_template, request, redirect, session
import yfinance as yf
import pandas as pd
import numpy as np
import threading
import time

from sklearn.ensemble import RandomForestClassifier

app = Flask(__name__)
app.secret_key = "trading_desk_pro"

USERNAME = "admin"
PASSWORD = "admin123"

ASSETS = ["AAPL", "MSFT", "TSLA", "AMZN", "BTC-USD", "ETH-USD"]

# 💰 capitale
capitale_iniziale = 10000
capitale = capitale_iniziale

storico = []
cache = []
equity_curve = []
pnl_giornaliero = []


# 📊 feature engine
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


# 🤖 modello trading desk
def train(df):
    X, y = features(df)

    if len(X) < 120:
        return None

    model = RandomForestClassifier(
        n_estimators=250,
        max_depth=10,
        random_state=42
    )

    model.fit(X, y)

    return model


# 📈 analisi asset
def analyze(asset):
    df = yf.download(asset, period="1y")

    if df.empty or len(df) < 150:
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

    if prob > 0.72:
        signal = "BUY"
        weight = 0.03
    elif prob < 0.28:
        signal = "SELL"
        weight = -0.03
    else:
        signal = "HOLD"
        weight = 0

    return {
        "asset": asset,
        "price": round(price, 2),
        "prob": round(prob, 2),
        "signal": signal,
        "weight": weight
    }


# 💼 motore portafoglio desk
def execute(weight):
    global capitale

    pnl = capitale * weight
    capitale += pnl

    equity_curve.append(capitale)
    pnl_giornaliero.append(pnl)


# ⚠️ VAR (rischio istituzionale)
def var():
    if len(equity_curve) < 20:
        return 0

    returns = np.diff(equity_curve) / equity_curve[:-1]
    return np.percentile(returns, 5) * capitale


# 📊 volatilità desk
def volatility():
    if len(equity_curve) < 2:
        return 0

    returns = np.diff(equity_curve) / equity_curve[:-1]
    return np.std(returns)


# 📈 Sharpe ratio
def sharpe():
    if len(equity_curve) < 2:
        return 0

    returns = np.diff(equity_curve) / equity_curve[:-1]

    if np.std(returns) == 0:
        return 0

    return np.mean(returns) / np.std(returns)


# 📉 PnL giornaliero medio
def pnl_media():
    if not pnl_giornaliero:
        return 0
    return np.mean(pnl_giornaliero)


# 🔁 LOOP TRADING DESK
def loop():
    global cache, storico

    while True:
        results = []

        for a in ASSETS:
            data = analyze(a)

            if data:
                execute(data["weight"])

                storico.append({
                    "asset": data["asset"],
                    "signal": data["signal"],
                    "price": data["price"],
                    "capital": round(capitale, 2)
                })

                results.append(data)

        cache = results
        time.sleep(60)


# 🌐 login
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["user"] == USERNAME and request.form["pwd"] == PASSWORD:
            session["ok"] = True
            return redirect("/dashboard")

    return render_template("login.html")


# 🏦 DASHBOARD TRADING DESK
@app.route("/dashboard")
def dashboard():
    if not session.get("ok"):
        return redirect("/")

    return render_template(
        "dashboard.html",
        data=cache,
        capitale=round(capitale, 2),
        storico=storico[-60:],
        var=round(var(), 3),
        sharpe=round(sharpe(), 3),
        volatility=round(volatility(), 4),
        pnl=round(pnl_media(), 2)
    )


if __name__ == "__main__":
    threading.Thread(target=loop).start()
    app.run(host="0.0.0.0", port=5000)
