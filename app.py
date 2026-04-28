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
        df = yf.download(a, period="3mo", interval="1d")

        if df is None or df.empty:
            continue

        df = indicators(df)
        last = df.iloc[-1]

        rsi = float(last["rsi"]) if last["rsi"] == last["rsi"] else 50
        macd_score = last["macd"] - last["signal"]

        # 🧠 ALPHA SCORE (semplificato ma efficace)
        score = (50 - rsi) + (macd_score * 10)

        signals.append({
            "asset": a,
            "price": round(last["Close"], 2),
            "rsi": round(rsi, 2),
            "signal": get_signal(last),
            "score": round(score, 2)
        })

    # 📊 ranking
    ranked = sorted(signals, key=lambda x: x["score"], reverse=True)

    # 🔥 decisione principale
    top = ranked[0]

    if top["signal"] == "BUY":
        action = f"🟢 BUY {top['asset']} (TOP OPPORTUNITY)"
    elif top["signal"] == "SELL":
        action = f"🔴 SELL {top['asset']} (RISK OFF)"
    else:
        action = "⚪ NO CLEAR EDGE"

    return render_template(
        "dashboard.html",
        signals=ranked,
        portfolio=portfolio,
        action=action
    )
