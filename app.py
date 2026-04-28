from flask import Flask, render_template, request, redirect, session
import random

app = Flask(__name__)
app.secret_key = "trading_desk_key"

# 👤 login semplice
USERNAME = "admin"
PASSWORD = "admin123"

# 💰 capitale simulato
capitale = 10000

# 📊 storico operazioni
storico = []

# 📈 asset simulati
ASSETS = ["AAPL", "TSLA", "MSFT", "AMZN", "BTC", "ETH"]


# 🌐 LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("user")
        pwd = request.form.get("pwd")

        if user == USERNAME and pwd == PASSWORD:
            session["ok"] = True
            return redirect("/dashboard")

    return render_template("login.html")


# 📊 DASHBOARD
@app.route("/dashboard")
def dashboard():
    if not session.get("ok"):
        return redirect("/")

    data = []

    for a in ASSETS:
        prezzo = round(random.uniform(50, 600), 2)
        segnale = random.choice(["BUY", "SELL", "HOLD"])

        data.append({
            "asset": a,
            "prezzo": prezzo,
            "segnale": segnale
        })

    return render_template(
        "dashboard.html",
        data=data,
        capitale=capitale
    )


# 🟢 BUY
@app.route("/buy", methods=["POST"])
def buy():
    global capitale

    asset = request.form.get("asset")

    trade_value = capitale * 0.01
    capitale += trade_value

    storico.append(f"BUY {asset} +{trade_value:.2f}")

    print("BUY:", asset)

    return redirect("/dashboard")


# 🔴 SELL
@app.route("/sell", methods=["POST"])
def sell():
    global capitale

    asset = request.form.get("asset")

    trade_value = capitale * 0.01
    capitale -= trade_value

    storico.append(f"SELL {asset} -{trade_value:.2f}")

    print("SELL:", asset)

    return redirect("/dashboard")


# 🚀 AVVIO
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
