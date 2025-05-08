from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv
from models import db, User, Request, Message
import bcrypt
import os
from werkzeug.utils import secure_filename
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', '/app/static/uploads')
app.config['PROFILE_PICTURE_FOLDER'] = os.getenv('PROFILE_PICTURE_FOLDER', '/app/static/profile_pictures')
app.config['PDF_FOLDER'] = os.getenv('PDF_FOLDER', '/app/static/pdfs')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///voxjuris.db'
print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ALLOWED_EXTENSIONS'] = {'mp3', 'wav'}
app.config['ALLOWED_IMAGE_EXTENSIONS'] = {'jpg', 'jpeg', 'png'}

# Liste des domaines d'intervention
EXPERTISE_DOMAINS = [
    'Droit immobilier', 'Voies d\'exécution', 'Arbitrage', 'Droit OHADA',
    'Droit bancaire', 'Droit des assurances', 'Droit fiscal', 'Droit social',
    'Droit des affaires', 'Droit du travail et des affaires sociales', 'Recouvrement de créances'
]

db.init_app(app)

# Initialiser la base de données
with app.app_context():
    db.create_all()

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@app.route('/')
def home():
    num_professionals = User.query.filter_by(role='professional').count()
    num_requests = Request.query.count()
    num_resolved_requests = Request.query.filter_by(status='resolved').count()
    return render_template('base.html', 
                         num_professionals=num_professionals,
                         num_requests=num_requests,
                         num_resolved_requests=num_resolved_requests)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')
        name = request.form['name']
        role = request.form['role']
        expertise = request.form.get('expertise')
        expertise_domains = request.form.getlist('expertise_domains')  # Sélection multiple
        location = request.form.get('location')
        profile_picture = request.files.get('profile_picture')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Cet email est déjà utilisé.')
            return redirect(url_for('register'))

        if role == 'professional' and not expertise_domains:
            flash('Veuillez sélectionner au moins un domaine d\'intervention.')
            return redirect(url_for('register'))

        # Valider les domaines
        if role == 'professional':
            invalid_domains = [d for d in expertise_domains if d not in EXPERTISE_DOMAINS]
            if invalid_domains:
                flash(f'Domaines invalides : {", ".join(invalid_domains)}')
                return redirect(url_for('register'))

        profile_picture_path = None
        if profile_picture and allowed_file(profile_picture.filename, app.config['ALLOWED_IMAGE_EXTENSIONS']):
            filename = secure_filename(profile_picture.filename)
            profile_picture_path = f"profile_pictures/{filename}"
            absolute_path = os.path.join(app.config['PROFILE_PICTURE_FOLDER'], filename)
            os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
            profile_picture.save(absolute_path)

        hashed_password = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')
        new_user = User(
            email=email,
            password=hashed_password,
            name=name,
            role=role,
            expertise=expertise if role == 'professional' else None,
            location=location,
            profile_picture=profile_picture_path
        )
        if role == 'professional':
            new_user.set_expertise_domains(expertise_domains)
        db.session.add(new_user)
        db.session.commit()

        flash('Inscription réussie ! Veuillez vous connecter.')
        return redirect(url_for('login'))

    return render_template('register.html', expertise_domains=EXPERTISE_DOMAINS)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password'].encode('utf-8')

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.checkpw(password, user.password.encode('utf-8')):
            login_user(user)
            if user.role == 'citizen':
                accepted_requests = Request.query.filter_by(citizen_id=user.id, status='accepted').all()
                for req in accepted_requests:
                    if req.professional:
                        flash(f'Votre demande dans le domaine {req.domain} a été acceptée par {req.professional.name}.')
            return redirect(url_for('home'))
        else:
            flash('Email ou mot de passe incorrect.')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/submit_request', methods=['GET', 'POST'])
@login_required
def submit_request():
    if current_user.role != 'citizen':
        flash('Seuls les citoyens peuvent soumettre des demandes.')
        return redirect(url_for('home'))

    if request.method == 'POST':
        domain = request.form['domain']
        description = request.form.get('description')
        recorded_audio = request.files.get('recordedAudio')
        uploaded_audio = request.files.get('audio')

        # Valider le domaine
        if domain not in EXPERTISE_DOMAINS:
            flash(f'Domaine invalide : {domain}')
            return redirect(url_for('submit_request'))

        audio_path = None
        if recorded_audio and allowed_file(recorded_audio.filename, app.config['ALLOWED_EXTENSIONS']):
            filename = secure_filename(recorded_audio.filename)
            audio_path = f"uploads/{filename}"
            absolute_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
            recorded_audio.save(absolute_path)
        elif uploaded_audio and allowed_file(uploaded_audio.filename, app.config['ALLOWED_EXTENSIONS']):
            filename = secure_filename(uploaded_audio.filename)
            audio_path = f"uploads/{filename}"
            absolute_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
            uploaded_audio.save(absolute_path)

        if not audio_path and not description:
            flash('Vous devez fournir au moins un audio ou une description.')
            return redirect(url_for('submit_request'))

        new_request = Request(
            citizen_id=current_user.id,
            audio_path=audio_path,
            description=description,
            domain=domain
        )
        db.session.add(new_request)
        db.session.commit()

        flash('Demande soumise avec succès !')
        return redirect(url_for('home'))

    return render_template('submit_request.html', expertise_domains=EXPERTISE_DOMAINS)

