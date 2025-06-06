import os
import re
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, make_response, send_from_directory, flash
from flask_sqlalchemy import SQLAlchemy
from weasyprint import HTML
from werkzeug.utils import secure_filename
from pathlib import Path

# Configuração inicial
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///contratos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'  # Para mensagens flash
app.config['UPLOAD_FOLDER'] = 'static/assinaturas'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

# Criar pasta de uploads se não existir
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Inicialização do banco de dados
db = SQLAlchemy(app)

# Modelos (models.py)
class Cliente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_completo = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    email = db.Column(db.String(100))
    whatsapp = db.Column(db.String(20))
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow)
    contratos = db.relationship('Contrato', backref='cliente', lazy=True)

class Contrato(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(20))  # 'evento' ou 'ensaio'
    
    # Campos comuns a ambos
    data_contrato = db.Column(db.String(20))  # DATA POR EXTENSO
    valor = db.Column(db.String(20))
    forma_pagamento = db.Column(db.String(100))
    descricao_servico = db.Column(db.Text)
    arquivo_pdf = db.Column(db.String(100))
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    cliente_id = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    
    # Campos específicos para ensaios
    data_ensaio = db.Column(db.String(20))
    horario_ensaio = db.Column(db.String(20))
    local_ensaio = db.Column(db.String(100))
    cidade_estado_ensaio = db.Column(db.String(50))
    duracao_ensaio = db.Column(db.String(20))
    
    # Campos específicos para eventos
    nome_evento = db.Column(db.String(100))
    data_evento = db.Column(db.String(20))
    horario_evento = db.Column(db.String(20))
    local_evento = db.Column(db.String(100))
    cidade_estado_evento = db.Column(db.String(50))
    tempo_cobertura = db.Column(db.String(20))
    qtd_fotografos = db.Column(db.Integer)
    
    # Informações de assinatura
    assinatura_cliente = db.Column(db.String(100))  # caminho para imagem da assinatura
    data_assinatura = db.Column(db.String(20))

# Funções auxiliares
def validar_cpf(cpf):
    """Valida o formato do CPF (apenas formato, não verifica dígitos verificadores)"""
    return re.match(r'^\d{3}\.\d{3}\.\d{3}-\d{2}$', cpf) is not None

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def formatar_data_extenso(data_str):
    """Converte '2023-01-10' para '10 de janeiro de 2023'"""
    try:
        data = datetime.strptime(data_str, '%Y-%m-%d')
        meses = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
                'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro']
        return f"{data.day} de {meses[data.month - 1]} de {data.year}"
    except:
        return data_str

# Rotas principais
@app.route('/')
def home():
    return redirect(url_for('listar_contratos'))

# Rotas de Clientes
@app.route('/clientes')
def listar_clientes():
    clientes = Cliente.query.order_by(Cliente.nome_completo).all()
    return render_template('lista_clientes.html', clientes=clientes)

@app.route('/cliente/novo', methods=['GET', 'POST'])
def cadastrar_cliente():
    if request.method == 'POST':
        nome = request.form['nome_completo']
        cpf = request.form['cpf']
        email = request.form.get('email', '')
        whatsapp = request.form.get('whatsapp', '')
        
        # Validações
        if not validar_cpf(cpf):
            flash('CPF inválido. Formato esperado: 000.000.000-00', 'error')
            return render_template('cliente_form.html', 
                                nome=nome, cpf=cpf, email=email, whatsapp=whatsapp)
        
        if Cliente.query.filter_by(cpf=cpf).first():
            flash('Já existe um cliente cadastrado com este CPF', 'error')
            return render_template('cliente_form.html', 
                                nome=nome, cpf=cpf, email=email, whatsapp=whatsapp)
        
        cliente = Cliente(
            nome_completo=nome,
            cpf=cpf,
            email=email,
            whatsapp=whatsapp
        )
        
        db.session.add(cliente)
        db.session.commit()
        flash('Cliente cadastrado com sucesso!', 'success')
        return redirect(url_for('listar_clientes'))
    
    return render_template('cliente_form.html')

@app.route('/cliente/<int:id>/contratos')
def contratos_cliente(id):
    cliente = Cliente.query.get_or_404(id)
    contratos = Contrato.query.filter_by(cliente_id=id).order_by(Contrato.data_criacao.desc()).all()
    return render_template('contratos_cliente.html', cliente=cliente, contratos=contratos)

# Rotas de Contratos
@app.route('/contratos')
def listar_contratos():
    contratos = Contrato.query.order_by(Contrato.data_criacao.desc()).limit(50).all()
    return render_template('lista_contratos.html', contratos=contratos)

@app.route('/contrato/novo/<tipo>')
def novo_contrato(tipo):
    if tipo not in ['evento', 'ensaio']:
        return redirect(url_for('home'))
    
    clientes = Cliente.query.order_by(Cliente.nome_completo).all()
    return render_template(f'form_{tipo}.html', clientes=clientes)

