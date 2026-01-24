#!/bin/bash

# 从 GitHub 更新到 PythonAnywhere 的完整脚本
# 用户名: Lucas2002
# 仓库: vocabulary-learning-assistant

echo "=========================================="
echo "开始更新到 PythonAnywhere..."
echo "=========================================="

# 进入项目目录
cd /home/Lucas2002/vocabulary-learning-assistant

echo ""
echo "1️⃣  更新代码（git pull）..."
git pull origin main

if [ $? -eq 0 ]; then
    echo "✅ Git pull 成功"
else
    echo "❌ Git pull 失败"
    exit 1
fi

echo ""
echo "2️⃣  安装/更新依赖..."
pip3 install --upgrade -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ 依赖安装成功"
else
    echo "❌ 依赖安装失败"
    exit 1
fi

echo ""
echo "2b️⃣ 验证关键依赖..."
echo "检查 flask-cors..."
python3 -c "import flask_cors; print('✅ flask-cors OK')" 2>&1 || echo "❌ flask-cors 失败"
echo "检查 gtts..."
python3 -c "import gtts; print('✅ gtts OK')" 2>&1 || echo "❌ gtts 失败"

echo ""
echo "3️⃣  验证更新..."
echo "最新提交："
git log -1 --oneline

echo ""
echo "=========================================="
echo "✅ 更新完成！"
echo "=========================================="
echo ""
echo "📌 后续步骤："
echo "1. 登录 PythonAnywhere 网站"
echo "2. 点击 'Web' 选项卡"
echo "3. 点击 'Reload' 按钮重启应用"
echo ""
echo "✨ 应用会立即应用所有更改（音频修复、新数据等）"