@app.route('/view_requests')
@login_required
def view_requests():
    if current_user.role != 'professional':
        flash('Seuls les professionnels peuvent voir les demandes.')
        return redirect(url_for('home'))

    domain = request.args.get('domain')
    status = request.args.get('status')

    query = Request.query
    if domain:
        if domain not in EXPERTISE_DOMAINS:
            flash(f'Domaine invalide : {domain}')
            return redirect(url_for('view_requests'))
        query = query.filter_by(domain=domain)
    if status:
        query = query.filter_by(status=status)
    else:
        query = query.filter(Request.status != 'resolved')
    requests = query.all()

    return render_template('view_requests.html', requests=requests, expertise_domains=EXPERTISE_DOMAINS)

@app.route('/accept_request/<int:request_id>', methods=['POST'])
@login_required
def accept_request(request_id):
    if current_user.role != 'professional':
        flash('Seuls les professionnels peuvent accepter des demandes.')
        return redirect(url_for('home'))

    req = Request.query.get_or_404(request_id)
    if req.status != 'open':
        flash('Cette demande n\'est plus disponible.')
        return redirect(url_for('view_requests'))

    req.status = 'accepted'
    req.professional_id = current_user.id
    db.session.commit()

    flash('Demande acceptée avec succès !')
    return redirect(url_for('view_requests'))

@app.route('/resolve_request/<int:request_id>', methods=['POST'])
@login_required
def resolve_request(request_id):
    req = Request.query.get_or_404(request_id)
    if current_user.role == 'professional' and req.professional_id != current_user.id:
        flash('Vous ne pouvez pas résoudre cette demande.')
        return redirect(url_for('view_requests'))
    if current_user.role == 'citizen' and req.citizen_id != current_user.id:
        flash('Vous ne pouvez pas résoudre cette demande.')
        return redirect(url_for('my_requests'))
    if req.status != 'accepted':
        flash('Cette demande ne peut pas être marquée comme résolue.')
        return redirect(url_for('view_requests' if current_user.role == 'professional' else 'my_requests'))

    req.status = 'resolved'
    db.session.commit()

    flash('Demande marquée comme résolue avec succès !')
    return redirect(url_for('view_requests' if current_user.role == 'professional' else 'my_requests'))

@app.route('/my_requests')
@login_required
def my_requests():
    if current_user.role != 'citizen':
        flash('Seuls les citoyens peuvent voir leurs demandes.')
        return redirect(url_for('home'))

    requests = Request.query.filter_by(citizen_id=current_user.id).all()
    return render_template('my_requests.html', requests=requests)

@app.route('/messages/<int:request_id>', methods=['GET', 'POST'])
@login_required
def messages(request_id):
    req = Request.query.get_or_404(request_id)
    if req.status not in ['accepted', 'resolved'] or (current_user.id not in [req.citizen_id, req.professional_id]):
        flash('Vous n\'avez pas accès à cette messagerie.')
        return redirect(url_for('home'))

    if request.method == 'POST':
        content = request.form.get('content')
        recorded_audio = request.files.get('messageRecordedAudio')

        audio_path = None
        if recorded_audio and allowed_file(recorded_audio.filename, app.config['ALLOWED_EXTENSIONS']):
            filename = secure_filename(recorded_audio.filename)
            audio_path = f"uploads/{filename}"
            absolute_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
            recorded_audio.save(absolute_path)

        if not content and not audio_path:
            flash('Vous devez fournir un message texte ou audio.')
            return redirect(url_for('messages', request_id=request_id))

        receiver_id = req.professional_id if current_user.id == req.citizen_id else req.citizen_id
        new_message = Message(
            request_id=request_id,
            sender_id=current_user.id,
            receiver_id=receiver_id,
            content=content,
            audio_path=audio_path
        )
        db.session.add(new_message)
        db.session.commit()
        flash('Message envoyé avec succès !')
        return redirect(url_for('messages', request_id=request_id))

    messages = Message.query.filter_by(request_id=request_id).order_by(Message.sent_at.asc()).all()
    return render_template('messages.html', request_obj=req, messages=messages)

