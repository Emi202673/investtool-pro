from flask import Flask, render_template, request, redirect, session
import yfinance as yf
import pandas as pd
import numpy as np
import threading
import time
from sklearn.ensemble import RandomForestClassifier

app = Flask(__name__)
app.secret_key = "chiave_trading_desk"

# 🔐 login semplice
USERNAME = "admin"
PASSWORD = "admin123"

# 📊 asset
ASSETS = ["AAPL", "MSFT", "TSLA", "AMZN", "BTC-USD", "ETH-USD"]

# 💰 stato sistema
capitale = 10000
storico = []
cache = []
equity_curve = []


# 📊 features ML
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


# 🤖 modello
def train_model(df):
    X, y = build_features(df)

    if len(X) < 100:
        return None

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=8,
        random_state=42
    )

    model.fit(X, y)

    return model


# 📈 analisi asset
def analyze(asset):
    try:
        df = yf.download(asset, period="1y")

        if df is None or df.empty or len(df) < 100:
            return None

        model = train_model(df)
        if model is None:
            return None

        last = df.iloc[-1]

        X_live = pd.DataFrame([{
            "return": df["Close"].pct_change().iloc[-1],
            "volatility": df["Close"].pct_change().rolling(10).std().iloc[-1],
            "ma10": df["Close"].rolling(10).mean().iloc[-1],
            "ma30": df["Close"].rolling(30).mean().iloc[-1]
        }])

        prob = model.predict_proba(X_live)[0][1]
        price = float(last["Close"])

        if prob > 0.70:
            signal = "ACQUISTA"
            weight = 0.02
        elif prob < 0.30:
            signal = "VENDI"
            weight = -0.02
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

    except:
        return None


# 💰 esecuzione simulata
def execute(weight):
    global capitale

    pnl = capitale * weight
    capitale += pnl

    equity_curve.append(capitale)


# ⚠️ rischio
def var():
    if len(equity_curve) < 10:
        return 0
    returns = np.diff(equity_curve) / equity_curve[:-1]
    return np.percentile(returns, 5) * capitale


def sharpe():
    if len(equity_curve) < 2:
        return 0
    returns = np.diff(equity_curve) / equity_curve[:-1]
    if np.std(returns) == 0:
        return 0
    return np.mean(returns) / np.std(returns)


def volatility():
    if len(equity_curve) < 2:
        return 0
    returns = np.diff(equity_curve) / equity_curve[:-1]
    return np.std(returns)


# 🔁 loop trading
def loop():
    global cache, storico

    while True:
        results = []

        for a in ASSETS:
            data = analyze(a)

            if data:
                execute(data["peso"])

                storico.append({
                    "asset": data["asset"],
                    "segnale": data["segnale"],
                    "prezzo": data["prezzo"],
                    "capitale": round(capitale, 2)
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


# 📊 dashboard (QUESTA È LA PARTE CHE TI MANCAVA)
@app.route("/dashboard")
def dashboard():
    if not session.get("ok"):
        return redirect("/")

    return render_template(
        "dashboard.html",
        data=cache if cache else [],
        capitale=round(capitale, 2),
        storico=storico[-50:] if storico else [],
        var=round(var(), 4),
        sharpe=round(sharpe(), 4),
        rischio=round(volatility(), 4)
    )


# 🚀 avvio
if __name__ == "__main__":
    t = threading.Thread(target=loop)
    t.daemon = True
    t.start()

    app.run(host="0.0.0.0", port=5000)
