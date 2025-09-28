from flask import Flask, render_template, request, session, redirect, url_for, jsonify, flash, render_template_string
import json
import os
from werkzeug.utils import secure_filename
from salao_app.models import db, Appointment, Photo
from datetime import datetime

app = Flask(__name__, template_folder='salao_app/templates', static_folder='salao_app/static')
import os.path
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'appointments.db')
os.makedirs(os.path.dirname(db_path), exist_ok=True)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{db_path}').replace('postgres://', 'postgresql://')
app.config['SECRET_KEY'] = 'secret'
db.init_app(app)

with app.app_context():
    # db.drop_all()  # Commented for production to avoid losing data
    db.create_all()

@app.route('/')
def home():
    photos = Photo.query.all()
    content = """<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Salão de Beleza</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <div class="container">
        <h1>Bem-vindo ao Salão Beauty Shalom</h1>
        <p class="description">Agende seu horário conosco!</p>
        <div class="links">
            <a href="/agendar">Agendar Horário</a>
        </div>
        <h2>Nossos Trabalhos</h2>
        <div class="gallery">
            {% for photo in photos %}
            <img src="{{ url_for('static', filename='images/' + photo.filename) }}" alt="{{ photo.description or 'Trabalho do salão' }}">
            {% endfor %}
            {% if not photos %}
            <p>Nenhuma foto adicionada ainda. Volte em breve!</p>
            {% endif %}
        </div>
    </div>
</body>
</html>"""
    return render_template_string(content, photos=photos)

@app.route('/agendar', methods=['GET', 'POST'])
def agendar():
    if request.method == 'POST':
        name = request.form['name']
        service = request.form['service']
        professional = request.form['professional']
        date_str = request.form['date']
        time_str = request.form['time']
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        time = datetime.strptime(time_str, '%H:%M').time()
        # Check availability
        existing = Appointment.query.filter_by(date=date, time=time).first()
        if existing:
            flash('Horário indisponível. Tente outro.')
            return redirect(url_for('agendar'))
        new_appt = Appointment(client_name=name, service=service, professional=professional, date=date, time=time)
        db.session.add(new_appt)
        db.session.commit()
        flash('Agendamento realizado com sucesso!')
        return redirect(url_for('agendar'))
    return render_template('agendar.html')

@app.route('/available_times/<date_str>')
def available_times(date_str):
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'times': []})
    
    all_slots = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00']
    
    booked_times = db.session.query(Appointment.time).filter_by(date=date).all()
    booked_set = {str(t[0])[:5] for t in booked_times}
    
    available = [slot for slot in all_slots if slot not in booked_set]
    
    return jsonify({'times': available})

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'Lucas' and password == 'senha123':
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('login.html', error='Credenciais inválidas!')
    return render_template('login.html')

@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    appointments = Appointment.query.all()
    return render_template('admin.html', appointments=appointments)

@app.route('/admin/gallery', methods=['GET', 'POST'])
def admin_gallery():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            description = request.form.get('description', '')
            if file.filename == '':
                flash('Nenhum arquivo selecionado.')
            else:
                filename = secure_filename(file.filename)
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    os.makedirs('salao_app/static/images', exist_ok=True)
                    filepath = os.path.join('salao_app/static/images', filename)
                    file.save(filepath)
                    new_photo = Photo(filename=filename, description=description)
                    db.session.add(new_photo)
                    db.session.commit()
                    flash('Foto adicionada com sucesso!')
                else:
                    flash('Apenas arquivos PNG, JPG ou JPEG são permitidos.')
    else:
        flash('Nenhum arquivo enviado.')
    photos = Photo.query.all()
    return render_template('admin_gallery.html', photos=photos)

@app.route('/delete_photo/<int:photo_id>', methods=['POST'])
def delete_photo(photo_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    photo = Photo.query.get_or_404(photo_id)
    filepath = os.path.join('salao_app/static/images', photo.filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    db.session.delete(photo)
    db.session.commit()
    flash('Foto deletada com sucesso!')
    return redirect(url_for('admin_gallery'))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

@app.route('/delete/<int:appt_id>', methods=['POST'])
def delete_appointment(appt_id):
    appt = Appointment.query.get_or_404(appt_id)
    db.session.delete(appt)
    db.session.commit()
    flash('Agendamento deletado com sucesso!')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)
