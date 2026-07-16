from flask import Blueprint, render_template, jsonify, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Employee, Screenshot, Activity, Alert, User
from extensions import db, socketio
from datetime import datetime, timedelta
import secrets

employees_bp = Blueprint('employees', __name__)

@employees_bp.route('/')
@login_required
def dashboard():
    employees = Employee.query.all()
    total_employees = len(employees)
    active_employees = Employee.query.filter_by(status='active').count()
    recent_alerts = Alert.query.filter_by(is_read=False).order_by(Alert.created_at.desc()).limit(10).all()
    total_alerts = Alert.query.filter_by(is_read=False).count()

    latest_screenshots = Screenshot.query.order_by(Screenshot.captured_at.desc()).limit(8).all()

    return render_template('dashboard.html',
        employees=employees,
        total_employees=total_employees,
        active_employees=active_employees,
        recent_alerts=recent_alerts,
        total_alerts=total_alerts,
        latest_screenshots=latest_screenshots
    )

@employees_bp.route('/employees')
@login_required
def employees_list():
    employees = Employee.query.all()
    return render_template('employees.html', employees=employees)

@employees_bp.route('/employee/<int:emp_id>')
@login_required
def employee_detail(emp_id):
    employee = Employee.query.get_or_404(emp_id)
    screenshots = Screenshot.query.filter_by(employee_id=emp_id).order_by(Screenshot.captured_at.desc()).limit(50).all()
    activities = Activity.query.filter_by(employee_id=emp_id).order_by(Activity.recorded_at.desc()).limit(50).all()
    alerts = Alert.query.filter_by(employee_id=emp_id).order_by(Alert.created_at.desc()).limit(20).all()

    return render_template('employee_detail.html',
        employee=employee,
        screenshots=screenshots,
        activities=activities,
        alerts=alerts
    )

@employees_bp.route('/api/employees/add', methods=['POST'])
@login_required
def add_employee():
    name = request.form.get('name')
    email = request.form.get('email')
    department = request.form.get('department', '')

    if not name or not email:
        flash('Name and email are required', 'danger')
        return redirect(url_for('employees.employees_list'))

    if Employee.query.filter_by(email=email).first():
        flash('Employee with this email already exists', 'danger')
        return redirect(url_for('employees.employees_list'))

    agent_key = secrets.token_hex(32)
    emp = Employee(
        name=name,
        email=email,
        department=department,
        agent_key=agent_key,
        consent_given=True,
        consent_date=datetime.utcnow()
    )
    db.session.add(emp)
    db.session.commit()

    flash(f'Employee {name} added successfully!', 'success')
    return redirect(url_for('employees.employees_list'))

@employees_bp.route('/api/employees/<int:emp_id>/edit', methods=['POST'])
@login_required
def edit_employee(emp_id):
    employee = Employee.query.get_or_404(emp_id)
    employee.name = request.form.get('name', employee.name)
    employee.email = request.form.get('email', employee.email)
    employee.department = request.form.get('department', employee.department)
    db.session.commit()
    flash(f'Employee {employee.name} updated!', 'success')
    return redirect(url_for('employees.employee_detail', emp_id=emp_id))

@employees_bp.route('/api/employees/<int:emp_id>/delete', methods=['POST'])
@login_required
def delete_employee(emp_id):
    employee = Employee.query.get_or_404(emp_id)
    name = employee.name
    Screenshot.query.filter_by(employee_id=emp_id).delete()
    Activity.query.filter_by(employee_id=emp_id).delete()
    Alert.query.filter_by(employee_id=emp_id).delete()
    db.session.delete(employee)
    db.session.commit()
    flash(f'Employee {name} deleted!', 'success')
    return redirect(url_for('employees.employees_list'))

@employees_bp.route('/api/employees/<int:emp_id>/regenerate-key', methods=['POST'])
@login_required
def regenerate_key(emp_id):
    employee = Employee.query.get_or_404(emp_id)
    employee.agent_key = secrets.token_hex(32)
    db.session.commit()
    flash('Agent key regenerated!', 'success')
    return redirect(url_for('employees.employee_detail', emp_id=emp_id))

@employees_bp.route('/api/dashboard-data')
@login_required
def dashboard_data():
    employees = Employee.query.all()
    emp_data = []
    for emp in employees:
        latest_activity = Activity.query.filter_by(employee_id=emp.id).order_by(Activity.recorded_at.desc()).first()
        emp_data.append({
            'id': emp.id,
            'name': emp.name,
            'status': emp.status,
            'last_activity': latest_activity.recorded_at.isoformat() if latest_activity else None,
            'idle_time': latest_activity.idle_time if latest_activity else 0
        })

    return jsonify({
        'employees': emp_data,
        'total': len(employees),
        'active': Employee.query.filter_by(status='active').count(),
        'alerts': Alert.query.filter_by(is_read=False).count()
    })