@app.route('/messages_inbox')
@login_required
def messages_inbox():
    if current_user.role == 'citizen':
        conversations = Request.query.filter_by(citizen_id=current_user.id).filter(Request.status.in_(['accepted', 'resolved'])).all()
    else:
        conversations = Request.query.filter_by(professional_id=current_user.id).filter(Request.status.in_(['accepted', 'resolved'])).all()
    return render_template('messages_inbox.html', conversations=conversations)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        expertise = request.form.get('expertise')
        expertise_domains = request.form.getlist('expertise_domains')
        location = request.form.get('location')
        profile_picture = request.files.get('profile_picture')

        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.id != current_user.id:
            flash('Cet email est déjà utilisé.')
            return redirect(url_for('profile'))

        if current_user.role == 'professional' and not expertise_domains:
            flash('Veuillez sélectionner au moins un domaine d\'intervention.')
            return redirect(url_for('profile'))

        # Valider les domaines
        if current_user.role == 'professional':
            invalid_domains = [d for d in expertise_domains if d not in EXPERTISE_DOMAINS]
            if invalid_domains:
                flash(f'Domaines invalides : {", ".join(invalid_domains)}')
                return redirect(url_for('profile'))

        current_user.name = name
        current_user.email = email
        if current_user.role == 'professional':
            current_user.expertise = expertise
            current_user.set_expertise_domains(expertise_domains)
        current_user.location = location

        if profile_picture and allowed_file(profile_picture.filename, app.config['ALLOWED_IMAGE_EXTENSIONS']):
            filename = secure_filename(profile_picture.filename)
            profile_picture_path = f"profile_pictures/{filename}"
            absolute_path = os.path.join(app.config['PROFILE_PICTURE_FOLDER'], filename)
            os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
            profile_picture.save(absolute_path)
            current_user.profile_picture = profile_picture_path

        db.session.commit()
        flash('Profil mis à jour avec succès !')
        return redirect(url_for('profile'))

    return render_template('profile.html', expertise_domains=EXPERTISE_DOMAINS)

@app.route('/export_pdf/<int:request_id>')
@login_required
def export_pdf(request_id):
    req = Request.query.get_or_404(request_id)
    if (current_user.role == 'citizen' and req.citizen_id != current_user.id) or \
       (current_user.role == 'professional' and req.professional_id != current_user.id) or \
       req.status != 'resolved':
        flash('Vous n\'avez pas accès à l\'exportation de cette demande.')
        return redirect(url_for('my_requests' if current_user.role == 'citizen' else 'view_requests'))

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"request_{request_id}_{timestamp}.pdf"
    pdf_path = os.path.join(app.config['PDF_FOLDER'], filename)
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

    doc = SimpleDocTemplate(pdf_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"Rapport de la Demande #{req.id}", styles['Title']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Domaine :</b> {req.domain}", styles['Normal']))
    story.append(Paragraph(f"<b>Statut :</b> {req.status}", styles['Normal']))
    story.append(Paragraph(f"<b>Date de création :</b> {req.created_at.strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Paragraph(f"<b>Soumis par :</b> {req.user.name}", styles['Normal']))
    story.append(Paragraph(f"<b>Accepté par :</b> {req.professional.name if req.professional else 'N/A'}", styles['Normal']))
    story.append(Spacer(1, 12))

    if req.description:
        story.append(Paragraph("<b>Description :</b>", styles['Heading2']))
        story.append(Paragraph(req.description, styles['Normal']))
        story.append(Spacer(1, 12))

    if req.audio_path:
        story.append(Paragraph("<b>Audio de la demande :</b> Présent (non inclus dans le PDF)", styles['Normal']))
        story.append(Spacer(1, 12))

    story.append(Paragraph("<b>Messages :</b>", styles['Heading2']))
    messages = Message.query.filter_by(request_id=req.id).order_by(Message.sent_at.asc()).all()
    if messages:
        for msg in messages:
            sender = msg.sender.name
            sent_at = msg.sent_at.strftime('%Y-%m-%d %H:%M:%S')
            content = msg.content or "(Aucun texte)"
            audio = "Message audio présent (non inclus dans le PDF)" if msg.audio_path else "Aucun audio"
            story.append(Paragraph(f"<b>{sender} ({sent_at}) :</b>", styles['Normal']))
            story.append(Paragraph(f"Texte : {content}", styles['Normal']))
            story.append(Paragraph(f"Audio : {audio}", styles['Normal']))
            story.append(Spacer(1, 6))
    else:
        story.append(Paragraph("Aucun message.", styles['Normal']))

    doc.build(story)
    return send_from_directory(app.config['PDF_FOLDER'], filename, as_attachment=True)



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)