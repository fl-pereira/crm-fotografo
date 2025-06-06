from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import render_template, request, redirect, url_for, flash

import os

app = Flask(__name__)
app.config['SECRET_KEY'] = '123456'

# Configurar SQLite com caminho absoluto
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database', 'crm.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Criar pasta de banco de dados se não existir
os.makedirs(os.path.join(basedir, 'database'), exist_ok=True)

db = SQLAlchemy(app)

# Modelo básico de cliente
class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    email = db.Column(db.String(100))
    whatsapp = db.Column(db.String(20))


@app.route("/")
def home():
    return "Sistema iniciado com sucesso!"

@app.route("/clientes", methods=["GET", "POST"])
def clientes():
    if request.method == "POST":
        nome = request.form["nome"]
        cpf = request.form["cpf"]
        email = request.form["email"]
        whatsapp = request.form["whatsapp"]

        if Cliente.query.filter_by(cpf=cpf).first():
            flash("CPF já cadastrado!", "error")
            return redirect(url_for("clientes"))

        cliente = Cliente(nome=nome, cpf=cpf, email=email, whatsapp=whatsapp)
        db.session.add(cliente)
        db.session.commit()
        flash("Cliente cadastrado com sucesso!", "success")
        return redirect(url_for("clientes"))

    clientes = Cliente.query.order_by(Cliente.nome).all()
    return render_template("clientes.html", clientes=clientes)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)