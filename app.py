from flask import Flask, render_template, request, redirect, session
import yfinance as yf
import ta

app = Flask(__name__)
app.secret_key = "hf_desk_final"

USERNAME = "admin"
PASSWORD = "admin123"

portfolio = {}
cash = 10000  # capitale simulato

assets = ["AAPL", "TSLA", "MSFT", "AMZN", "NVDA"]


# 📊 indicatori
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
    return "HOLD"


# 🧠 alpha score (opportunità)
def score(row):
    return (50 - row["rsi"]) + (row["macd"] - row["signal"]) * 10


# 📊 rischio portafoglio (semplice concentrazione)
def portfolio_risk():
    total = sum(portfolio.values()) if portfolio else 1
    return {k: v / total for k, v in portfolio.items()}


# 🌐 LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("user") == USERNAME and request.form.get("pwd") == PASSWORD:
            session["ok"] = True
            return redirect("/dashboard")
    return render_template("login.html")


# 🏦 DASHBOARD HEDGE FUND
@app.route("/dashboard")
def dashboard():
    if not session.get("ok"):
        return redirect("/")

    signals = []
    equity_curve = []
    global cash

    for a in assets:
        df = yf.download(a, period="3mo", interval="1d")
        df = indicators(df)

        last = df.iloc[-1]

        s = signal(last)
        sc = score(last)

        signals.append({
            "asset": a,
            "price": round(last["Close"], 2),
            "rsi": round(last["rsi"], 2),
            "signal": s,
            "score": round(sc, 2)
        })

    ranked = sorted(signals, key=lambda x: x["score"], reverse=True)
    top = ranked[0]

    # 🔥 decision engine finale
    if top["signal"] == "BUY":
        action = f"🟢 BUY {top['asset']}"
    elif top["signal"] == "SELL":
        action = f"🔴 SELL {top['asset']}"
    else:
        action = "⚪ HOLD - no edge"

    # 💼 portfolio risk
    risk = portfolio_risk()

    return render_template(
        "dashboard.html",
        signals=ranked,
        portfolio=portfolio,
        action=action,
        risk=risk,
        cash=round(cash, 2)
    )


# ➕ BUY
@app.route("/add", methods=["POST"])
def add():
    asset = request.form.get("asset")
    qty = float(request.form.get("qty"))

    portfolio[asset] = portfolio.get(asset, 0) + qty
    return redirect("/dashboard")


# ➖ SELL
@app.route("/remove", methods=["POST"])
def remove():
    asset = request.form.get("asset")
    qty = float(request.form.get("qty"))

    if asset in portfolio:
        portfolio[asset] -= qty
        if portfolio[asset] <= 0:
            del portfolio[asset]

    return redirect("/dashboard")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
