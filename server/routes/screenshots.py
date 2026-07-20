from flask import Blueprint, render_template, send_from_directory, jsonify, request
from flask_login import login_required
from models import Screenshot, Employee
from config import Config
import os

screenshots_bp = Blueprint('screenshots', __name__)

@screenshots_bp.route('/screenshots')
@login_required
def screenshots_page():
    try:
        page = int(request.args.get('page', 1))
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1
    per_page = 20
    screenshots = Screenshot.query.order_by(Screenshot.captured_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    employees = Employee.query.all()
    return render_template('screenshots.html', screenshots=screenshots, employees=employees)

@screenshots_bp.route('/uploads/<path:filename>')
@login_required
def uploaded_file(filename):
    return send_from_directory(Config.UPLOAD_FOLDER, filename)

@screenshots_bp.route('/api/screenshots/<int:emp_id>')
@login_required
def employee_screenshots(emp_id):
    screenshots = Screenshot.query.filter_by(employee_id=emp_id).order_by(
        Screenshot.captured_at.desc()
    ).limit(100).all()

    return jsonify([{
        'id': s.id,
        'filename': s.filename,
        'filepath': s.filepath,
        'captured_at': s.captured_at.isoformat(),
        'employee_id': s.employee_id
    } for s in screenshots])
