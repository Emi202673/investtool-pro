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
        df = indicators(df)
        last = df.iloc[-1]

        signals.append({
            "asset": a,
            "price": round(last["Close"], 2),
            "rsi": round(last["rsi"], 2),
            "signal": get_signal(last)
        })

    return render_template(
        "dashboard.html",
        signals=signals,
        portfolio=portfolio
    )


@app.route("/add", methods=["POST"])
def add():
    asset = request.form.get("asset")
    qty = float(request.form.get("qty"))

    portfolio[asset] = portfolio.get(asset, 0) + qty
    return redirect("/dashboard")


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
