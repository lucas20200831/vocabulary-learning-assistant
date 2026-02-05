#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
移除 flask_app.py 中的所有特殊字符
"""

with open('flask_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换所有特殊字符
replacements = {
    '✓': '[OK]',
    '✗': '[FAIL]',
    '❌': '[ERROR]',
    '⚠': '[WARN]',
    '●': '●'
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open('flask_app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('[OK] Replaced all special characters')
