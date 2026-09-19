import os
from flask import Flask, render_template, request, jsonify
import smtplib
from email.mime.text import MIMEText

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

@app.route("/laboratorio-encriptado")
def laboratorio_encriptado():
    return render_template("laboratorio-encriptado.html")


# ---------------------------------------------------------------
# IMPORTANTE: esta ruta debe registrarse ANTES de app.run().
# app.run() bloquea la ejecución del script mientras el servidor
# está corriendo, así que cualquier @app.route colocado después
# de esa línea nunca llega a registrarse. Eso era lo que causaba
# el error "Unexpected token '<'": Flask respondía con su página
# 404 en HTML porque no conocía la ruta /rate.
# ---------------------------------------------------------------
@app.route("/rate", methods=["POST"])
def rate():
    data = request.json
    reaction = data.get("rating")

    # --- Guardar en archivo ---
    with open("reacciones.txt", "a", encoding="utf-8") as f:
        f.write(reaction + "\n")

    # --- Enviar correo ---
    remitente = "misaelchavez856@gmail.com"
    destinatario = "misaelchavez856@gmail.com"  # puede ser el mismo o otro

    # La contraseña ya NO va escrita en el código: se lee de una
    # variable de entorno llamada GMAIL_APP_PASSWORD. Así, si subes
    # este archivo a GitHub o lo compartes, la contraseña no queda expuesta.
    contraseña = os.environ.get("GMAIL_APP_PASSWORD")

    if not contraseña:
        print("⚠️ No se configuró la variable de entorno GMAIL_APP_PASSWORD; se omite el envío de correo.")
    else:
        mensaje = MIMEText(f"Se recibió una nueva reacción: {reaction}")
        mensaje["Subject"] = "Nueva reacción en tu sitio"
        mensaje["From"] = remitente
        mensaje["To"] = destinatario

        try:
            with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
                servidor.login(remitente, contraseña)
                servidor.sendmail(remitente, destinatario, mensaje.as_string())
            print("Correo enviado con éxito")
        except Exception as e:
            print("Error al enviar correo:", e)

    return jsonify({"message": "Gracias por tu opinión"})


if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=puerto, debug=False)
