from flask import Flask, render_template, request, redirect, session
import random
import math

app = Flask(__name__)
app.secret_key = "portfolio_opt_v1"

USERNAME = "admin"
PASSWORD = "admin123"

capital = 10000

assets_list = ["AAPL", "TSLA", "MSFT", "AMZN", "BTC", "ETH"]

# 📊 storici rendimenti simulati
returns_data = {
    a: [random.gauss(0.001, 0.02) for _ in range(50)]
    for a in assets_list
}


# 📈 media rendimenti
def mean(r):
    return sum(r) / len(r)


# 📉 volatilità
def vol(r):
    m = mean(r)
    return math.sqrt(sum((x - m) ** 2 for x in r) / len(r))


# 🧠 score rischio/rendimento
def score_asset(r):
    return mean(r) / (vol(r) + 1e-6)


# ⚖️ ottimizzazione semplice (softmax dei score)
def portfolio_weights():
    scores = {a: score_asset(returns_data[a]) for a in assets_list}

    exp_scores = {a: math.exp(scores[a]) for a in assets_list}
    total = sum(exp_scores.values())

    weights = {a: exp_scores[a] / total for a in assets_list}

    return weights


# 🌐 LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("user") == USERNAME and request.form.get("pwd") == PASSWORD:
            session["ok"] = True
            return redirect("/dashboard")
    return render_template("login.html")


# 📊 DASHBOARD PORTFOLIO OPT
@app.route("/dashboard")
def dashboard():
    if not session.get("ok"):
        return redirect("/")

    weights = portfolio_weights()

    portfolio = []

    for a in assets_list:
        portfolio.append({
            "asset": a,
            "mean": round(mean(returns_data[a]), 5),
            "vol": round(vol(returns_data[a]), 5),
            "weight": round(weights[a], 4)
        })

    return render_template(
        "dashboard.html",
        portfolio=portfolio,
        capital=capital
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
