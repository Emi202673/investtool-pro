from flask import Flask, render_template, request, redirect, session
import yfinance as yf
import ta

app = Flask(__name__)
app.secret_key = "safe_app"

USERNAME = "admin"
PASSWORD = "admin123"

portfolio = {}

assets = ["AAPL", "TSLA", "MSFT", "AMZN", "NVDA"]


def indicators(df):
    try:
        df["rsi"] = ta.momentum.RSIIndicator(df["Close"]).rsi()
        macd = ta.trend.MACD(df["Close"])
        df["macd"] = macd.macd()
        df["signal"] = macd.macd_signal()
    except:
        df["rsi"] = 50
        df["macd"] = 0
        df["signal"] = 0
    return df


def get_signal(row):
    try:
        if row["rsi"] < 30 and row["macd"] > row["signal"]:
            return "BUY"
        elif row["rsi"] > 70 and row["macd"] < row["signal"]:
            return "SELL"
        return "HOLD"
    except:
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
    debug = []

    for a in assets:
        try:
            df = yf.download(
                a,
                period="1mo",
                interval="1d",
                progress=False,
                threads=False
            )

            # DEBUG
            debug.append(f"{a}: rows={0 if df is None else len(df)}")

            if df is None or df.empty:
                raise Exception("NO DATA")

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
            debug.append(f"{a}: ERROR")

    return render_template(
        "dashboard.html",
        signals=signals,
        portfolio=portfolio,
        debug=debug
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
