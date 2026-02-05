#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动 Flask 应用，并让它持续运行
"""

import sys
import os
import time

os.chdir(r'd:\Education_Lucas\vocabulary-learning-assistant')

try:
    print("[INIT] Importing flask_app...")
    from flask_app import app
    print("[INIT] Flask app imported successfully!")
    
    print("\n[INIT] Starting Flask development server...")
    print("[INIT] Server will run on http://127.0.0.1:5002")
    print("[INIT] Open your browser and navigate to: http://127.0.0.1:5002/vocab_list")
    print("[INIT] Press Ctrl+C to stop\n")
    
    # Don't use reloader to prevent TTS thread issues
    # The debug=False prevents automatic restarts
    app.run(
        debug=False, 
        host='127.0.0.1', 
        port=5002, 
        use_reloader=False,
        threaded=True  # Allow multiple concurrent requests
    )
    
except KeyboardInterrupt:
    print("\n[SHUTDOWN] Server stopped by user")
    sys.exit(0)
except Exception as e:
    print(f"\n[ERROR] Failed to start server: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
