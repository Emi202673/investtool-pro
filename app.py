from flask import Flask, render_template, request, redirect, session
import random

app = Flask(__name__)
app.secret_key = "chiave_trading"

# 👤 login
USERNAME = "admin"
PASSWORD = "admin123"

# 💰 capitale
capitale = 10000


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

    assets = ["AAPL", "TSLA", "MSFT", "AMZN", "BTC", "ETH"]

    data = []

    for a in assets:
        data.append({
            "asset": a,
            "prezzo": round(random.uniform(50, 600), 2),
            "segnale": random.choice(["BUY", "SELL", "HOLD"])
        })

    return render_template("dashboard.html", data=data, capitale=capitale)


# 🟢 BUY
@app.route("/buy", methods=["POST"])
def buy():
    global capitale

    capitale += capitale * 0.01

    return redirect("/dashboard")


# 🔴 SELL
@app.route("/sell", methods=["POST"])
def sell():
    global capitale

    capitale -= capitale * 0.01

    return redirect("/dashboard")


# 🚀 AVVIO
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
