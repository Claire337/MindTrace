from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_babel import Babel, gettext
from config import config
import os

# 加载 .env 文件（优先使用 python-dotenv，否则手动解析）
def _load_dotenv(path='.env'):
    try:
        from dotenv import load_dotenv
        load_dotenv(path)
    except ImportError:
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        os.environ.setdefault(k.strip(), v.strip())

_load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

db = SQLAlchemy()
login_manager = LoginManager()
babel = Babel()


def create_app(config_name='development'):
    """应用工厂"""
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    db.init_app(app)
    login_manager.init_app(app)
    
    # 配置 Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = gettext('Please log in to access this page.')
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return db.session.get(User, int(user_id))
    
    # 固定使用英文
    def get_locale():
        return 'en'
    
    babel.init_app(app, locale_selector=get_locale)
    
    # 在 Jinja2 模板上下文中注册 get_locale 函数
    @app.context_processor
    def inject_get_locale():
        return {'get_locale': get_locale}
    
    # 注册 Blueprint
    from app.auth import auth_bp
    from app.mood import mood_bp
    from app.insights import insights_bp
    from app.tools import tools_bp
    from app.main import main_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(mood_bp)
    app.register_blueprint(insights_bp)
    app.register_blueprint(tools_bp)
    app.register_blueprint(main_bp)

    # 根路由重定向
    from flask import redirect, url_for as _url_for
    from flask_login import current_user as _current_user

    @app.route('/')
    def index():
        if _current_user.is_authenticated:
            return redirect(_url_for('main.dashboard'))
        return redirect(_url_for('auth.login'))
    
    # 创建表
    with app.app_context():
        db.create_all()
    
    return app