@app.route('/contrato/gerar', methods=['POST'])
def gerar_contrato():
    tipo = request.form.get('tipo')
    cliente_id = request.form.get('cliente_id')
    
    if tipo not in ['evento', 'ensaio'] or not cliente_id:
        flash('Dados inválidos para gerar contrato', 'error')
        return redirect(url_for('home'))
    
    cliente = Cliente.query.get_or_404(cliente_id)
    
    # Validação de data para eventos
    if tipo == 'evento':
        data_evento = request.form.get('data_evento')
        try:
            data_obj = datetime.strptime(data_evento, '%Y-%m-%d')
            if data_obj < datetime.now():
                flash('A data do evento não pode ser no passado', 'error')
                return redirect(url_for('novo_contrato', tipo='evento'))
        except:
            flash('Data do evento inválida', 'error')
            return redirect(url_for('novo_contrato', tipo='evento'))
    
    # Criação do contrato
    if tipo == 'ensaio':
        contrato = Contrato(
            tipo='ensaio',
            cliente_id=cliente.id,
            data_ensaio=request.form.get('data_ensaio'),
            horario_ensaio=request.form.get('horario_ensaio'),
            local_ensaio=request.form.get('local_ensaio'),
            cidade_estado_ensaio=request.form.get('cidade_estado_ensaio'),
            duracao_ensaio=request.form.get('duracao_ensaio'),
            descricao_servico=request.form.get('descricao_servico'),
            valor=request.form.get('valor'),
            forma_pagamento=request.form.get('forma_pagamento'),
            data_contrato=formatar_data_extenso(request.form.get('data_contrato'))
        )
    else:  # evento
        contrato = Contrato(
            tipo='evento',
            cliente_id=cliente.id,
            nome_evento=request.form.get('nome_evento'),
            data_evento=request.form.get('data_evento'),
            horario_evento=request.form.get('horario_evento'),
            local_evento=request.form.get('local_evento'),
            cidade_estado_evento=request.form.get('cidade_estado_evento'),
            tempo_cobertura=request.form.get('tempo_cobertura'),
            qtd_fotografos=request.form.get('qtd_fotografos'),
            descricao_servico=request.form.get('descricao_servico'),
            valor=request.form.get('valor'),
            forma_pagamento=request.form.get('forma_pagamento'),
            data_contrato=formatar_data_extenso(request.form.get('data_contrato'))
        )
    
    db.session.add(contrato)
    db.session.commit()
    
    # Gerar PDF
    html = render_template(f'contrato_{tipo}.html', contrato=contrato)
    pdf = HTML(string=html).write_pdf()
    
    # Salvar PDF
    filename = f"contrato_{contrato.id}.pdf"
    pdf_path = os.path.join('static', filename)
    with open(pdf_path, 'wb') as f:
        f.write(pdf)
    
    # Atualizar contrato com nome do arquivo
    contrato.arquivo_pdf = filename
    db.session.commit()
    
    flash('Contrato gerado com sucesso!', 'success')
    return redirect(url_for('visualizar_contrato', id=contrato.id))

@app.route('/contrato/<int:id>')
def visualizar_contrato(id):
    contrato = Contrato.query.get_or_404(id)
    if not contrato.arquivo_pdf:
        flash('Arquivo PDF não encontrado', 'error')
        return redirect(url_for('listar_contratos'))
    
    pdf_path = os.path.join('static', contrato.arquivo_pdf)
    if not os.path.exists(pdf_path):
        flash('Arquivo PDF não encontrado no servidor', 'error')
        return redirect(url_for('listar_contratos'))
    
    with open(pdf_path, 'rb') as f:
        pdf = f.read()
    
    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'inline; filename=contrato_{id}.pdf'
    return response

@app.route('/contrato/<int:id>/download')
def download_contrato(id):
    contrato = Contrato.query.get_or_404(id)
    if not contrato.arquivo_pdf:
        flash('Arquivo PDF não encontrado', 'error')
        return redirect(url_for('listar_contratos'))
    
    return send_from_directory('static', contrato.arquivo_pdf, as_attachment=True)

# Busca
@app.route('/buscar_contratos')
def buscar_contratos():
    tipo = request.args.get('tipo')
    nome_cliente = request.args.get('nome_cliente')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    query = Contrato.query.join(Cliente)
    
    if tipo:
        query = query.filter(Contrato.tipo == tipo)
    
    if nome_cliente:
        query = query.filter(Cliente.nome_completo.ilike(f'%{nome_cliente}%'))
    
    if data_inicio and data_fim:
        try:
            if tipo == 'evento':
                query = query.filter(Contrato.data_evento.between(data_inicio, data_fim))
            else:
                query = query.filter(Contrato.data_ensaio.between(data_inicio, data_fim))
        except:
            flash('Datas inválidas para filtro', 'error')
    
    contratos = query.order_by(Contrato.data_criacao.desc()).all()
    return render_template('busca_contratos.html', contratos=contratos)

# Inicialização do banco de dados
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)