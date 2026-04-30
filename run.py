import os
from app import create_app
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# 创建应用
config_name = os.getenv('FLASK_ENV', 'development')
app = create_app(config_name)

if __name__ == '__main__':
    # use_reloader=True 会导致页面加载延迟（Flask 文件监控）
    # 如果想快速加载，改为 use_reloader=False
    app.run(
    debug=app.config['DEBUG'],
    host='0.0.0.0',
    port=int(os.environ.get('PORT', 5000)),
    use_reloader=False
    )
