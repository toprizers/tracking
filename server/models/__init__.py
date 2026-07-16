from extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default='admin')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Employee(db.Model):
    __tablename__ = 'employees'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    department = db.Column(db.String(50))
    laptop_id = db.Column(db.String(50), unique=True)
    status = db.Column(db.String(20), default='offline')
    agent_key = db.Column(db.String(64), unique=True, nullable=False)
    consent_given = db.Column(db.Boolean, default=False)
    consent_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    screenshots = db.relationship('Screenshot', backref='employee', lazy=True)
    activities = db.relationship('Activity', backref='employee', lazy=True)
    alerts = db.relationship('Alert', backref='employee', lazy=True)

class Screenshot(db.Model):
    __tablename__ = 'screenshots'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)
    thumbnail = db.Column(db.String(500))
    captured_at = db.Column(db.DateTime, server_default=db.func.now())
    uploaded_at = db.Column(db.DateTime, server_default=db.func.now())

class Activity(db.Model):
    __tablename__ = 'activities'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text)
    mouse_clicks = db.Column(db.Integer, default=0)
    keystrokes = db.Column(db.Integer, default=0)
    mouse_movement = db.Column(db.Float, default=0.0)
    idle_time = db.Column(db.Integer, default=0)
    active_window = db.Column(db.String(255))
    recorded_at = db.Column(db.DateTime, server_default=db.func.now())

class Alert(db.Model):
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)
    message = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), default='warning')
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
