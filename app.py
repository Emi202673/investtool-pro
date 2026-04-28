from flask import Flask, render_template, request, redirect, session
import random

app = Flask(__name__)
app.secret_key = "chiave_semplice"

# 👤 login semplice
USERNAME = "admin"
PASSWORD = "admin123"

# 💰 dati simulati
capitale = 10000

storico = []
data = []


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

    # simulazione dati mercato
    data = []
    assets = ["AAPL", "TSLA", "MSFT", "BTC"]

    for a in assets:
        prezzo = round(random.uniform(50, 500), 2)
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


# 🚀 AVVIO
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
