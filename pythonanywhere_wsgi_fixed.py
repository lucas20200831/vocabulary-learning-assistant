# ============================================================================
# 改进的PythonAnywhere WSGI配置 - 解决路径和加载问题
# ============================================================================
# 这个文件应该保存在PythonAnywhere的：
# /var/www/lucas2002_pythonanywhere_com_wsgi.py
# ============================================================================

import sys
import os

# 设置项目路径
project_home = '/home/Lucas2002/vocabulary-learning-assistant'

# 确保项目路径在module search path的最前面
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# 设置环境变量
os.environ['FLASK_ENV'] = 'production'

# 调试日志
print(f"[WSGI] Project home: {project_home}")
print(f"[WSGI] sys.path: {sys.path[:3]}")
print(f"[WSGI] Current directory: {os.getcwd()}")

try:
    # 导入Flask应用
    from flask_app import app
    print("[WSGI] Successfully imported flask_app")
    
    # WSGI应用对象
    application = app
    print("[WSGI] WSGI application configured successfully")
    
except ImportError as e:
    print(f"[WSGI] ERROR: Failed to import flask_app: {e}")
    import traceback
    traceback.print_exc()
    raise
except Exception as e:
    print(f"[WSGI] ERROR: Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    raise
