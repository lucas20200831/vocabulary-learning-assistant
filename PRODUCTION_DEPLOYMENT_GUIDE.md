# 生产环境部署指南 - 音频功能修复

## 问题诊断

在正式网站部署后出现音频无声的问题，通常原因包括：

1. **CORS 跨域问题** ❌ → ✅ 已修复
   - 前端请求被 CORS 策略阻止
   - 已添加 Flask-CORS 支持

2. **音频文件生成延迟** ❌ → ✅ 已修复
   - 后台线程生成时间长，前端立即请求时文件不存在
   - 已改进后端逻辑，等待文件生成（最多3秒）

3. **文件权限问题** ❌ → ✅ 已修复
   - Web 服务器无法读取音频文件
   - 已添加文件权限设置（chmod 0o644）

4. **缓存问题** ❌ → ✅ 已修复
   - 浏览器缓存导致找不到新生成的文件
   - 已为 URL 添加时间戳版本号

## 本次更新内容

### 后端改进 (flask_app.py)

```python
# 1. 添加 CORS 支持
from flask_cors import CORS
CORS(app, resources={
    r"/tts/*": {"origins": "*"},
    r"/static/*": {"origins": "*"}
})

# 2. 改进 TTS worker 错误处理和权限设置
os.chmod(audio_file, 0o644)

# 3. 改进 /tts/<word> 端点
- 添加详细日志
- 等待文件生成（非阻塞，最多等待3秒）
- 返回文件就绪状态
- 添加缓存破坏版本号（时间戳）
```

### 前端改进 (templates/quiz.html)

```javascript
// 1. 改进音频加载逻辑
- 检查文件是否就绪
- 添加加载失败重试
- 详细的调试日志 [AUDIO]

// 2. 更好的错误处理
- audioPlayer 错误事件监听
- Promise 异常捕获
- 开发者工具中易于诊断
```

### 依赖更新 (requirements.txt)

```
+ flask-cors>=4.0.0
```

## 部署步骤

### 1. 本地测试

```bash
# 安装新依赖
pip install -r requirements.txt

# 运行诊断脚本
python audio_diagnostics.py

# 启动 Flask 应用
python flask_app.py
```

在浏览器中访问：http://localhost:5002

打开开发者工具 (F12) → Console 标签，观察 `[AUDIO]` 日志

### 2. 生产环境配置

#### 如果使用 Nginx：

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:5002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        # CORS 支持
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS' always;
    }
    
    location /static/ {
        alias /path/to/app/static/;
        # 音频文件 MIME 类型
        types {
            audio/mpeg mp3;
        }
        # 启用缓存（但不要过长）
        expires 1d;
    }
}
```

#### 如果使用 Gunicorn + Nginx：

```bash
# 安装 Gunicorn
pip install gunicorn

# 运行 Gunicorn（多工作进程）
gunicorn -w 4 -b 127.0.0.1:5002 flask_app:app

# 在 Nginx 中配置同上
```

#### 如果使用 Apache：

```apache
<VirtualHost *:80>
    ServerName your-domain.com
    
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:5002/
    ProxyPassReverse / http://127.0.0.1:5002/
    
    # 启用 CORS
    Header set Access-Control-Allow-Origin "*"
    
    <Directory /path/to/app/static/audio>
        Allow from all
        AddType audio/mpeg .mp3
    </Directory>
</VirtualHost>
```

### 3. 文件系统权限

```bash
# 确保音频目录权限正确
chmod 755 /path/to/app/static/audio
# 或者让 Flask 应用自动创建
chown -R appuser:appuser /path/to/app/static
```

### 4. 验证部署

访问应用后，在浏览器开发者工具中：

1. **Network 标签**
   - 查看 `/tts/<word>` 请求状态
   - 查看 `/static/audio/*.mp3` 响应状态
   - 验证响应大小 > 0

2. **Console 标签**
   - 查看 `[AUDIO]` 日志输出
   - 检查是否有错误信息

3. **检查实际文件**
   ```bash
   # SSH 到服务器
   ls -la /path/to/app/static/audio/
   # 应该看到 *.mp3 文件
   ```

## 常见问题解决

### 问题 1: 404 Not Found (音频文件找不到)

**原因**: 
- 静态文件路径配置错误
- Web 服务器配置不包含 /static/ 路径

**解决**:
- 确保 Flask 应用的 `AUDIO_DIR` 路径正确
- 在 Web 服务器配置中包含 static 目录
- 运行诊断脚本：`python audio_diagnostics.py`

### 问题 2: CORS 错误

**症状**: 浏览器控制台显示 "CORS policy: No 'Access-Control-Allow-Origin' header"

**原因**: 跨域请求被阻止

**解决**:
```python
# 已在 flask_app.py 中添加：
from flask_cors import CORS
CORS(app)
```

### 问题 3: 音频文件损坏或无法播放

**原因**: 文件权限问题或生成失败

**解决**:
```bash
# 检查文件权限
ls -la static/audio/
# 应该显示 644 或更高权限

# 检查文件大小（不应该为 0）
file static/audio/*.mp3

# 运行诊断
python audio_diagnostics.py
```

### 问题 4: 生成音频缓慢

**原因**: gTTS 需要网络连接到 Google 服务，速度受网络影响

**解决**:
- 使用多线程（已配置 3 个工作线程）
- 部署时确保服务器网络通畅
- 可考虑缓存预加载

## 监控和日志

### 查看 Flask 日志

```bash
# 应该看到 [TTS] 开头的日志消息
# 例如：
# [TTS] Request for: 学习
# [TTS] File exists: False
# [TTS] Queueing: 学习
# [TTS] Generated: 学习 -> /path/to/static/audio/hash.mp3
```

### 启用详细日志（开发调试）

编辑 `flask_app.py`，在初始化部分添加：

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 性能优化建议

1. **预加载常用词汇**
   - 应用启动时生成常用词汇的音频
   - 减少首次请求延迟

2. **使用 CDN 缓存**
   - 将音频文件上传到 CDN
   - 加快全球用户访问速度

3. **异步生成**
   - 已使用后台线程（无需额外配置）
   - 不阻塞 HTTP 请求

4. **定期清理过期缓存**
   ```bash
   # 删除 7 天前的音频文件
   find static/audio -type f -mtime +7 -delete
   ```

## 回滚方案

如果遇到严重问题，可恢复到原始版本：

```bash
# 查看 git 历史
git log --oneline

# 恢复特定文件
git checkout <commit-hash> -- flask_app.py templates/quiz.html

# 或恢复整个项目
git reset --hard <commit-hash>
```

## 技术支持

如果问题仍未解决，请：

1. 运行诊断脚本并保存输出：
   ```bash
   python audio_diagnostics.py > diagnostics.log 2>&1
   ```

2. 检查 Flask 日志中的 [TTS] 错误

3. 查看浏览器控制台中的 [AUDIO] 日志

4. 验证网络连接和防火墙设置

---

**更新日期**: 2026年1月24日
**版本**: v2.0 (音频功能改进版)
