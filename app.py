from flask import Flask, render_template, request, redirect, session
import yfinance as yf
import pandas as pd
import numpy as np
import threading
import time

from sklearn.ensemble import RandomForestClassifier

app = Flask(__name__)
app.secret_key = "quant_fund_final"

USERNAME = "admin"
PASSWORD = "admin123"

ASSETS = ["AAPL", "MSFT", "TSLA", "AMZN", "BTC-USD", "ETH-USD"]

# 💰 capitale iniziale
capitale = 10000
storico = []
cache = []
equity_curve = []


# 📊 feature engineering avanzata
def build_features(df):
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


# 🤖 modello quant finale
def train_model(df):
    X, y = build_features(df)

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

    model = train_model(df)

    if model is None:
        return None

    last = df.iloc[-1]

    features = pd.DataFrame([{
        "return": df["Close"].pct_change().iloc[-1],
        "volatility": df["Close"].pct_change().rolling(10).std().iloc[-1],
        "ma10": df["Close"].rolling(10).mean().iloc[-1],
        "ma30": df["Close"].rolling(30).mean().iloc[-1]
    }])

    prob = model.predict_proba(features)[0][1]

    price = float(last["Close"])

    if prob > 0.70:
        signal = "ACQUISTA"
        weight = 0.03
    elif prob < 0.30:
        signal = "VENDI"
        weight = -0.03
    else:
        signal = "NEUTRO"
        weight = 0

    return {
        "asset": asset,
        "prezzo": round(price, 2),
        "probabilita": round(prob, 2),
        "segnale": signal,
        "peso": weight
    }


# ⚖️ portfolio risk parity semplificato
def portfolio_step(weight):
    global capitale

    capitale += capitale * weight
    equity_curve.append(capitale)


# 📊 correlazione (semplificata)
def correlation_risk():
    if len(equity_curve) < 20:
        return 0

    returns = np.diff(equity_curve) / equity_curve[:-1]
    return np.std(returns)


# ⚠️ Value at Risk (VaR)
def var():
    if len(equity_curve) < 20:
        return 0

    returns = np.diff(equity_curve) / equity_curve[:-1]
    return np.percentile(returns, 5) * capitale


# 📈 Sharpe ratio finale
def sharpe():
    if len(equity_curve) < 2:
        return 0

    returns = np.diff(equity_curve) / equity_curve[:-1]

    if np.std(returns) == 0:
        return 0

    return np.mean(returns) / np.std(returns)


# 🔁 loop hedge fund finale
def loop():
    global cache, storico

    while True:
        results = []

        for a in ASSETS:
            data = analyze(a)

            if data:
                portfolio_step(data["peso"])

                storico.append({
                    "asset": data["asset"],
                    "segnale": data["segnale"],
                    "prezzo": data["prezzo"],
                    "capitale": round(capitale, 2)
                })

                results.append(data)

        cache = results
        time.sleep(300)


# 🌐 login
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["user"] == USERNAME and request.form["pwd"] == PASSWORD:
            session["loggato"] = True
            return redirect("/dashboard")

    return render_template("login.html")


# 🏦 dashboard finale quant hedge fund
@app.route("/dashboard")
def dashboard():
    if not session.get("loggato"):
        return redirect("/")

    return render_template(
        "dashboard.html",
        data=cache,
        capitale=round(capitale, 2),
        storico=storico[-40:],
        sharpe=round(sharpe(), 3),
        var=round(var(), 3),
        rischio=round(correlation_risk(), 4)
    )


if __name__ == "__main__":
    threading.Thread(target=loop).start()
    app.run(host="0.0.0.0", port=5000)
