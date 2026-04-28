from flask import Flask, render_template, request, redirect, session
import yfinance as yf
import pandas as pd

app = Flask(__name__)
app.secret_key = "safe_app"

USERNAME = "admin"
PASSWORD = "admin123"

portfolio = {}

assets = ["AAPL", "TSLA", "MSFT", "AMZN", "NVDA"]


# RSI robusto
def compute_rsi(series, period=14):
    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi.fillna(50)  # 🔥 fallback


# MACD robusto
def compute_macd(series):
    exp1 = series.ewm(span=12, adjust=False).mean()
    exp2 = series.ewm(span=26, adjust=False).mean()

    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()

    return macd.fillna(0), signal.fillna(0)


def get_signal(rsi, macd, signal):
    if rsi < 30 and macd > signal:
        return "BUY"
    elif rsi > 70 and macd < signal:
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
    debug = []

    for a in assets:
        try:
            df = yf.download(a, period="1mo", interval="1d", progress=False)

            if df is None or df.empty:
                debug.append(f"{a}: NO DATA")
                continue

            debug.append(f"{a}: rows={len(df)}")

            # 🔥 CONVERSIONE SICURA
            df["Close"] = pd.to_numeric(df["Close"], errors="coerce")

            # 🔥 DROP valori non validi
            df = df.dropna(subset=["Close"])

            # 🔥 CALCOLI
            df["rsi"] = compute_rsi(df["Close"])
            df["macd"], df["signal"] = compute_macd(df["Close"])

            last = df.iloc[-1]

            price = float(last["Close"])
            rsi = float(last["rsi"])
            macd = float(last["macd"])
            signal_val = float(last["signal"])

            signals.append({
                "asset": a,
                "price": round(price, 2),
                "rsi": round(rsi, 2),
                "signal": get_signal(rsi, macd, signal_val)
            })

        except Exception as e:
            debug.append(f"{a}: ERROR -> {str(e)}")

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
