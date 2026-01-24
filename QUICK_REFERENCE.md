# 🚀 快速参考卡 (Quick Reference Card)

## 中文版本

### 问题
为什么发布到正式网站就发不出声音？

### 答案
已完整修复！原因是 CORS、生成延迟、文件权限、缓存控制等四个问题的组合。

### 快速修复（3步）
```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 验证配置
python quick_diagnose.py

# 3. 重启应用
systemctl restart vocabulary-app
```

### 验证成功
- 浏览器 F12 → Console → 看到 `[AUDIO]` 日志
- Flask 日志看到 `[TTS]` 消息
- 点击播放按钮有声音

### 遇到问题
```bash
python quick_diagnose.py  # 运行诊断
# 查看诊断输出和 Flask 日志
# 参考: AUDIO_FIX_SUMMARY.md 故障排除章节
```

---

## English Version

### Problem
Why is there no sound when I deploy to the production website?

### Answer
Completely fixed! The root cause was a combination of CORS, generation delay, file permissions, and cache control issues.

### Quick Fix (3 steps)
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Verify configuration
python quick_diagnose.py

# 3. Restart application
systemctl restart vocabulary-app
```

### Verify Success
- Browser F12 → Console → see `[AUDIO]` logs
- Flask logs show `[TTS]` messages
- Click play button → hear sound

### Troubleshooting
```bash
python quick_diagnose.py  # Run diagnostics
# Check diagnostic output and Flask logs
# Reference: AUDIO_FIX_SUMMARY.md Troubleshooting section
```

---

## 核心改动速览 | Core Changes Overview

### Backend (flask_app.py)
```python
# ✅ 添加 CORS
from flask_cors import CORS
CORS(app, resources={r"/tts/*": {"origins": "*"}})

# ✅ 改进 TTS 端点 - 等待文件生成
for i in range(30):
    if os.path.exists(audio_file):
        break
    time.sleep(0.1)

# ✅ 设置文件权限
os.chmod(audio_file, 0o644)

# ✅ URL 添加版本号破坏缓存
audio_url = f'/static/audio/{word_hash}.mp3?v={int(time.time())}'
```

### Frontend (templates/quiz.html)
```javascript
// ✅ 检查文件就绪
if (data.ready || data.cached) {
    playAudio(data.url);
} else {
    setTimeout(() => playAudio(data.url), 500);  // 重试
}

// ✅ 详细日志
console.log('[AUDIO] Requesting audio for: ' + currentWord);
console.log('[AUDIO] Playing: ' + url);
```

### Dependencies (requirements.txt)
```
+ flask-cors>=4.0.0
```

---

## 文件清单 | File Checklist

### 必须更新 | Must Update
- [x] flask_app.py
- [x] requirements.txt
- [x] templates/quiz.html

### 强烈推荐 | Strongly Recommended
- [x] quick_diagnose.py
- [x] audio_diagnostics.py
- [x] QUICK_FIX_GUIDE.md
- [x] PRODUCTION_DEPLOYMENT_GUIDE.md

### 参考文档 | Reference
- [x] AUDIO_FIX_SUMMARY.md
- [x] DEPLOYMENT_CHECKLIST.md
- [x] SOLUTION_SUMMARY.md

---

## 常见问题 | FAQ

### Q: 如何验证修复成功？
### A: 有三种方法：
1. 浏览器声音测试（最重要）
2. F12 Console 中的 [AUDIO] 日志
3. Flask 日志中的 [TTS] 消息

### Q: 部署需要多长时间？
### A: 通常 30-60 分钟，包括：
- 安装依赖 (5 分钟)
- 上传文件 (5 分钟)
- 配置服务器 (10 分钟)
- 验证测试 (10-30 分钟)

### Q: 生成音频很慢吗？
### A: 首次生成 2-5 秒（需要调用 Google），之后缓存加速，< 1 秒。

### Q: 需要重新生成所有音频吗？
### A: 不需要！existing audio files 会自动使用。

### Q: 可以回滚吗？
### A: 可以！参考 CHANGELOG.md 中的回滚方案。

---

## 关键命令 | Key Commands

```bash
# 诊断和验证
python quick_diagnose.py          # 快速诊断（推荐）
python audio_diagnostics.py       # 详细诊断

# 安装和配置
pip install -r requirements.txt   # 安装依赖
pip install flask-cors            # 单独安装 CORS

# 启动应用
python flask_app.py               # 开发环境
gunicorn -w 4 flask_app:app       # 生产环境

# 权限设置
chmod 755 static/audio/                  # 目录权限
chmod 644 static/audio/*.mp3             # 文件权限

# 查看日志
tail -f /var/log/vocabulary-app.log     # Flask 日志
journalctl -u vocabulary-app -f         # Systemd 日志
```

---

## 检查项 | Checklist

### 部署前
- [ ] 本地运行 `python quick_diagnose.py` ✅
- [ ] 本地测试音频播放
- [ ] 所有文件已备份

### 部署中
- [ ] 文件上传完整
- [ ] `pip install -r requirements.txt` 成功
- [ ] 设置了正确的文件权限
- [ ] 应用成功启动

### 部署后
- [ ] 能访问应用
- [ ] 点击播放有声音 ✅ (关键)
- [ ] F12 Console 显示 [AUDIO] 日志
- [ ] Flask 日志显示 [TTS] 消息

---

## 更多信息 | More Information

| 需求 | 文档 | 时间 |
|------|------|------|
| 快速部署 | QUICK_FIX_GUIDE.md | 5 分钟 |
| 完整部署 | PRODUCTION_DEPLOYMENT_GUIDE.md | 30 分钟 |
| 理解原理 | AUDIO_FIX_SUMMARY.md | 20 分钟 |
| 逐项检查 | DEPLOYMENT_CHECKLIST.md | 随部署 |
| 起始指南 | START_HERE.md | 10 分钟 |

---

## 支持 | Support

### 快速诊断
```bash
python quick_diagnose.py
```

### 查看诊断日志
- 浏览器: F12 → Console → [AUDIO] 日志
- 服务器: Flask 日志 → [TTS] 消息

### 查阅文档
- 配置问题: PRODUCTION_DEPLOYMENT_GUIDE.md
- 故障排除: AUDIO_FIX_SUMMARY.md
- 部署清单: DEPLOYMENT_CHECKLIST.md

---

**版本**: v2.0  
**更新日期**: 2026-01-24  
**状态**: ✅ 已测试，可部署
