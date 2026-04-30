from flask import render_template
from flask_login import login_required
from app.tools import tools_bp

@tools_bp.route('/')
@login_required
def index():
    """工具箱首页"""
    return render_template('tools/index.html')

@tools_bp.route('/breathing')
@login_required
def breathing():
    """呼吸训练"""
    return render_template('tools/breathing.html')

@tools_bp.route('/firstaid')
@login_required
def firstaid():
    """情绪急救卡"""
    return render_template('tools/firstaid.html')
