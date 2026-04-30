from flask import render_template, redirect, url_for, request, session, flash
from flask_login import login_required, current_user
from app.main import main_bp
from app import db
from app.models import User, MoodEntry
from datetime import datetime, timedelta
from sqlalchemy import desc
from werkzeug.security import check_password_hash, generate_password_hash

@main_bp.route('/')
def index():
    """首页"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """仪表盘 — 传递统计数据给模板"""
    # 最近 5 条记录
    recent_entries = MoodEntry.query.filter_by(user_id=current_user.id)\
        .order_by(desc(MoodEntry.date)).limit(5).all()

    # 总记录数
    total_entries = MoodEntry.query.filter_by(user_id=current_user.id).count()

    # 本周记录数
    week_start = (datetime.utcnow() - timedelta(days=7)).date()
    week_entries = MoodEntry.query.filter(
        MoodEntry.user_id == current_user.id,
        MoodEntry.date >= week_start
    ).count()

    # 最近一条记录的情绪
    latest_entry = recent_entries[0] if recent_entries else None

    # 今天是否已打卡
    today = datetime.utcnow().date()
    today_entry = MoodEntry.query.filter_by(
        user_id=current_user.id, date=today
    ).first()

    return render_template('main/dashboard.html',
                           recent_entries=recent_entries,
                           total_entries=total_entries,
                           week_entries=week_entries,
                           latest_entry=latest_entry,
                           today_entry=today_entry)

@main_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """用户设置（含修改密码）"""
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'change_password':
            current_pw = request.form.get('current_password', '')
            new_pw = request.form.get('new_password', '')
            confirm_pw = request.form.get('confirm_password', '')

            if not check_password_hash(current_user.password_hash, current_pw):
                flash('Current password is incorrect.', 'error')
            elif len(new_pw) < 8:
                flash('New password must be at least 8 characters.', 'error')
            elif new_pw != confirm_pw:
                flash('New passwords do not match.', 'error')
            else:
                current_user.password_hash = generate_password_hash(new_pw)
                db.session.commit()
                flash('Password updated successfully!', 'success')

        elif action == 'change_username':
            new_username = request.form.get('username', '').strip()
            if len(new_username) < 2:
                flash('Username must be at least 2 characters.', 'error')
            else:
                current_user.username = new_username
                db.session.commit()
                flash('Username updated successfully!', 'success')

        return redirect(url_for('main.settings'))

    return render_template('main/settings.html')


