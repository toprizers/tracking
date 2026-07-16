from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required
from models import Employee, Activity, Screenshot
from extensions import db
from datetime import datetime, timedelta

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports')
@login_required
def reports_page():
    employees = Employee.query.all()
    return render_template('reports.html', employees=employees)

@reports_bp.route('/api/reports/activity/<int:emp_id>')
@login_required
def employee_activity_report(emp_id):
    days = int(request.args.get('days', 7))
    start_date = datetime.utcnow() - timedelta(days=days)

    activities = Activity.query.filter(
        Activity.employee_id == emp_id,
        Activity.recorded_at >= start_date
    ).order_by(Activity.recorded_at.asc()).all()

    daily_data = {}
    for act in activities:
        day = act.recorded_at.strftime('%Y-%m-%d')
        if day not in daily_data:
            daily_data[day] = {'clicks': 0, 'keys': 0, 'idle_minutes': 0, 'active_minutes': 0}
        daily_data[day]['clicks'] += act.mouse_clicks
        daily_data[day]['keys'] += act.keystrokes
        daily_data[day]['idle_minutes'] += act.idle_time // 60
        if act.idle_time < 300:
            daily_data[day]['active_minutes'] += 1

    labels = sorted(daily_data.keys())
    clicks = [daily_data[d]['clicks'] for d in labels]
    keys = [daily_data[d]['keys'] for d in labels]
    idle = [daily_data[d]['idle_minutes'] for d in labels]
    active = [daily_data[d]['active_minutes'] for d in labels]

    return jsonify({
        'labels': labels,
        'clicks': clicks,
        'keystrokes': keys,
        'idle_minutes': idle,
        'active_minutes': active
    })

@reports_bp.route('/api/reports/screenshots/<int:emp_id>')
@login_required
def employee_screenshot_count(emp_id):
    days = int(request.args.get('days', 7))
    start_date = datetime.utcnow() - timedelta(days=days)

    screenshots = Screenshot.query.filter(
        Screenshot.employee_id == emp_id,
        Screenshot.captured_at >= start_date
    ).all()

    daily = {}
    for s in screenshots:
        day = s.captured_at.strftime('%Y-%m-%d')
        daily[day] = daily.get(day, 0) + 1

    labels = sorted(daily.keys())
    counts = [daily[d] for d in labels]

    return jsonify({'labels': labels, 'counts': counts})

@reports_bp.route('/api/reports/summary')
@login_required
def summary_report():
    days = int(request.args.get('days', 7))
    start_date = datetime.utcnow() - timedelta(days=days)
    employees = Employee.query.all()

    summary = []
    for emp in employees:
        act_count = Activity.query.filter(
            Activity.employee_id == emp.id,
            Activity.recorded_at >= start_date
        ).count()
        ss_count = Screenshot.query.filter(
            Screenshot.employee_id == emp.id,
            Screenshot.captured_at >= start_date
        ).count()
        latest = Activity.query.filter_by(employee_id=emp.id).order_by(Activity.recorded_at.desc()).first()

        total_clicks = db.session.query(db.func.sum(Activity.mouse_clicks)).filter(
            Activity.employee_id == emp.id,
            Activity.recorded_at >= start_date
        ).scalar() or 0
        total_keys = db.session.query(db.func.sum(Activity.keystrokes)).filter(
            Activity.employee_id == emp.id,
            Activity.recorded_at >= start_date
        ).scalar() or 0

        summary.append({
            'id': emp.id,
            'name': emp.name,
            'department': emp.department,
            'status': emp.status,
            'activity_count': act_count,
            'screenshot_count': ss_count,
            'total_clicks': total_clicks,
            'total_keys': total_keys,
            'last_active': latest.recorded_at.isoformat() if latest else None
        })

    return jsonify({'summary': summary, 'days': days})
