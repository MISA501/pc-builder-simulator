from flask import Flask, render_template, request, redirect
import smtplib
from email.message import EmailMessage

app = Flask(__name__)

@app.route('/enviar-feedback', methods=['POST'])
@app.route('/enviar-feedback', methods=['POST'])
def enviar_feedback():
    nombre = request.form.get('nombre')
    reaccion = request.form.get('reaccion')

    # Configuración del correo (ejemplo usando Gmail)
    msg = EmailMessage()
    msg.set_content(f"Nuevo mensaje de: {nombre}\n\nReacción:\n{reaccion}")
    msg['Subject'] = "¡Nueva reacción en tu Simulador Web!"
    msg['From'] = "misaelchavez856@gmail.com"
    msg['To'] = "misaelchavez856@gmail.com"

    try:
        # Nota: Necesitas una 'Contraseña de aplicación' de Google si usas Gmail
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login('tucorreo@gmail.com', 'tu_contraseña_de_aplicacion')
            smtp.send_message(msg)
    except Exception as e:
        print(f"Error al enviar: {e}")

    return redirect('/')

