import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.utils import secure_filename
from config import Config


os.makedirs(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance'), exist_ok=True)
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)





os.makedirs('instance', exist_ok=True)
os.makedirs('static/uploads', exist_ok=True)

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'

# --- Модели ---
class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(120))

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'))
    service = db.relationship('Service')

class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

# --- Логин-менеджер ---
@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

# --- Главная страница ---
@app.route('/')
def index():
    services = Service.query.all()
    return render_template('index.html', services=services)

# --- Форма записи ---
@app.route('/booking', methods=['GET', 'POST'])
def booking():
    services = Service.query.all()
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        date = request.form['date']
        service_id = request.form['service']
        booking = Booking(name=name, phone=phone, date=date, service_id=service_id)
        db.session.add(booking)
        db.session.commit()
        flash('Вы успешно записались!', 'success')
        return redirect(url_for('index'))
    return render_template('booking.html', services=services)

# --- Админ-панель ---
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username).first()
        if admin and admin.password == password:
            login_user(admin)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Неверные данные!', 'danger')
    return render_template('admin/login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('admin_login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/admin/services', methods=['GET', 'POST'])
@login_required
def admin_services():
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        image = request.files['image']
        filename = None
        if image and image.filename != '':
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        service = Service(name=name, price=price, image=filename)
        db.session.add(service)
        db.session.commit()
        flash('Услуга добавлена!', 'success')
        return redirect(url_for('admin_services'))
    services = Service.query.all()
    return render_template('admin/services.html', services=services)

@app.route('/admin/services/delete/<int:id>')
@login_required
def delete_service(id):
    service = Service.query.get_or_404(id)
    db.session.delete(service)
    db.session.commit()
    flash('Услуга удалена!', 'success')
    return redirect(url_for('admin_services'))

@app.route('/admin/bookings')
@login_required
def admin_bookings():
    bookings = Booking.query.order_by(Booking.date.desc()).all()
    return render_template('admin/bookings.html', bookings=bookings)

# --- Загрузка изображений ---
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- Инициализация базы данных ---
def create_tables():
    db.create_all()
    if not Admin.query.filter_by(username='admin').first():
        admin = Admin(username='admin', password='admin')
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    # Убедитесь, что папка для загрузки изображений существует
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    with app.app_context():
        create_tables()
    app.run(debug=True)
