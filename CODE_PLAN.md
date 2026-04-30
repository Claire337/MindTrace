# MindTrace 代码实现计划

---

## 一、项目目录结构

```
17/
├── app/
│   ├── __init__.py              # App Factory，初始化 Flask、数据库、登录、Babel
│   ├── models.py                # 所有数据库模型
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── routes.py            # 注册、登录、退出路由
│   │   └── forms.py             # WTForms 表单定义
│   ├── mood/
│   │   ├── __init__.py
│   │   ├── routes.py            # 打卡、历史、编辑、删除路由
│   │   └── forms.py
│   ├── insights/
│   │   ├── __init__.py
│   │   ├── routes.py            # AI 洞察、分析统计路由
│   │   └── llm_client.py        # LLM API 抽象层
│   ├── tools/
│   │   ├── __init__.py
│   │   └── routes.py            # 呼吸训练、情绪急救卡路由
│   ├── main/
│   │   ├── __init__.py
│   │   └── routes.py            # 仪表盘、首页、设置页路由
│   ├── nlp/
│   │   └── analyser.py          # NLP 分析模块（TextBlob）
│   ├── static/
│   │   ├── css/
│   │   │   └── main.css         # 自定义样式
│   │   └── js/
│   │       ├── charts.js        # Chart.js 图表逻辑
│   │       └── breathing.js     # 呼吸训练动画逻辑
│   ├── templates/
│   │   ├── base.html            # 基础模板（导航栏、页脚）
│   │   ├── auth/
│   │   │   ├── login.html
│   │   │   └── register.html
│   │   ├── mood/
│   │   │   ├── checkin.html     # 打卡页
│   │   │   ├── history.html     # 历史列表页
│   │   │   └── detail.html      # 单条记录详情/编辑页
│   │   ├── insights/
│   │   │   ├── daily.html       # 每日洞察卡片
│   │   │   ├── weekly.html      # 周期规律页
│   │   │   └── analytics.html   # 数据可视化页
│   │   ├── tools/
│   │   │   ├── breathing.html   # 呼吸训练页
│   │   │   └── firstaid.html    # 情绪急救卡页
│   │   └── main/
│   │       ├── dashboard.html   # 仪表盘
│   │       └── settings.html    # 用户设置页
│   └── translations/
│       ├── en/LC_MESSAGES/messages.po
│       └── zh/LC_MESSAGES/messages.po
├── config.py                    # 配置类
├── run.py                       # 启动入口
├── seed.py                      # 假数据生成脚本
├── requirements.txt
└── .env                         # API Key 等敏感配置（不提交 git）
```

---

## 二、数据库模型设计（`app/models.py`）

### User 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer, PK | 主键 |
| email | String(120), unique | 邮箱，用于登录 |
| username | String(80) | 显示名称 |
| password_hash | String(256) | Werkzeug 加密后的密码 |
| language | String(5) | 语言偏好，默认 'en' |
| created_at | DateTime | 注册时间 |

### MoodEntry 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer, PK | 主键 |
| user_id | Integer, FK(User) | 所属用户 |
| date | Date | 记录日期（唯一，一天一条） |
| mood_type | String(20) | 心情类型：happy/calm/anxious/sad/angry/neutral |
| intensity | Integer | 情绪强度 1–10 |
| journal_text | Text | 日记正文 |
| tags | String(200) | 标签，逗号分隔存储 |
| sentiment_label | String(20) | NLP 结果：Positive/Neutral/Negative |
| sentiment_polarity | Float | TextBlob polarity 原始值 |
| emotion_labels | Text | JSON 数组，细分情绪标签 |
| keywords | Text | JSON 数组，提取的关键词 |
| nlp_summary | String(300) | 一句话 NLP 总结 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 最后修改时间 |

### AIInsight 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer, PK | 主键 |
| user_id | Integer, FK(User) | 所属用户 |
| entry_id | Integer, FK(MoodEntry), nullable | 关联的打卡记录（周报告时为空） |
| insight_type | String(20) | 类型：daily / weekly |
| content | Text | LLM 生成的洞察正文 |
| suggestions | Text | JSON 数组，建议列表 |
| small_task | String(300) | 今日小任务建议 |
| generated_at | DateTime | 生成时间 |

