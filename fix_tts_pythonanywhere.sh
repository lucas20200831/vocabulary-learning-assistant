#!/bin/bash

# PythonAnywhere TTS 问题快速修复
# 问题: TTS engine not available

PROJECT_DIR="/home/Lucas2002/vocabulary-learning-assistant"
cd $PROJECT_DIR

echo "=========================================="
echo "🔧 快速修复 TTS 问题"
echo "=========================================="

echo ""
echo "1️⃣  强制重新安装 gtts..."
pip3 install --upgrade --force-reinstall gtts

echo ""
echo "2️⃣  强制重新安装 flask-cors..."
pip3 install --upgrade --force-reinstall flask-cors

echo ""
echo "3️⃣  验证安装..."
python3 << 'EOF'
print("\n检查模块导入:")
try:
    from gtts import gTTS
    print("✅ gTTS 导入成功")
    # 测试是否能工作
    tts = gTTS(text="测试", lang='zh-CN')
    print("✅ gTTS 可以正常使用")
except Exception as e:
    print(f"❌ gTTS 错误: {e}")

try:
    from flask_cors import CORS
    print("✅ flask-cors 导入成功")
except Exception as e:
    print(f"❌ flask-cors 错误: {e}")
EOF

echo ""
echo "=========================================="
echo "✅ 修复完成！"
echo "=========================================="
echo ""
echo "📌 后续步骤："
echo "1. 登录 PythonAnywhere 网站"
echo "2. 点击 'Web' 选项卡"
echo "3. 点击 'Reload' 按钮重启应用"
echo "4. 刷新页面并测试音频播放"
echo ""
