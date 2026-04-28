from flask import Flask, render_template, request, redirect, session
import random
import math

app = Flask(__name__)
app.secret_key = "efficient_frontier_v1"

USERNAME = "admin"
PASSWORD = "admin123"

assets = ["AAPL", "TSLA", "MSFT", "AMZN", "BTC"]

# 📊 rendimenti simulati
returns = {
    a: [random.gauss(0.001, 0.02) for _ in range(100)]
    for a in assets
}


# 📈 media
def mean(x):
    return sum(x) / len(x)


# 📉 volatilità
def vol(x):
    m = mean(x)
    return math.sqrt(sum((i - m) ** 2 for i in x) / len(x))


# 📊 correlazione semplificata
def corr(a, b):
    ma = mean(a)
    mb = mean(b)

    num = sum((a[i] - ma) * (b[i] - mb) for i in range(len(a)))
    den = math.sqrt(sum((a[i] - ma) ** 2 for i in range(len(a))) *
                    sum((b[i] - mb) ** 2 for i in range(len(b))))

    return num / den if den != 0 else 0


# 🧠 portafoglio random pesato
def random_portfolio():
    weights = [random.random() for _ in assets]
    s = sum(weights)
    weights = [w / s for w in weights]

    port_return = 0
    port_risk = 0

    # rendimento atteso
    for i, a in enumerate(assets):
        port_return += weights[i] * mean(returns[a])

    # rischio semplificato (varianza + correlazione)
    for i in range(len(assets)):
        for j in range(len(assets)):
            wi = weights[i]
            wj = weights[j]
            ri = returns[assets[i]]
            rj = returns[assets[j]]

            port_risk += wi * wj * corr(ri, rj) * vol(ri) * vol(rj)

    port_risk = math.sqrt(abs(port_risk))

    sharpe = port_return / port_risk if port_risk != 0 else 0

    return {
        "return": port_return,
        "risk": port_risk,
        "sharpe": sharpe
    }


# 🌐 LOGIN
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("user") == USERNAME and request.form.get("pwd") == PASSWORD:
            session["ok"] = True
            return redirect("/dashboard")
    return render_template("login.html")


# 📊 EFFICIENT FRONTIER
@app.route("/dashboard")
def dashboard():
    if not session.get("ok"):
        return redirect("/")

    portfolios = []

    for _ in range(30):  # simuliamo molti portafogli
        portfolios.append(random_portfolio())

    # 🏆 migliore Sharpe
    best = max(portfolios, key=lambda x: x["sharpe"])

    return render_template(
        "dashboard.html",
        portfolios=portfolios,
        best=best
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
