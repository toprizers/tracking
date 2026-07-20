from flask import Blueprint, request, jsonify, current_app
from models import Employee, Screenshot, Activity, Alert
from extensions import db, socketio
from datetime import datetime, timedelta
import os
import uuid

agent_bp = Blueprint('agent', __name__)

def verify_agent(key):
    employee = Employee.query.filter_by(agent_key=key).first()
    if not employee:
        return None
    employee.status = 'active'
    db.session.commit()
    return employee

@agent_bp.route('/api/agent/heartbeat', methods=['POST'])
def heartbeat():
    data = request.json
    key = data.get('agent_key')
    employee = verify_agent(key)
    if not employee:
        return jsonify({'error': 'Invalid key'}), 401

    employee.status = 'active'
    db.session.commit()

    socketio.emit('agent_heartbeat', {
        'employee_id': employee.id,
        'employee_name': employee.name,
        'timestamp': datetime.utcnow().isoformat()
    })

    return jsonify({'status': 'ok'})

@agent_bp.route('/api/agent/screenshot', methods=['POST'])
def upload_screenshot():
    key = request.form.get('agent_key')
    employee = verify_agent(key)
    if not employee:
        return jsonify({'error': 'Invalid key'}), 401

    if 'screenshot' not in request.files:
        return jsonify({'error': 'No screenshot'}), 400

    file = request.files['screenshot']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    filename = f"{employee.id}_{timestamp}_{uuid.uuid4().hex[:8]}.png"
    employee_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], str(employee.id))
    os.makedirs(employee_folder, exist_ok=True)
    filepath = os.path.join(employee_folder, filename)
    file.save(filepath)

    screenshot = Screenshot(
        employee_id=employee.id,
        filename=filename,
        filepath=f"{employee.id}/{filename}",
        captured_at=datetime.utcnow()
    )
    db.session.add(screenshot)
    db.session.commit()

    socketio.emit('new_screenshot', {
        'employee_id': employee.id,
        'employee_name': employee.name,
        'filename': filename,
        'filepath': f"{employee.id}/{filename}",
        'timestamp': datetime.utcnow().isoformat()
    })

    return jsonify({'status': 'ok', 'filename': filename})

@agent_bp.route('/api/agent/activity', methods=['POST'])
def report_activity():
    data = request.json
    key = data.get('agent_key')
    employee = verify_agent(key)
    if not employee:
        return jsonify({'error': 'Invalid key'}), 401

    activity = Activity(
        employee_id=employee.id,
        activity_type=data.get('type', 'general'),
        details=data.get('details'),
        mouse_clicks=data.get('mouse_clicks', 0),
        keystrokes=data.get('keystrokes', 0),
        mouse_movement=data.get('mouse_movement', 0.0),
        idle_time=data.get('idle_time', 0),
        active_window=data.get('active_window'),
        recorded_at=datetime.utcnow()
    )
    db.session.add(activity)

    idle_time = data.get('idle_time', 0)
    if idle_time >= 900:
        existing_alert = Alert.query.filter_by(
            employee_id=employee.id,
            alert_type='idle'
        ).filter(
            Alert.created_at >= datetime.utcnow() - timedelta(minutes=30)
        ).first()

        if not existing_alert:
            alert = Alert(
                employee_id=employee.id,
                alert_type='idle',
                message=f"{employee.name} has been idle for {idle_time // 60} minutes",
                severity='warning'
            )
            db.session.add(alert)
            socketio.emit('new_alert', {
                'employee_id': employee.id,
                'employee_name': employee.name,
                'type': 'idle',
                'message': alert.message,
                'severity': 'warning',
                'timestamp': datetime.utcnow().isoformat()
            })

    db.session.commit()
    return jsonify({'status': 'ok'})

@agent_bp.route('/api/agent/input-status', methods=['POST'])
def report_input_status():
    data = request.json
    key = data.get('agent_key')
    employee = verify_agent(key)
    if not employee:
        return jsonify({'error': 'Invalid key'}), 401

    mouse_works = data.get('mouse_works', True)
    keyboard_works = data.get('keyboard_works', True)

    if not mouse_works or not keyboard_works:
        failed_devices = []
        if not mouse_works:
            failed_devices.append("mouse")
        if not keyboard_works:
            failed_devices.append("keyboard")

        for device in failed_devices:
            existing = Alert.query.filter_by(
                employee_id=employee.id,
                alert_type='input_failure',
                message=f"{employee.name}'s {device} is not responding!"
            ).filter(
                Alert.created_at >= datetime.utcnow() - timedelta(minutes=30)
            ).first()

            if not existing:
                alert = Alert(
                    employee_id=employee.id,
                    alert_type='input_failure',
                    message=f"{employee.name}'s {device} is not responding!",
                    severity='critical'
                )
                db.session.add(alert)
                db.session.commit()

                socketio.emit('new_alert', {
                    'employee_id': employee.id,
                    'employee_name': employee.name,
                    'type': 'input_failure',
                    'message': alert.message,
                    'severity': 'critical',
                    'timestamp': datetime.utcnow().isoformat()
                })

    return jsonify({'status': 'ok'})

@agent_bp.route('/api/agent/status', methods=['POST'])
def report_status():
    data = request.json
    key = data.get('agent_key')
    employee = verify_agent(key)
    if not employee:
        return jsonify({'error': 'Invalid key'}), 401

    employee.status = data.get('status', 'active')
    db.session.commit()
    return jsonify({'status': 'ok'})
