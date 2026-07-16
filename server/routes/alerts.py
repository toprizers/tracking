from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from models import Alert, Employee
from extensions import db, socketio

alerts_bp = Blueprint('alerts', __name__)

@alerts_bp.route('/alerts')
@login_required
def alerts_page():
    alerts = Alert.query.order_by(Alert.created_at.desc()).limit(100).all()
    return render_template('alerts.html', alerts=alerts)

@alerts_bp.route('/api/alerts', methods=['GET'])
@login_required
def get_alerts():
    alerts = Alert.query.order_by(Alert.created_at.desc()).limit(50).all()
    return jsonify([{
        'id': a.id,
        'employee_id': a.employee_id,
        'employee_name': a.employee.name,
        'type': a.alert_type,
        'message': a.message,
        'severity': a.severity,
        'is_read': a.is_read,
        'created_at': a.created_at.isoformat()
    } for a in alerts])

@alerts_bp.route('/api/alerts/<int:alert_id>/read', methods=['POST'])
@login_required
def mark_read(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    alert.is_read = True
    db.session.commit()
    return jsonify({'status': 'ok'})

@alerts_bp.route('/api/alerts/read-all', methods=['POST'])
@login_required
def mark_all_read():
    Alert.query.filter_by(is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'status': 'ok'})
