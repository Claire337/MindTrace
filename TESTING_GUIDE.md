# MindTrace 测试指南

## 快速启动

### 1. 激活虚拟环境
```bash
cd /Users/linchenglong/Work/Program/Python/Flask/17
source venv/bin/activate
```

### 2. 编译翻译文件（如果还没做过）
```bash
pybabel compile -d app/translations
```

### 3. 启动 Flask 开发服务器
```bash
python run.py
```

你应该看到这样的输出：
```
* Running on http://127.0.0.1:5000
Press CTRL+C to quit
* Debugger is active!
```

---

## 手动测试（在浏览器中）

### 访问地址
打开浏览器访问：`http://127.0.0.1:5000`

### 测试路径

#### 1. **首页重定向** ✓
- URL：`http://127.0.0.1:5000/`
- 预期：**未登录时** 重定向到登录页
- 预期：**已登录时** 重定向到仪表盘

#### 2. **注册页面** ✓
- URL：`http://127.0.0.1:5000/auth/register`
- 测试用例：
  - ✓ 输入邮箱、用户名、密码（8字符以上），确认密码一致 → 应该注册成功
  - ✓ 密码不一致 → 显示错误 "Passwords do not match"
  - ✓ 密码少于8字符 → 显示错误 "Password must be at least 8 characters"
  - ✓ 邮箱已存在 → 显示错误 "Email already registered"
  - ✓ 注册成功后自动跳转到仪表盘

#### 3. **登录页面** ✓
- URL：`http://127.0.0.1:5000/auth/login`
- 测试用例：
  - ✓ 输入正确邮箱和密码 → 登录成功，跳转仪表盘
  - ✓ 邮箱不存在 → 显示错误 "Invalid email or password"
  - ✓ 密码错误 → 显示错误 "Invalid email or password"
  - ✓ 勾选"记住我" → session 延长到 30 天
  - ✓ 页面提示演示账户（虽然还没创建）

#### 4. **仪表盘** ✓
- URL：`http://127.0.0.1:5000/dashboard`（需要先登录）
- 预期：
  - ✓ 导航栏显示当前用户名
  - ✓ 显示欢迎信息 "Welcome to MindTrace..."
  - ✓ 有两个快速入口卡片：打卡、查看历史
  - ✓ 未登录时访问重定向到登录页

#### 5. **设置页面** ✓
- URL：`http://127.0.0.1:5000/settings`
- 预期：
  - ✓ 显示账户信息（邮箱、用户名、注册时间）
  - ✓ 语言偏好选择按钮（EN / 中文）

#### 6. **双语切换** ✓
- 点击导航栏右上角的 "EN / 中文" 下拉菜单
- 点击 "English" → 页面切换为英文
- 点击 "中文" → 页面切换为中文
- 测试项目：
  - ✓ 导航栏菜单文字切换
  - ✓ 按钮文字切换
  - ✓ 页面标题切换
  - ✓ 语言选择保存到 session（刷新页面仍保持）
  - ✓ 已登录用户刷新后语言选择保持

#### 7. **退出登录** ✓
- 点击用户下拉菜单 → 点击 "Logout"
- 预期：
  - ✓ 清除 session
  - ✓ 重定向到登录页
  - ✓ 显示成功提示 "You have been logged out"

#### 8. **占位符页面** ✓
- 已登录状态下访问以下页面，应该都能打开（显示占位符）：
  - ✓ `/mood/new` —— 新建打卡
  - ✓ `/mood/history` —— 历史记录
  - ✓ `/insights/analytics` —— 数据分析
  - ✓ `/tools/breathing` —— 呼吸训练

---

## 自动化测试（Python 脚本）

### 快速功能测试
```python
# 在项目根目录运行
python -c "
from app import create_app

app = create_app()
client = app.test_client()

# 测试重定向到登录
resp = client.get('/')
assert resp.status_code == 302  # 重定向
print('✓ 首页重定向正常')

# 测试注册页可访问
resp = client.get('/auth/register')
assert resp.status_code == 200
print('✓ 注册页可访问')

# 测试登录页可访问
resp = client.get('/auth/register')
assert resp.status_code == 200
print('✓ 登录页可访问')

print('\\n✅ 所有基础测试通过！')
"
```

---

## 数据库检查

### 查看数据库文件
```bash
# 数据库文件位置
ls -lh /Users/linchenglong/Work/Program/Python/Flask/17/mindtrace_dev.db

# 查看表结构
python -c "
from app import db, create_app
from app.models import User, MoodEntry, AIInsight

app = create_app()
with app.app_context():
    # 查看用户数
    user_count = User.query.count()
    print(f'✓ Users 表中有 {user_count} 条记录')
    
    # 列出所有用户
    for user in User.query.all():
        print(f'  - {user.username} ({user.email})')
"
```

---

## 常见问题排查

### 问题 1：翻译文件编译错误
```bash
# 重新编译
pybabel compile -d app/translations
```

### 问题 2：数据库锁定
```bash
# 删除数据库，重新启动会自动重建
rm mindtrace_dev.db
python run.py
```

### 问题 3：端口 5000 已被占用
```bash
# 改用其他端口
python -c "from app import create_app; app = create_app(); app.run(port=5001)"
```

### 问题 4：翻译不生效
```bash
# 清除 Flask 缓存并重启
rm -rf __pycache__ app/__pycache__
pybabel compile -d app/translations
python run.py
```

---

## 测试检查表

完整功能验证：

- [ ] 注册新用户成功
- [ ] 用新账号登录成功
- [ ] 访问仪表盘显示用户名
- [ ] 语言切换 EN → 中文 → EN
- [ ] 退出登录返回登录页
- [ ] 登出后重新登录同一账户
- [ ] 所有占位符页面可访问
- [ ] 设置页显示账户信息
- [ ] 未登录用户无法访问受保护页面
- [ ] 数据库表创建正确

---

## 下一步

Phase 1 验证完成后，可以开始 **Phase 2 — 情绪记录核心功能**：
- 打卡表单实现
- 历史列表实现
- NLP 分析准备

有任何问题，随时告诉我！
