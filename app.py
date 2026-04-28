from flask import Flask, render_template, request, redirect, session
import yfinance as yf
import ta

app = Flask(__name__)
app.secret_key = "unified_desk_final"

USERNAME = "admin"
PASSWORD = "admin123"

portfolio = {}

assets = ["AAPL", "TSLA", "MSFT", "AMZN", "NVDA", "BTC-USD"]


# 🧠 indicatori
def indicators(df):
    df["rsi"] = ta.momentum.RSIIndicator(df["Close"]).rsi()
    macd = ta.trend.MACD(df["Close"])
    df["macd"] = macd.macd()
    df["signal"] = macd.macd_signal()
    return df


# 🧠 segnale base
def signal(row):
    if row["rsi"] < 30 and row["macd"] > row["signal"]:
        return "BUY"
    elif row["rsi"] > 70 and row["macd"] < row["signal"]:
        return "SELL"
    else:
        return "HOLD"


# 🧠 score opportunità
def score(row):
    return (50 - row["rsi"]) + (row["macd"] - row["signal"]) * 10


# 🌐 LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("user") == USERNAME and request.form.get("pwd") == PASSWORD:
            session["ok"] = True
            return redirect("/dashboard")
    return render_template("login.html")


# 📊 DASHBOARD UNIFICATA
@app.route("/dashboard")
def dashboard():
    if not session.get("ok"):
        return redirect("/")

    signals = []
    actions = []

    for a in assets:

        df = yf.download(a, period="3mo", interval="1d")
        df = indicators(df)

        last = df.iloc[-1]

        sig = signal(last)
        sc = score(last)

        signals.append({
            "asset": a,
            "price": round(last["Close"], 2),
            "rsi": round(last["rsi"], 2),
            "signal": sig,
            "score": round(sc, 2)
        })

    # 🔥 ranking opportunità
    ranked = sorted(signals, key=lambda x: x["score"], reverse=True)

    # 🧠 decision engine finale
    top = ranked[0]

    if top["signal"] == "BUY":
        actions.append(f"🟢 BUY {top['asset']} (top opportunity)")
    elif top["signal"] == "SELL":
        actions.append(f"🔴 SELL {top['asset']} (risk/reversal)")
    else:
        actions.append(f"⚪ HOLD - no strong setup")

    return render_template(
        "dashboard.html",
        ranked=ranked,
        actions=actions,
        portfolio=portfolio
    )


# 🟢 BUY
@app.route("/buy", methods=["POST"])
def buy():
    asset = request.form.get("asset")
    portfolio[asset] = portfolio.get(asset, 0) + 1
    return redirect("/dashboard")


# 🔴 SELL
@app.route("/sell", methods=["POST"])
def sell():
    asset = request.form.get("asset")
    if asset in portfolio:
        portfolio[asset] -= 1
        if portfolio[asset] <= 0:
            del portfolio[asset]
    return redirect("/dashboard")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
