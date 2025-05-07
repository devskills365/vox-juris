from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'citizen' ou 'professional'
    name = db.Column(db.String(100))
    expertise = db.Column(db.String(100))  # Pour les professionnels
    location = db.Column(db.String(100))  # Localisation
    profile_picture = db.Column(db.String(200))  # Chemin de la photo
    requests = db.relationship('Request', foreign_keys='Request.citizen_id', backref='user', lazy=True)
    accepted_requests = db.relationship('Request', foreign_keys='Request.professional_id', backref='professional', lazy=True)
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy=True)
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy=True)

class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    citizen_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    audio_path = db.Column(db.String(200))  # Chemin du fichier audio (nullable)
    description = db.Column(db.Text)  # Description textuelle
    domain = db.Column(db.String(100))  # Domaine juridique
    status = db.Column(db.String(20), default='open')  # 'open', 'accepted', 'resolved'
    professional_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    messages = db.relationship('Message', backref='request', lazy=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('request.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text)  # Contenu textuel (nullable)
    audio_path = db.Column(db.String(200))  # Chemin du fichier audio (nullable)
    sent_at = db.Column(db.DateTime, default=db.func.current_timestamp())