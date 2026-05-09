from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps
import os

app = Flask(__name__)
app.secret_key = 'feedback_secret_key_2024'

# ─── DATABASE CONFIG ──────────────────────────────────────────────────────────
# To use MySQL, install PyMySQL:  pip install pymysql
# Then set USE_MYSQL = True and fill in your credentials below.
#
# MySQL setup in MySQL Workbench / CLI:
#   CREATE DATABASE feedbackiq CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
#   CREATE USER 'feedbackuser'@'localhost' IDENTIFIED BY 'yourpassword';
#   GRANT ALL PRIVILEGES ON feedbackiq.* TO 'feedbackuser'@'localhost';
#   FLUSH PRIVILEGES;

USE_MYSQL = True   # ← Set to True to switch to MySQL

if USE_MYSQL:
    MYSQL_USER     = 'root'
    MYSQL_PASSWORD = 'Danny%402005'
    MYSQL_HOST     = 'localhost'
    MYSQL_PORT     = '3306'
    MYSQL_DB       = 'feedbackiq'
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}'
    )
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///feedback.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
analyzer = SentimentIntensityAnalyzer()

# ─── Models ───────────────────────────────────────────────────────────────────

class User(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    name      = db.Column(db.String(100), nullable=False)
    email     = db.Column(db.String(120), unique=True, nullable=False)
    password  = db.Column(db.String(200), nullable=False)
    role      = db.Column(db.String(20), default='user')  # 'user' | 'admin'
    feedbacks = db.relationship('Feedback', backref='author', lazy=True)

class Feedback(db.Model):
    id        = db.Column(db.Integer, primary_key=True)
    user_id   = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    message   = db.Column(db.Text, nullable=False)
    sentiment = db.Column(db.String(20), nullable=False)
    score     = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# ─── Helpers ──────────────────────────────────────────────────────────────────

def analyze_sentiment(text):
    scores = analyzer.polarity_scores(text)
    compound = scores['compound']
    if compound >= 0.05:
        label = 'Positive'
    elif compound <= -0.05:
        label = 'Negative'
    else:
        label = 'Neutral'
    return label, round(compound, 4)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login required'}), 401
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'admin':
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated

# ─── Page Routes ──────────────────────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/admin')
def admin_page():
    if session.get('role') != 'admin':
        return redirect('/')
    return render_template('admin.html')

# ─── Auth API ─────────────────────────────────────────────────────────────────

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data or not all(k in data for k in ('name', 'email', 'password')):
        return jsonify({'error': 'Missing fields'}), 400
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409
    user = User(
        name=data['name'],
        email=data['email'],
        password=generate_password_hash(data['password']),
        role='admin' if data['email'] == 'admin@feedback.com' else 'user'
    )
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'Registered successfully', 'role': user.role}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()
    if not user or not check_password_hash(user.password, data.get('password', '')):
        return jsonify({'error': 'Invalid credentials'}), 401
    session['user_id'] = user.id
    session['user_name'] = user.name
    session['role'] = user.role
    return jsonify({'message': 'Login successful', 'name': user.name, 'role': user.role})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out'})

@app.route('/api/me')
def me():
    if 'user_id' in session:
        return jsonify({'logged_in': True, 'name': session['user_name'], 'role': session['role']})
    return jsonify({'logged_in': False})

# ─── Feedback API ─────────────────────────────────────────────────────────────

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    data = request.get_json()
    if not data or not data.get('message', '').strip():
        return jsonify({'error': 'Message is required'}), 400
    label, score = analyze_sentiment(data['message'])
    fb = Feedback(
        user_id=session.get('user_id'),
        message=data['message'].strip(),
        sentiment=label,
        score=score
    )
    db.session.add(fb)
    db.session.commit()
    return jsonify({'sentiment': label, 'score': score, 'id': fb.id}), 201

@app.route('/api/my-feedback')
@login_required
def my_feedback():
    feedbacks = Feedback.query.filter_by(user_id=session['user_id'])\
                              .order_by(Feedback.timestamp.desc()).all()
    return jsonify([{
        'id': f.id, 'message': f.message,
        'sentiment': f.sentiment, 'score': f.score,
        'timestamp': f.timestamp.strftime('%Y-%m-%d %H:%M')
    } for f in feedbacks])

@app.route('/api/summary')
def summary():
    total    = Feedback.query.count()
    positive = Feedback.query.filter_by(sentiment='Positive').count()
    negative = Feedback.query.filter_by(sentiment='Negative').count()
    neutral  = Feedback.query.filter_by(sentiment='Neutral').count()

    # Last 7 days trend
    from sqlalchemy import func, cast, Date
    daily = db.session.query(
        cast(Feedback.timestamp, Date).label('day'),
        Feedback.sentiment,
        func.count().label('cnt')
    ).group_by('day', Feedback.sentiment).order_by('day').all()

    trend = {}
    for row in daily:
        day_str = str(row.day)
        if day_str not in trend:
            trend[day_str] = {'Positive': 0, 'Negative': 0, 'Neutral': 0}
        trend[day_str][row.sentiment] = row.cnt

    return jsonify({
        'total': total,
        'positive': positive,
        'negative': negative,
        'neutral': neutral,
        'trend': trend
    })

@app.route('/api/admin/all-feedback')
@login_required
@admin_required
def all_feedback():
    feedbacks = Feedback.query.order_by(Feedback.timestamp.desc()).all()
    return jsonify([{
        'id': f.id,
        'user': f.author.name if f.author else 'Guest',
        'message': f.message,
        'sentiment': f.sentiment,
        'score': f.score,
        'timestamp': f.timestamp.strftime('%Y-%m-%d %H:%M')
    } for f in feedbacks])

@app.route('/api/admin/delete/<int:fid>', methods=['DELETE'])
@login_required
@admin_required
def delete_feedback(fid):
    fb = Feedback.query.get_or_404(fid)
    db.session.delete(fb)
    db.session.commit()
    return jsonify({'message': 'Deleted'})

# ─── Init ─────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Seed admin if not exists
        if not User.query.filter_by(email='admin@feedback.com').first():
            admin = User(name='Admin', email='admin@feedback.com',
                         password=generate_password_hash('admin123'), role='admin')
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin seeded: admin@feedback.com / admin123")
    app.run(debug=True, port=5000)
