from flask import render_template, redirect, url_for, flash, jsonify, request
from flask_login import login_required, current_user
from app.insights import insights_bp
from app.insights.llm_client import get_llm_client
from app import db
from app.models import MoodEntry, AIInsight
from datetime import datetime, timedelta
from sqlalchemy import desc

@insights_bp.route('/daily/<int:entry_id>')
@login_required
def daily_insight(entry_id):
    """每日洞察"""
    entry = MoodEntry.query.get_or_404(entry_id)
    
    # 验证所有权
    if entry.user_id != current_user.id:
        flash('Unauthorized', 'error')
        return redirect(url_for('mood.history'))
    
    # 查找或创建 AI 洞察
    insight = AIInsight.query.filter_by(
        user_id=current_user.id,
        entry_id=entry_id,
        insight_type='daily'
    ).first()
    
    # 允许 ?refresh=1 强制重新生成
    if insight and request.args.get('refresh') == '1':
        db.session.delete(insight)
        db.session.commit()
        insight = None

    if not insight:
        # 生成新洞察
        llm_client = get_llm_client()
        content = llm_client.generate_daily_insight(entry)
        suggestions = llm_client.generate_suggestions(entry)
        small_task = llm_client.generate_small_task(entry)
        
        insight = AIInsight(
            user_id=current_user.id,
            entry_id=entry_id,
            insight_type='daily',
            content=content,
            small_task=small_task
        )
        insight.set_suggestions(suggestions)
        
        db.session.add(insight)
        db.session.commit()
    
    return render_template('insights/daily.html', entry=entry, insight=insight)

@insights_bp.route('/weekly')
@login_required
def weekly_insight():
    """周期洞察"""
    # 获取过去7天的记录
    seven_days_ago = (datetime.utcnow() - timedelta(days=7)).date()
    entries = MoodEntry.query.filter(
        MoodEntry.user_id == current_user.id,
        MoodEntry.date >= seven_days_ago
    ).order_by(desc(MoodEntry.date)).all()
    
    # 查找或创建周报告
    insight = AIInsight.query.filter_by(
        user_id=current_user.id,
        entry_id=None,
        insight_type='weekly'
    ).first()
    
    # 允许 ?refresh=1 强制重新生成
    if insight and request.args.get('refresh') == '1':
        db.session.delete(insight)
        db.session.commit()
        insight = None

    if not insight:
        # 生成新洞察
        llm_client = get_llm_client()
        content = llm_client.generate_weekly_summary(entries)
        
        insight = AIInsight(
            user_id=current_user.id,
            entry_id=None,
            insight_type='weekly',
            content=content
        )
        
        db.session.add(insight)
        db.session.commit()
    
    return render_template('insights/weekly.html', entries=entries, insight=insight)

@insights_bp.route('/analytics')
@login_required
def analytics():
    """数据可视化"""
    # 获取过去30天的记录
    thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).date()
    entries = MoodEntry.query.filter(
        MoodEntry.user_id == current_user.id,
        MoodEntry.date >= thirty_days_ago
    ).order_by(MoodEntry.date).all()
    
    # 将 SQLAlchemy 对象转为可 JSON 序列化的字典
    entries_json = [
        {
            'date': e.date.strftime('%Y-%m-%d'),
            'mood_type': e.mood_type,
            'intensity': e.intensity,
            'sentiment_label': e.sentiment_label or 'Neutral'
        }
        for e in entries
    ]
    
    return render_template('insights/analytics.html', entries=entries, entries_json=entries_json)
