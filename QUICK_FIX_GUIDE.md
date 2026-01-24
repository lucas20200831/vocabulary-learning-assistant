# 🎯 生产环境音频问题 - 快速修复清单

## 📋 本次更新内容

| 文件 | 变更 | 目的 |
|------|------|------|
| `flask_app.py` | 添加 CORS, 改进 TTS 端点 | 解决跨域和延迟问题 |
| `requirements.txt` | 添加 flask-cors | CORS 支持 |
| `templates/quiz.html` | 改进音频加载和日志 | 更好的调试和重试 |
| `audio_diagnostics.py` | **新文件** | 诊断工具 |
| `PRODUCTION_DEPLOYMENT_GUIDE.md` | **新文件** | 详细部署指南 |

---

## 🚀 快速部署（3步）

### 1️⃣ 本地测试
```bash
pip install -r requirements.txt
python audio_diagnostics.py
python flask_app.py
```
在 http://localhost:5002 测试音频播放

### 2️⃣ 上传文件到服务器
```
flask_app.py         ← 更新
requirements.txt     ← 更新  
templates/quiz.html  ← 更新
audio_diagnostics.py ← 新增
```

### 3️⃣ 服务器配置

**安装新依赖**:
```bash
pip install -r requirements.txt
```

**Nginx 配置**:
```nginx
location /static/ {
    alias /path/to/app/static/;
    types { audio/mpeg mp3; }
    expires 1d;
}
```

**重启应用**:
```bash
# 使用 Gunicorn
gunicorn -w 4 -b 127.0.0.1:5002 flask_app:app

# 或使用 systemd
systemctl restart vocabulary-app
```

---

## 🔍 验证部署成功

### 浏览器控制台 (F12 → Console)
应该看到:
```
[AUDIO] Requesting audio for: 学习
[AUDIO] Response: {success: true, url: "/static/audio/...", ready: true}
[AUDIO] Playing: /static/audio/....mp3?v=...
[AUDIO] Playing successfully
```

### Flask 日志
应该看到:
```
[TTS] Request for: 学习
[TTS] File exists: false
[TTS] Queueing: 学习
[TTS] Generated: 学习 -> /path/to/static/audio/...
```

### 网络请求 (F12 → Network)
- ✅ `/tts/...` → 状态 200
- ✅ `/static/audio/...` → 状态 200, 大小 > 5KB

---

## ⚠️ 常见问题速解

| 问题 | 解决方案 |
|------|---------|
| 仍然没声音 | 检查浏览器 Console 的 [AUDIO] 日志 |
| 404 Not Found | 检查 Web 服务器 /static/ 配置 |
| CORS 错误 | 确保 `pip install flask-cors` 成功 |
| 音频文件损坏 | 运行 `python audio_diagnostics.py` |
| 播放很慢 | 正常（首次 2-5秒），之后缓存加速 |

---

## 📞 需要帮助?

1. **运行诊断**:
   ```bash
   python audio_diagnostics.py
   ```

2. **查看日志**:
   - Flask 日志: 查看 `[TTS]` 消息
   - 浏览器日志: F12 控制台 `[AUDIO]` 消息

3. **参考文档**:
   - 详细指南: `PRODUCTION_DEPLOYMENT_GUIDE.md`
   - 解决方案: `AUDIO_FIX_SUMMARY.md`

---

**更新日期**: 2026-01-24  
**版本**: 2.0  
**状态**: ✅ 已测试，可部署