---

## 三、各模块实现细节

### 3.1 配置（`config.py`）

定义三个配置类：
- `Config`：基础配置，读取 `.env` 中的 `SECRET_KEY`、`LLM_API_KEY`、`LLM_MODEL` 等
- `DevelopmentConfig`：开发模式，`DEBUG=True`，数据库用本地 SQLite 文件
- `ProductionConfig`：生产模式（Demo 演示用，实际与开发一致）

### 3.2 用户认证（`app/auth/`）

**注册流程：**
1. 表单验证：邮箱格式、密码长度（最少8位）、两次密码一致
2. 检查邮箱是否已存在
3. `generate_password_hash()` 加密密码后存入数据库
4. 注册成功后自动登录，跳转到仪表盘

**登录流程：**
1. 查找邮箱对应用户
2. `check_password_hash()` 验证密码
3. `login_user()` 建立会话，支持"记住我"（30天）
4. 登录后跳转到仪表盘或来源页面

**退出：**`logout_user()` 清除会话，跳转登录页

### 3.3 情绪打卡（`app/mood/`）

**打卡表单字段：**
- 心情类型：6个图标按钮（Happy / Calm / Anxious / Sad / Angry / Neutral），点击高亮选中，值存入隐藏 input
- 情绪强度：HTML range 滑块（1–10），右侧实时显示数字
- 日记文字：textarea，占位文字引导用户写触发因素和感受
- 标签：多选 checkbox（Academic / Work / Relationships / Health / Sleep / Other）
- 日期：date input，默认今天，可改为过去日期（最多回溯30天）

**提交逻辑：**
1. 检查该用户当天是否已有记录：若有，提示"今天已打卡，是否覆盖/前往编辑"
2. 保存记录到数据库
3. 立即调用 `nlp/analyser.py` 进行分析，结果更新回同一条记录
4. 跳转到该记录的详情页，展示 NLP 分析结果

**历史页面：**
- 按日期倒序排列，每页10条
- 每条卡片显示：日期、心情 emoji、强度色块、日记前80字、情绪标签 chips
- 顶部筛选栏：按心情类型筛选、按日期范围筛选

**编辑/删除：**
- 编辑：表单预填当前值，保存后重新触发 NLP 分析（覆盖旧结果）
- 删除：弹出确认 modal 后执行，同时删除关联的 AIInsight 记录

### 3.4 NLP 分析模块（`app/nlp/analyser.py`）

对外暴露一个函数 `analyse(text: str) -> dict`，返回：

```python
{
    "sentiment_label": "Negative",       # Positive / Neutral / Negative
    "sentiment_polarity": -0.35,         # TextBlob polarity 原始值
    "emotion_labels": ["anxiety", "stress"],  # 细分情绪列表
    "keywords": ["exam", "deadline", "sleep"],  # 提取的关键词
    "nlp_summary": "You seem mainly concerned about stress today, possibly triggered by exam."
}
```

**实现步骤：**

1. **情感极性**：`TextBlob(text).sentiment.polarity`
   - polarity > 0.1 → Positive
   - polarity < -0.1 → Negative
   - 其余 → Neutral

2. **细分情绪分类**（关键词规则匹配）：
   - 焦虑（anxiety）：worried, anxious, nervous, panic, dread, uneasy
   - 压力（stress）：deadline, exam, pressure, overloaded, stressed, rush
   - 孤独（loneliness）：lonely, alone, isolated, miss, left out, nobody
   - 愤怒（anger）：angry, furious, frustrated, annoyed, irritated, hate
   - 悲伤（sadness）：sad, crying, hopeless, depressed, down, empty, numb
   - 满足（satisfaction）：happy, proud, grateful, accomplished, relieved, excited
   - 文本转小写后逐词匹配，可返回多个标签

3. **关键词提取**：用 TextBlob 提取名词短语（`noun_phrases`），过滤停用词，取前5个

