#!/usr/bin/env python
"""
MindTrace 假数据生成脚本
运行: python seed.py
"""

from app import create_app, db
from app.models import User, MoodEntry, AIInsight
from app.nlp.analyser import analyse
from datetime import datetime, timedelta
import json

app = create_app()

def seed_database():
    """生成演示数据"""
    
    with app.app_context():
        # 清空数据库（可选，开发用）
        print("🗑️  清空现有数据...")
        # 注释掉下面这行可以保留旧数据
        # db.drop_all()
        # db.create_all()
        
        # 1. 创建演示用户
        print("👤 创建演示用户...")
        
        # 检查用户是否已存在
        demo_user = User.query.filter_by(email='demo@mindtrace.app').first()
        if demo_user:
            print("   ℹ️  demo@mindtrace.app 已存在，跳过创建")
        else:
            demo_user = User(
                email='demo@mindtrace.app',
                username='Demo User',
                language='en'
            )
            demo_user.set_password('Demo1234')
            db.session.add(demo_user)
            db.session.commit()
            print("   ✓ 创建成功: demo@mindtrace.app / Demo1234")
        
        # 2. 生成 30 天的情绪记录
        print("\n📝 生成 30 天情绪记录...")
        
        mood_types = ['happy', 'calm', 'anxious', 'sad', 'angry', 'neutral']
        emotion_labels_map = {
            'happy': ['satisfaction'],
            'calm': ['calm'],
            'anxious': ['anxiety', 'stress'],
            'sad': ['sadness', 'loneliness'],
            'angry': ['anger', 'frustration'],
            'neutral': []
        }
        keywords_map = {
            'happy': ['celebration', 'friends', 'achievement'],
            'calm': ['meditation', 'relax', 'peaceful'],
            'anxious': ['exam', 'deadline', 'worry'],
            'sad': ['lonely', 'tired', 'miss'],
            'angry': ['frustrated', 'annoyed', 'conflict'],
            'neutral': ['routine', 'normal', 'usual']
        }
        
        journal_samples = {
            'happy': [
                "Had an amazing day with my friends! We laughed a lot and made great memories.",
                "Just finished a project I was working on. Feeling proud of myself!",
                "Got great news today! Everything is going well.",
                "Spent time with family and felt really connected.",
                "Accomplished something I've been wanting to do for a while."
            ],
            'calm': [
                "Had a peaceful morning meditation. Feeling centered and balanced.",
                "Took a long walk in nature. Very relaxing and rejuvenating.",
                "Spent quiet time reading. Very soothing and peaceful.",
                "Yoga session was wonderful. Feeling grounded.",
                "Everything feels steady today. No major stress or excitement."
            ],
            'anxious': [
                "Have a big presentation coming up. Feeling nervous about it.",
                "Deadlines are piling up. Feeling overwhelmed.",
                "Can't stop thinking about the exam next week.",
                "Worried about making the right decision.",
                "Too many things to do, not enough time."
            ],
            'sad': [
                "Missing someone today. Feeling a bit lonely.",
                "Didn't go well as expected. Feeling disappointed.",
                "Feeling empty and disconnected today.",
                "Not feeling very motivated. Everything seems dull.",
                "Had a disagreement with someone I care about."
            ],
            'angry': [
                "Someone said something hurtful today. Still upset.",
                "Things didn't go my way. Feeling frustrated.",
                "People can be so annoying sometimes.",
                "Feeling irritated by small things today.",
                "Had a conflict and it's bothering me."
            ],
            'neutral': [
                "Just a regular day. Nothing special happened.",
                "Same routine as usual. Going through the motions.",
                "Nothing to complain about, but nothing exciting either.",
                "Normal day at work/school. No major events.",
                "Feeling neutral about everything today."
            ]
        }
        
        # 检查是否已有记录
        existing_count = MoodEntry.query.filter_by(user_id=demo_user.id).count()
        if existing_count > 0:
            print(f"   ℹ️  已有 {existing_count} 条记录，跳过生成")
        else:
            for i in range(30):
                # 生成过去 30 天的日期
                entry_date = datetime.utcnow().date() - timedelta(days=29-i)
                
                # 随机选择情绪类型（偏向某些类型以显示变化）
                import random
                weights = [1, 2, 3, 1, 1, 1]  # 偏向 anxious, calm
                mood_type = random.choices(mood_types, weights=weights)[0]
                
                # 创建记录
                journal_text = random.choice(journal_samples[mood_type])
                mood_entry = MoodEntry(
                    user_id=demo_user.id,
                    date=entry_date,
                    mood_type=mood_type,
                    intensity=random.randint(2, 9),
                    journal_text=journal_text,
                    tags='Academic,Work' if mood_type == 'anxious' else 'Health,Sleep'
                )
                db.session.add(mood_entry)
                db.session.flush()  # 获取 entry_id
                
                # 执行 NLP 分析
                analysis = analyse(f"{mood_type} {journal_text}")
                mood_entry.sentiment_label = analysis['sentiment_label']
                mood_entry.sentiment_polarity = analysis['sentiment_polarity']
                mood_entry.emotion_labels = json.dumps(analysis['emotion_labels'])
                mood_entry.keywords = json.dumps(analysis['keywords'])
                mood_entry.nlp_summary = analysis['nlp_summary']
            
            db.session.commit()
            print(f"   ✓ 生成 30 条情绪记录")
        
        print("\n✅ 演示数据生成完成！\n")
        print("=" * 50)
        print("登录凭证:")
        print(f"  邮箱: demo@mindtrace.app")
        print(f"  密码: Demo1234")
        print("=" * 50)

if __name__ == '__main__':
    seed_database()
