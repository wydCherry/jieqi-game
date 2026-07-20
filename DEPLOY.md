# 揭棋对战 - 云端部署指南

## 一键部署到 Render.com

### 步骤 1：注册 GitHub 账号
如果还没有 GitHub 账号，请先注册：https://github.com/signup

### 步骤 2：创建 GitHub 仓库
1. 登录 GitHub
2. 点击右上角 "+" → "New repository"
3. 仓库名填：`jieqi-game`
4. 选择 "Public"
5. 点击 "Create repository"

### 步骤 3：上传代码到 GitHub

#### 方法 A：使用 GitHub Desktop（推荐新手）
1. 下载安装 [GitHub Desktop](https://desktop.github.com/)
2. 登录 GitHub 账号
3. 点击 "File" → "Add Local Repository"
4. 选择项目文件夹：`C:\Users\91096\Desktop\jieqi-game`
5. 点击 "Publish repository"
6. 取消勾选 "Keep this code private"（保持公开）
7. 点击 "Publish repository"

#### 方法 B：使用命令行
```bash
cd C:\Users\91096\Desktop\jieqi-game
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/你的用户名/jieqi-game.git
git push -u origin main
```

### 步骤 4：部署到 Render.com

1. 访问 https://render.com 并用 GitHub 账号登录
2. 点击 "New" → "Web Service"
3. 授权 Render 访问你的 GitHub
4. 选择 `jieqi-game` 仓库
5. 填写配置：
   - **Name**: `jieqi-game`（或自定义名称）
   - **Region**: Singapore（离中国最近）
   - **Branch**: main
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
6. 点击 "Deploy Web Service"

### 步骤 5：获取公网链接
部署完成后（约 2-5 分钟），Render 会给你一个链接：
```
https://jieqi-game-xxxx.onrender.com
```

**这个链接可以在任何手机浏览器打开！**

---

## 备选方案：PythonAnywhere（完全免费）

### 步骤 1：注册
访问 https://www.pythonanywhere.com 注册免费账号

### 步骤 2：上传代码
1. 登录后点击 "Files" 标签
2. 创建目录 `jieqi-game`
3. 上传所有项目文件

### 步骤 3：创建 Web App
1. 点击 "Web" 标签
2. 点击 "Add a new web app"
3. 选择手动配置 → Python 3.10
4. 设置工作目录为 `/home/你的用户名/jieqi-game`

### 步骤 4：配置 WSGI
编辑 WSGI 配置文件：
```python
import sys
sys.path.append('/home/你的用户名/jieqi-game')

from app import app as application
```

### 步骤 5：安装依赖
点击 "Consoles" → "Bash"，运行：
```bash
pip install flask
```

### 步骤 6：重启并访问
点击 "Web" → "Reload"，访问：
```
https://你的用户名.pythonanywhere.com
```

---

## 注意事项

1. **免费限制**：
   - Render 免费版会在 15 分钟无访问后休眠，首次访问需要等待 30 秒启动
   - PythonAnywhere 免费版每天有 CPU 秒数限制

2. **数据持久化**：
   - 云平台重启后数据会丢失（排行榜记录）
   - 如需持久化，需要使用数据库（如 SQLite 持久卷或 PostgreSQL）

3. **网络对战**：
   - 当前网络对战功能仅支持局域网
   - 云部署后暂不支持实时对战（需要 WebSocket 支持）

---

## 快速测试

部署完成后，用手机浏览器访问你的公网链接即可开始游戏！