4. **一句话总结**：模板填充，例如：
   `"You seem mainly concerned about {top_emotion} today, possibly triggered by {top_keyword}."`
   若无明显情绪标签，则用情感极性描述：`"Your journal reflects a {Positive/Neutral/Negative} emotional state today."`

**注意：** 若 `journal_text` 为空，仅根据 `mood_type` 和 `intensity` 生成简单总结，不报错

### 3.5 LLM 洞察模块（`app/insights/`）

**抽象层 `llm_client.py`：**

定义函数 `generate_insight(prompt: str) -> str`，内部根据配置中的 `LLM_PROVIDER` 决定调用哪个 API：
- `openai`：调用 `openai` 库
- `deepseek` / `gemini` 等：调用对应的 OpenAI 兼容接口或官方 SDK
- 统一异常处理：超时、rate limit 均返回 `None`，上层显示 fallback 文字

**每日洞察 Prompt 模板：**
```
The user recorded a mood entry today:
- Mood: {mood_type}, Intensity: {intensity}/10
- Journal: "{journal_text}"
- NLP Analysis: Sentiment={sentiment_label}, Emotions={emotion_labels}, Keywords={keywords}

Please provide in 3 short paragraphs:
1. An empathetic summary of today's emotional state
2. One likely underlying cause or trigger
3. Two practical suggestions for today

Keep the tone warm, supportive, and non-clinical. 
Do not diagnose. Do not use technical jargon.
```

**周期规律 Prompt 模板：**
```
Here is a summary of the user's past 7 days:
- Average intensity: {avg}
- Most common mood: {top_mood}
- Recurring emotions: {top_emotions}
- Recurring keywords: {top_keywords}

In 2–3 sentences, identify any emotional pattern and give one forward-looking suggestion.
```

**小任务建议 Prompt 模板：**
```
The user is feeling {mood_type} with intensity {intensity}/10. 
Suggest one very small, specific action they could take today (1 sentence, under 20 words).
```

**缓存逻辑：**
- 每条 MoodEntry 对应至多一条 AIInsight（daily 类型），已生成则直接读数据库，不重复调用 API
- 提供"重新生成"按钮可强制刷新

**Fallback 规则（无 API 时）：**
- 焦虑 → "Try the 4-7-8 breathing exercise and break your tasks into smaller steps."
- 悲伤/孤独 → "Reach out to someone you trust, or take a short walk outside."
- 愤怒 → "Give yourself 10 minutes before reacting. Writing your thoughts can help."
- 压力 → "List your top 3 priorities. Focus on just one at a time."
- 其他 → "Take a moment to acknowledge your feelings. You're doing well."

### 3.6 数据可视化（`app/insights/routes.py` + `static/js/charts.js`）

后端路由 `/insights/analytics` 返回 JSON 数据，前端 Chart.js 渲染：

**折线图（情绪强度趋势）：**
- x 轴：日期（最近7天或30天，顶部 toggle 切换）
- y 轴：情绪强度（1–10）
- 颜色根据情感极性变化（绿/灰/红）

**条形图（心情类型分布）：**
- x 轴：6种心情类型
- y 轴：该时期内出现次数
- 每个柱子用对应心情的配色

**统计卡片：**
- 本周平均强度 vs 上周平均强度（百分比变化，红/绿箭头）
- 本月最常见心情
- 最长连续积极情绪天数

### 3.7 减压工具箱（`app/tools/`）

**呼吸训练页 `/tools/breathing`：**
- 纯前端实现（`breathing.js`）
- 一个圆形 div，CSS 动画：吸气时放大，呼气时缩小
- 文字提示随阶段变化：Breathe In → Hold → Breathe Out
- 计时器逻辑（4-7-8 默认，可切换方块呼吸 4-4-4-4）
- 按钮：开始 / 暂停 / 重置，循环计数器

**情绪急救卡页 `/tools/firstaid`：**
- 分步骤卡片，点击"下一步"推进
- Step 1：接地气练习 - "Name 5 things you can see right now"
- Step 2：跳转呼吸训练
- Step 3：根据用户最近一条记录的情绪类型，显示对应的规则建议（不调用 LLM）

