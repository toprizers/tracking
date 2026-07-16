import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'employee-monitor-secret-key-change-this')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///employee_monitor.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    SCREENSHOT_INTERVAL = 1800
    IDLE_THRESHOLD = 900
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
