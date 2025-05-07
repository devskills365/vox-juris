

"""
with app.app_context():
    # Créer les tables si elles n'existent pas
    db.create_all()
    
    # Ajouter un utilisateur de test
    user = User(email="test@example.com", password="test123", role="citizen", name="Test User")
    db.session.add(user)
    db.session.commit()
    
    # Afficher tous les utilisateurs
    print(User.query.all())

"""
from app import app
from models import db, User, Request
with app.app_context():
    user = User.query.filter_by(email="test@example.com").first()
    request = Request(citizen_id=user.id, audio_path="static/uploads/test_audio.mp3", domain="Immobilier")
    db.session.add(request)
    db.session.commit()
    print(Request.query.all())