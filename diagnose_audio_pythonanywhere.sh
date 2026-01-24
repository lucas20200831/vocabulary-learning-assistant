#!/bin/bash

# PythonAnywhere 音频问题诊断脚本
# 用于诊断 TTS 和 CORS 问题

echo "=========================================="
echo "🔍 PythonAnywhere 音频诊断"
echo "=========================================="

PROJECT_DIR="/home/Lucas2002/vocabulary-learning-assistant"
cd $PROJECT_DIR

echo ""
echo "1️⃣  检查 flask_cors 是否安装..."
python3 -c "import flask_cors; print('✅ flask_cors 已安装')" 2>&1 || echo "❌ flask_cors 未安装"

echo ""
echo "2️⃣  检查 gtts 是否安装..."
python3 -c "import gtts; print('✅ gtts 已安装')" 2>&1 || echo "❌ gtts 未安装"

echo ""
echo "3️⃣  检查音频目录..."
if [ -d "static/audio" ]; then
    echo "✅ 音频目录存在"
    echo "   已有音频文件数量: $(ls -1 static/audio/*.mp3 2>/dev/null | wc -l) 个"
else
    echo "❌ 音频目录不存在，创建中..."
    mkdir -p static/audio
    chmod 755 static/audio
fi

echo ""
echo "4️⃣  检查 flask_app.py 中 CORS 配置..."
if grep -q "CORS(app" flask_app.py; then
    echo "✅ CORS 已配置"
    grep "CORS(app" flask_app.py | head -1
else
    echo "❌ CORS 未配置"
fi

echo ""
echo "5️⃣  检查 TTS 端点..."
if grep -q "@app.route('/tts/" flask_app.py; then
    echo "✅ TTS 端点存在"
else
    echo "❌ TTS 端点缺失"
fi

echo ""
echo "6️⃣  验证 requirements.txt..."
echo "当前依赖列表："
cat requirements.txt

echo ""
echo "=========================================="
echo "📌 排查建议："
echo "=========================================="
echo ""
echo "如果出现问题，请在浏览器中："
echo "1. 按 F12 打开开发者工具"
echo "2. 选择 Console 标签，查看 [AUDIO] 和 [TTS] 日志"
echo "3. 选择 Network 标签，看 /tts/ 请求的响应"
echo "4. 选择 Application 标签，检查 CORS 相关 headers"
echo ""
echo "常见问题："
echo "- CORS 错误：检查 flask_cors 是否安装并正确配置"
echo "- 404 错误：检查音频文件是否生成"
echo "- 超时错误：可能是 gTTS 请求被阻止"
