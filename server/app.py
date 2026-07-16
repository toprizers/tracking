from flask import Flask
from extensions import db, socketio, login_manager
from config import Config

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return User.query.get(int(user_id))

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    from routes.auth import auth_bp
    from routes.employees import employees_bp
    from routes.screenshots import screenshots_bp
    from routes.alerts import alerts_bp
    from routes.agent_api import agent_bp
    from routes.reports import reports_bp
    from routes.settings import settings_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(employees_bp)
    app.register_blueprint(screenshots_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(agent_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(settings_bp)

    import os
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    with app.app_context():
        db.create_all()
        _create_defaults()

    return app

def _create_defaults():
    from models import User
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', role='admin')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("[OK] Default admin created -> admin / admin123")

if __name__ == '__main__':
    app = create_app()
    socketio.run(app, host='127.0.0.1', port=5000, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)
