from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from models import User
from extensions import db

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/settings')
@login_required
def settings_page():
    users = User.query.all()
    return render_template('settings.html', users=users)

@settings_bp.route('/settings/change-password', methods=['POST'])
@login_required
def change_password():
    from flask_login import current_user
    old_pass = request.form.get('old_password')
    new_pass = request.form.get('new_password')
    confirm = request.form.get('confirm_password')

    if not current_user.check_password(old_pass):
        flash('Current password is incorrect', 'danger')
        return redirect(url_for('settings.settings_page'))

    if new_pass != confirm:
        flash('New passwords do not match', 'danger')
        return redirect(url_for('settings.settings_page'))

    if len(new_pass) < 6:
        flash('Password must be at least 6 characters', 'danger')
        return redirect(url_for('settings.settings_page'))

    current_user.set_password(new_pass)
    db.session.commit()
    flash('Password changed successfully!', 'success')
    return redirect(url_for('settings.settings_page'))