### 3.8 双语切换（Flask-Babel）

- 所有 Jinja2 模板中的 UI 文字用 `{{ _('...') }}` 包裹
- 路由 `/set_language/<lang>`：将语言偏好存入 session，若用户已登录同时更新数据库 `User.language` 字段
- 导航栏右上角显示 "EN / 中文" 切换链接
- 翻译文件路径：`app/translations/zh/LC_MESSAGES/messages.po`
- 使用 `pybabel extract` / `pybabel update` / `pybabel compile` 管理翻译

### 3.9 仪表盘（`app/main/routes.py`）

登录后的首页，集中展示：
- 问候语（早上好/下午好/晚上好 + 用户名）
- 今日打卡状态：已打卡则显示今日心情概要，未打卡则显示"去打卡"按钮
- 最新 AI 洞察卡片（today's daily insight，或最近一条）
- 今日小任务建议（来自最新 AIInsight）
- 7天情绪迷你折线图（sparkline，Chart.js）
- 快速入口：打卡 / 查看历史 / 呼吸训练 / 情绪急救

### 3.10 用户设置（`app/main/routes.py`）

页面路由 `/settings`，包含：
- 修改用户名（username）
- 修改密码（需验证当前密码）
- 语言偏好选择（下拉框，EN / 中文）

### 3.11 假数据 Seeder（`seed.py`）

运行方式：`python seed.py`

生成内容：
- 1个演示用户：邮箱 `demo@mindtrace.app`，密码 `Demo1234`
- 30条情绪记录（过去30天，每天一条）
  - 心情类型随机分布（偏向 anxious/sad/calm 以体现变化）
  - 情绪强度有高低起伏（模拟真实情绪波动）
  - 预置10条不同主题的英文日记文本（考试压力、工作疲惫、家人争吵、愉快聚会等）
  - 预填 NLP 分析结果（hardcode，不调用 TextBlob，避免依赖）
  - 预填 AI 洞察文本（hardcode，不调用 LLM API）

---

## 四、关键依赖包（`requirements.txt`）

```
Flask>=3.0
Flask-Login>=0.6
Flask-SQLAlchemy>=3.1
Flask-WTF>=1.2
Flask-Babel>=4.0
Werkzeug>=3.0
textblob>=0.18
python-dotenv>=1.0
openai>=1.0        # LLM 客户端（兼容多数供应商）
```

---

## 五、开发顺序

按以下顺序逐步实现，每步完成后可独立运行验证：

1. `config.py` + `run.py` + `app/__init__.py` → 空 Flask 应用能启动
2. `app/models.py` → 数据库表能创建
3. `app/auth/` → 注册/登录/退出能跑通
4. `app/templates/base.html` + 导航栏 + 语言切换框架 → UI 基础可用
5. `app/mood/` → 打卡、历史、编辑、删除完整流程
6. `app/nlp/analyser.py` → 分析结果能正确写入数据库并展示
7. `app/insights/llm_client.py` + daily insight → LLM 洞察能生成
8. `app/insights/` weekly + small task → 洞察模块完整
9. `app/main/dashboard.html` → 仪表盘整合所有数据
10. `app/insights/analytics` + Chart.js → 图表可视化
11. `app/tools/` → 呼吸训练 + 急救卡
12. `app/main/settings` → 用户设置
13. `seed.py` → 假数据生成
14. 全局 UI 打磨 + 翻译文件补全 + 错误页面

---

## 六、注意事项

- `.env` 文件包含 `SECRET_KEY` 和 `LLM_API_KEY`，必须加入 `.gitignore`
- LLM 调用统一经过抽象层，换供应商只需修改 `llm_client.py` 和 `.env` 中的配置
- 所有 LLM 生成内容页面底部需加免责声明：*"AI-generated content is not a substitute for professional mental health support."*
- 情绪打卡每天只允许一条记录（同一用户同一日期唯一约束）
- 图表数据通过 Flask 路由返回 JSON，前端 fetch 获取，避免在模板中混入大量数据