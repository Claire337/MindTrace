from flask import render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app.mood import mood_bp
from app import db
from app.models import MoodEntry
from app.nlp.analyser import analyse_entry
from datetime import datetime, date
from sqlalchemy import desc

@mood_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_entry():
    """新建打卡"""
    if request.method == 'POST':
        entry_date_str = request.form.get('date', '')
        mood_type = request.form.get('mood_type', '')
        intensity = request.form.get('intensity', '')
        journal_text = request.form.get('journal_text', '')
        # 收集所有勾选的 tag（含自定义）
        selected_tags = request.form.getlist('tags')
        custom_tag = request.form.get('custom_tag', '').strip()
        if custom_tag:
            selected_tags.append(custom_tag)
        tags = ', '.join(t.strip() for t in selected_tags if t.strip())
        
        # 验证
        if not all([entry_date_str, mood_type, intensity, journal_text]):
            flash('Please fill in all required fields', 'error')
            return redirect(url_for('mood.new_entry'))
        
        try:
            entry_date = datetime.strptime(entry_date_str, '%Y-%m-%d').date()
            intensity = int(intensity)
            
            if intensity < 1 or intensity > 10:
                flash('Intensity must be between 1 and 10', 'error')
                return redirect(url_for('mood.new_entry'))
            
            # 检查当天是否已有记录
            existing = MoodEntry.query.filter_by(
                user_id=current_user.id,
                date=entry_date
            ).first()
            
            if existing:
                flash('You already have an entry for this date. Would you like to edit it?', 'warning')
                return redirect(url_for('mood.edit_entry', entry_id=existing.id))
            
            # 创建新记录
            mood_entry = MoodEntry(
                user_id=current_user.id,
                date=entry_date,
                mood_type=mood_type,
                intensity=intensity,
                journal_text=journal_text,
                tags=tags
            )
            
            db.session.add(mood_entry)
            db.session.commit()
            
            # 执行 NLP 分析
            try:
                analyse_entry(mood_entry)
                db.session.commit()
            except Exception as e:
                print(f"NLP analysis error: {e}")
                # 分析失败不影响记录保存
            
            flash('Mood entry saved successfully!', 'success')
            return redirect(url_for('mood.view_entry', entry_id=mood_entry.id))
            
        except ValueError:
            flash('Invalid date format', 'error')
            return redirect(url_for('mood.new_entry'))
    
    return render_template('mood/checkin.html', today_date=date.today().isoformat())

@mood_bp.route('/history')
@login_required
def history():
    """查看历史"""
    # 分页
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # 过滤条件
    mood_filter = request.args.get('mood', '')
    
    query = MoodEntry.query.filter_by(user_id=current_user.id)
    
    if mood_filter:
        query = query.filter_by(mood_type=mood_filter)
    
    # 按日期倒序
    query = query.order_by(desc(MoodEntry.date))
    
    # 分页
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    entries = pagination.items
    
    # 获取所有心情类型（用于过滤）
    all_moods = MoodEntry.query.filter_by(user_id=current_user.id).distinct(MoodEntry.mood_type).all()
    mood_types = list(set([e.mood_type for e in all_moods]))
    
    return render_template('mood/history.html',
                         entries=entries,
                         pagination=pagination,
                         current_mood_filter=mood_filter,
                         mood_types=sorted(mood_types))

@mood_bp.route('/<int:entry_id>')
@login_required
def view_entry(entry_id):
    """查看单条记录"""
    entry = MoodEntry.query.get_or_404(entry_id)
    
    # 验证所有权
    if entry.user_id != current_user.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('mood.history'))
    
    return render_template('mood/detail.html', entry=entry)

@mood_bp.route('/<int:entry_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_entry(entry_id):
    """编辑记录"""
    entry = MoodEntry.query.get_or_404(entry_id)
    
    # 验证所有权
    if entry.user_id != current_user.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('mood.history'))
    
    if request.method == 'POST':
        mood_type = request.form.get('mood_type', '')
        intensity = request.form.get('intensity', '')
        journal_text = request.form.get('journal_text', '')
        selected_tags = request.form.getlist('tags')
        custom_tag = request.form.get('custom_tag', '').strip()
        if custom_tag:
            selected_tags.append(custom_tag)
        tags = ', '.join(t.strip() for t in selected_tags if t.strip())
        
        if not all([mood_type, intensity, journal_text]):
            flash('Please fill in all required fields', 'error')
            return redirect(url_for('mood.edit_entry', entry_id=entry_id))
        
        try:
            intensity = int(intensity)
            if intensity < 1 or intensity > 10:
                raise ValueError('Intensity out of range')
            
            entry.mood_type = mood_type
            entry.intensity = intensity
            entry.journal_text = journal_text
            entry.tags = tags
            entry.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            # 重新执行 NLP 分析
            try:
                analyse_entry(entry)
                db.session.commit()
            except Exception as e:
                print(f"NLP analysis error: {e}")
            
            flash('Entry updated successfully!', 'success')
            return redirect(url_for('mood.view_entry', entry_id=entry_id))
            
        except ValueError:
            flash('Invalid input', 'error')
            return redirect(url_for('mood.edit_entry', entry_id=entry_id))
    
    return render_template('mood/edit.html', entry=entry)

@mood_bp.route('/<int:entry_id>/delete', methods=['POST'])
@login_required
def delete_entry(entry_id):
    """删除记录"""
    entry = MoodEntry.query.get_or_404(entry_id)
    
    # 验证所有权
    if entry.user_id != current_user.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('mood.history'))
    
    db.session.delete(entry)
    db.session.commit()
    
    flash('Entry deleted successfully!', 'success')
    return redirect(url_for('mood.history'))
