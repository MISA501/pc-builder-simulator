from flask import Flask, render_template
import subprocess

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('pc-builder-simulator.html')

@app.route('/jugar')
def jugar():
    subprocess.run(['python', 'main.py'])
    return "El juego se está ejecutando en el servidor."

if __name__ == '__main__':
    app.run(debug=True)

