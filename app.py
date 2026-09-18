import os
from flask import Flask, render_template

app = Flask(__name__)

# Página principal
@app.route("/")
def inicio():
    return render_template("pc-builder-simulator.html")

# Rutas para cada juego/página
@app.route("/bios")
def bios():
    return render_template("bios.html")

@app.route("/juego-cable-match")
def cable_match():
    return render_template("juego-cable-match.html")

@app.route("/juego-debug-hunter")
def debug_hunter():
    return render_template("juego-debug-hunter.html")

@app.route("/juego-firewall-defense")
def firewall_defense():
    return render_template("juego-firewall-defense.html")

@app.route("/juego-packet-runner")
def packet_runner():
    return render_template("juego-packet-runner.html")

@app.route("/juego-ram-rush")
def ram_rush():
    return render_template("juego-ram-rush.html")

@app.route("/linux_game")
def linux_game():
    return render_template("linux_game.html")

@app.route("/macos_game")
def macos_game():
    return render_template("macos_game.html")

@app.route("/pc-builder-pro-2d")
def pc_builder_pro():
    return render_template("pc-builder-pro-2d.html")

if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=puerto, debug=False)


