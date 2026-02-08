# PythonAnywhere 部署指南

## 第1步：在PythonAnywhere上克隆项目

1. 登录到 [PythonAnywhere](https://www.pythonanywhere.com/)
2. 打开 Web 标签页，进入 "Bash console"（顶部菜单）
3. 运行以下命令：

```bash
cd /home/lucas2002
git clone https://github.com/lucas20200831/vocabulary-learning-assistant.git mysite
cd mysite
```

## 第2步：创建虚拟环境并安装依赖

在Bash控制台中运行：

```bash
mkvirtualenv --python=/usr/bin/python3.10 venv
pip install -r requirements.txt
```

如果已有虚拟环境，运行：
```bash
source /home/lucas2002/.virtualenvs/venv/bin/activate
pip install -r requirements.txt
```

## 第3步：配置WSGI（最关键）

1. 在PythonAnywhere Web标签页中，点击 "lucas2002.pythonanywhere.com"
2. 在打开的Web应用配置页面中：
   - 找到 "Code" 部分中的 "WSGI configuration file"
   - 点击编辑它（通常路径是 `/home/lucas2002/mysite/wsgi_pythonanywhere.py`）
   - 替换为以下内容：

```python
import sys
import os

# Add project directory to sys.path  
project_home = '/home/lucas2002/mysite'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ['FLASK_ENV'] = 'production'

# Import the Flask app
from flask_app import app

# The application object used by PythonAnywhere's WSGI handler
application = app
```

## 第4步：配置静态文件

在同一个Web应用配置页面中，找到 "Static files" 部分，添加以下两行：

| URL | Directory |
|-----|-----------|
| `/static` | `/home/lucas2002/mysite/static` |
| `/audio` | `/home/lucas2002/mysite/static/audio` |

## 第5步：配置虚拟环境路径

在同一个Web应用配置页面中，找到 "Virtualenv" 部分：
- 输入虚拟环境路径：`/home/lucas2002/.virtualenvs/venv`

## 第6步：重新加载Web应用

1. 返回Web应用配置页面顶部
2. 点击绿色的 "Reload lucas2002.pythonanywhere.com" 按钮
3. 等待几秒钟

## 第7步：检查应用日志

如果有任何问题，检查错误日志：
1. 在Web应用配置页中向下滚动找到 "Log files"
2. 查看 "Error log" 和 "Server log"

## 更新项目（下次更新时）

在Bash控制台中运行：

```bash
cd /home/lucas2002/mysite
git pull origin main
pip install -r requirements.txt  # 如果有新的依赖
```

然后在Web应用配置页面中点击 "Reload" 按钮。

## 常见问题

### Q: 如何修改Flask的监听端口？
A: PythonAnywhere会自动处理端口，不需要修改。

### Q: 音频文件无法保存？
A: 确保 `/home/lucas2002/mysite/static/audio` 目录存在并有写入权限。在Bash中运行：
```bash
mkdir -p /home/lucas2002/mysite/static/audio
chmod 755 /home/lucas2002/mysite/static/audio
```

### Q: 如何调试？
A: 在WSGI文件中添加打印语句并查看日志文件。

---

访问您的应用：https://lucas2002.pythonanywhere.com/
