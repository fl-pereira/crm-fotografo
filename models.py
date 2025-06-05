from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

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