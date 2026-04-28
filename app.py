from flask import Flask, render_template, request, redirect, session
import yfinance as yf
import pandas as pd
import numpy as np
import threading
import time

from sklearn.ensemble import RandomForestClassifier

app = Flask(__name__)
app.secret_key = "chiave_sistema_quant_italia"

# 🔐 login
USERNAME = "admin"
PASSWORD = "admin123"

# 📊 asset monitorati
ASSETS = ["AAPL", "MSFT", "TSLA", "AMZN", "BTC-USD", "ETH-USD"]

# 💰 capitale simulato
capitale = 10000
storico = []
cache = []
curva_capitale = []


# 📊 creazione dataset
def crea_dataset(df):
    df = df.copy()

    df["rendimento"] = df["Close"].pct_change()
    df["volatilita"] = df["rendimento"].rolling(10).std()
    df["media_10"] = df["Close"].rolling(10).mean()
    df["media_30"] = df["Close"].rolling(30).mean()

    df = df.dropna()

    df["target"] = np.where(df["Close"].shift(-1) > df["Close"], 1, 0)

    X = df[["rendimento", "volatilita", "media_10", "media_30"]]
    y = df["target"]

    return X, y


# 🤖 modello AI
def addestra_modello(df):
    X, y = crea_dataset(df)

    if len(X) < 80:
        return None

    modello = RandomForestClassifier(
        n_estimators=150,
        max_depth=7,
        random_state=42
    )

    modello.fit(X, y)

    return modello


# 📈 analisi asset
def analizza(asset):
    df = yf.download(asset, period="1y")

    if df.empty or len(df) < 100:
        return None

    modello = addestra_modello(df)

    if modello is None:
        return None

    ultimo = df.iloc[-1]

    input_dati = pd.DataFrame([{
        "rendimento": df["Close"].pct_change().iloc[-1],
        "volatilita": df["Close"].pct_change().rolling(10).std().iloc[-1],
        "media_10": df["Close"].rolling(10).mean().iloc[-1],
        "media_30": df["Close"].rolling(30).mean().iloc[-1]
    }])

    probabilita = modello.predict_proba(input_dati)[0][1]

    prezzo = float(ultimo["Close"])

    if probabilita > 0.65:
        segnale = "ACQUISTA"
    elif probabilita < 0.35:
        segnale = "VENDI"
    else:
        segnale = "NEUTRO"

    return {
        "asset": asset,
        "prezzo": round(prezzo, 2),
        "probabilita": round(probabilita, 2),
        "segnale": segnale
    }


# 💰 gestione capitale
def gestisci_capitale(segnale):
    global capitale

    peso = 0.01

    if segnale == "ACQUISTA":
        capitale += capitale * peso
    elif segnale == "VENDI":
        capitale -= capitale * peso

    curva_capitale.append(capitale)


# ⚠️ rischio (drawdown semplice)
def drawdown():
    if not curva_capitale:
        return 0

    picco = max(curva_capitale)
    return (picco - capitale) / picco * 100


# 🔁 loop sistema
def loop():
    global cache, storico

    while True:
        risultati = []

        for a in ASSETS:
            dati = analizza(a)

            if dati:
                gestisci_capitale(dati["segnale"])

                storico.append({
                    "asset": dati["asset"],
                    "segnale": dati["segnale"],
                    "prezzo": dati["prezzo"],
                    "capitale": round(capitale, 2)
                })

                risultati.append(dati)

        cache = risultati
        time.sleep(300)


# 🌐 login
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["user"] == USERNAME and request.form["pwd"] == PASSWORD:
            session["loggato"] = True
            return redirect("/dashboard")

    return render_template("login.html")


# 📊 dashboard italiana
@app.route("/dashboard")
def dashboard():
    if not session.get("loggato"):
        return redirect("/")

    return render_template(
        "dashboard.html",
        data=cache,
        capitale=round(capitale, 2),
        storico=storico[-30:],
        drawdown=round(drawdown(), 2)
    )


# 🚀 avvio sistema
if __name__ == "__main__":
    threading.Thread(target=loop).start()
    app.run(host="0.0.0.0", port=5000)
