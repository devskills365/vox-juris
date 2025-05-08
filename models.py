from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'citizen' ou 'professional'
    expertise = db.Column(db.String(255))  # Description générale de l'expertise
    expertise_domains = db.Column(db.String(500))  # Domaines d'intervention (ex. "Droit immobilier,Droit OHADA")
    location = db.Column(db.String(100))
    profile_picture = db.Column(db.String(255))
    requests = db.relationship('Request', backref='user', lazy=True, foreign_keys='Request.citizen_id')
    professional_requests = db.relationship('Request', backref='professional', lazy=True, foreign_keys='Request.professional_id')
    sent_messages = db.relationship('Message', backref='sender', lazy=True, foreign_keys='Message.sender_id')
    received_messages = db.relationship('Message', backref='receiver', lazy=True, foreign_keys='Message.receiver_id')

    def get_expertise_domains(self):
        return self.expertise_domains.split(',') if self.expertise_domains else []

    def set_expertise_domains(self, domains):
        self.expertise_domains = ','.join(domains) if domains else None

class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    citizen_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    audio_path = db.Column(db.String(255))
    description = db.Column(db.Text)
    domain = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default='open')  # 'open', 'accepted', 'resolved'
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    messages = db.relationship('Message', backref='request', lazy=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('request.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text)
    audio_path = db.Column(db.String(255))
    sent_at = db.Column(db.DateTime, default=db.func.current_timestamp())