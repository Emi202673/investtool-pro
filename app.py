from flask import Flask, render_template, request, redirect, session
import yfinance as yf
import ta

app = Flask(__name__)
app.secret_key = "desk"

USERNAME = "admin"
PASSWORD = "admin123"

portfolio = {}

assets = ["AAPL", "TSLA", "MSFT", "AMZN", "NVDA"]


def indicators(df):
    df["rsi"] = ta.momentum.RSIIndicator(df["Close"]).rsi()
    macd = ta.trend.MACD(df["Close"])
    df["macd"] = macd.macd()
    df["signal"] = macd.macd_signal()
    return df


def get_signal(row):
    if row["rsi"] < 30 and row["macd"] > row["signal"]:
        return "BUY"
    elif row["rsi"] > 70 and row["macd"] < row["signal"]:
        return "SELL"
    return "HOLD"


@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("user") == USERNAME and request.form.get("pwd") == PASSWORD:
            session["ok"] = True
            return redirect("/dashboard")
    return render_template("login.html")

@app.route("/dashboard")
def dashboard():
    if not session.get("ok"):
        return redirect("/")

    signals = []

    for a in assets:

        try:
            df = yf.download(a, period="3mo", interval="1d")

            # 🧠 STEP CRITICO: se vuoto salta
            if df is None or df.empty:
                continue

            df = indicators(df)

            last = df.iloc[-1]

            close = float(last["Close"]) if last["Close"] == last["Close"] else 0
            rsi = float(last["rsi"]) if last["rsi"] == last["rsi"] else 50

            signals.append({
                "asset": a,
                "price": round(close, 2),
                "rsi": round(rsi, 2),
                "signal": get_signal(last)
            })

        except Exception as e:
            print("ERROR on", a, e)

    # fallback sicurezza
    if len(signals) == 0:
        signals.append({
            "asset": "NO DATA",
            "price": 0,
            "rsi": 0,
            "signal": "HOLD"
        })

    return render_template(
        "dashboard.html",
        signals=signals,
        portfolio=portfolio
    )
    # fallback se tutto vuoto
    if len(signals) == 0:
        signals = [{
            "asset": "NO DATA",
            "price": 0,
            "rsi": 0,
            "signal": "HOLD"
        }]

    return render_template(
        "dashboard.html",
        signals=signals,
        portfolio=portfolio
    )
