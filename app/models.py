from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json

class User(UserMixin, db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    language = db.Column(db.String(5), default='en')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 关系
    mood_entries = db.relationship('MoodEntry', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    ai_insights = db.relationship('AIInsight', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """加密密码"""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class MoodEntry(db.Model):
    """情绪记录模型"""
    __tablename__ = 'mood_entries'
    __table_args__ = (db.UniqueConstraint('user_id', 'date', name='uq_user_date'),)
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True)
    mood_type = db.Column(db.String(20), nullable=False)  # happy/calm/anxious/sad/angry/neutral
    intensity = db.Column(db.Integer, nullable=False)  # 1-10
    journal_text = db.Column(db.Text)
    tags = db.Column(db.String(200))  # 逗号分隔
    
    # NLP 分析结果
    sentiment_label = db.Column(db.String(20))  # Positive/Neutral/Negative
    sentiment_polarity = db.Column(db.Float)
    emotion_labels = db.Column(db.Text)  # JSON 数组
    keywords = db.Column(db.Text)  # JSON 数组
    nlp_summary = db.Column(db.String(300))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    ai_insights = db.relationship('AIInsight', backref='entry', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_emotion_labels(self):
        """返回解析后的情绪标签列表"""
        if self.emotion_labels:
            return json.loads(self.emotion_labels)
        return []
    
    def set_emotion_labels(self, labels):
        """存储情绪标签列表"""
        self.emotion_labels = json.dumps(labels)
    
    def get_keywords(self):
        """返回解析后的关键词列表"""
        if self.keywords:
            return json.loads(self.keywords)
        return []
    
    def set_keywords(self, kws):
        """存储关键词列表"""
        self.keywords = json.dumps(kws)
    
    def __repr__(self):
        return f'<MoodEntry {self.date} {self.mood_type}>'


class AIInsight(db.Model):
    """AI 洞察模型"""
    __tablename__ = 'ai_insights'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    entry_id = db.Column(db.Integer, db.ForeignKey('mood_entries.id'), nullable=True)
    insight_type = db.Column(db.String(20), nullable=False)  # daily / weekly
    content = db.Column(db.Text, nullable=False)
    suggestions = db.Column(db.Text)  # JSON 数组
    small_task = db.Column(db.String(300))
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_suggestions(self):
        """返回解析后的建议列表"""
        if self.suggestions:
            return json.loads(self.suggestions)
        return []
    
    def set_suggestions(self, sugg):
        """存储建议列表"""
        self.suggestions = json.dumps(sugg)
    
    def __repr__(self):
        return f'<AIInsight {self.insight_type} {self.user_id}>'
