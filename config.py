import os
from datetime import timedelta

class Config:
    """基础配置"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Babel 配置
    BABEL_DEFAULT_LOCALE = 'en'
    BABEL_TRANSLATION_DIRECTORIES = 'translations'
    LANGUAGES = {'en': 'English', 'zh': '中文'}
    
    # Session 配置
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    
    # LLM 配置
    LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'openai')  # 供应商：openai, deepseek, gemini 等
    LLM_API_KEY = os.getenv('LLM_API_KEY', '')
    LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-3.5-turbo')
    LLM_BASE_URL = os.getenv('LLM_BASE_URL', 'https://api.openai.com/v1')  # 可用于兼容接口


class DevelopmentConfig(Config):
    """开发配置"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///mindtrace_dev.db'
    WTF_CSRF_ENABLED = True


class ProductionConfig(Config):
    """生产配置（Demo 演示用）"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///mindtrace.db'


class TestingConfig(Config):
    """测试配置"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


# 环境切换
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
