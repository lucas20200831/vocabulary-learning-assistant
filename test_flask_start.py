#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接测试 Flask 应用启动的简化版本
"""

import sys
import os
import threading
import time

os.chdir(r'd:\Education_Lucas\vocabulary-learning-assistant')

print("[TEST] 开始测试 Flask 启动...")

try:
    print("[TEST] Step 1: 导入 Flask...")
    from flask import Flask
    print("[TEST] ✓ Flask 导入成功")
    
    print("[TEST] Step 2: 导入 flask_app 模块...")
    import flask_app
    print("[TEST] ✓ flask_app 模块导入成功")
    
    print("[TEST] Step 3: 获取 app 对象...")
    app = flask_app.app
    print(f"[TEST] ✓ App 对象创建成功: {app}")
    
    print("[TEST] Step 4: 启动 Flask 应用...")
    print("[TEST] ⏳ Flask 将在 http://127.0.0.1:5002 启动")
    print("[TEST] ⏳ 等待 3 秒后检查服务器状态...")
    
    # 在后台线程启动 Flask
    flask_thread = threading.Thread(
        target=lambda: app.run(debug=True, host='127.0.0.1', port=5002, use_reloader=False),
        daemon=True
    )
    flask_thread.start()
    
    time.sleep(4)
    
    print("[TEST] Step 5: 检查服务器状态...")
    try:
        import requests
        response = requests.get('http://127.0.0.1:5002/vocab_list', timeout=2)
        print(f"[TEST] ✓ 服务器响应: {response.status_code}")
        print("[TEST] ✅ Flask 服务器成功启动!")
    except Exception as e:
        print(f"[TEST] ⚠ 服务器检查失败: {e}")
        print("[TEST] ⚠ Flask 可能仍在启动中")
    
    print("\n[TEST] 保持运行，按 Ctrl+C 停止...")
    while True:
        time.sleep(1)
    
except Exception as e:
    print(f"\n[TEST] ❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
except KeyboardInterrupt:
    print("\n[TEST] 被用户中断")
    sys.exit(0)
