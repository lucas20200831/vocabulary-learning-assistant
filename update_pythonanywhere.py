#!/usr/bin/env python3
"""
从 GitHub 更新到 PythonAnywhere 的完整脚本
用户名: Lucas2002
仓库: vocabulary-learning-assistant
"""

import subprocess
import sys
import os

def run_command(cmd, description):
    """执行命令并返回结果"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} 成功")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print(f"❌ {description} 失败")
            if result.stderr:
                print(f"错误: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        return False

def main():
    print("=" * 50)
    print("开始更新到 PythonAnywhere...")
    print("=" * 50)
    
    # 项目目录
    project_dir = "/home/Lucas2002/vocabulary-learning-assistant"
    
    # 检查目录是否存在
    if not os.path.exists(project_dir):
        print(f"❌ 项目目录不存在: {project_dir}")
        sys.exit(1)
    
    # 进入项目目录
    os.chdir(project_dir)
    print(f"📁 进入目录: {project_dir}")
    
    # 步骤1: 更新代码
    if not run_command("git pull origin main", "1️⃣  更新代码（git pull）"):
        sys.exit(1)
    
    # 步骤2: 安装依赖
    if not run_command("pip install -r requirements.txt", "2️⃣  安装/更新依赖"):
        sys.exit(1)
    
    # 步骤3: 验证更新
    print("\n3️⃣  验证更新...")
    result = subprocess.run("git log -1 --oneline", shell=True, capture_output=True, text=True)
    print("最新提交:")
    print(result.stdout)
    
    # 完成
    print("\n" + "=" * 50)
    print("✅ 更新完成！")
    print("=" * 50)
    print("\n📌 后续步骤:")
    print("1. 登录 PythonAnywhere 网站")
    print("2. 点击 'Web' 选项卡")
    print("3. 点击 'Reload' 按钮重启应用")
    print("\n✨ 应用会立即应用所有更改（音频修复、新数据等）")

if __name__ == "__main__":
    main()
