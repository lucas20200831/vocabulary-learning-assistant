#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟前端发送保存请求
"""

import requests
import json
from flask_app import format_sentences_new

# 测试课程信息
lesson = "测试课程_拆分功能"
language = "中文"

# 段落内容
paragraphs_content = {
    "短句示例（无需拆分）": "青马大桥很壮观。我们乘坐快速列车。",
    "中等长句（需要拆分）": "我们乘坐着快速列车，沿着青马大桥向前疾驰而去。壮观的景色展现在我们眼前。",
    "混合标点示例": "青马大桥向前延伸，疾驰而去。我们乘坐着快速列车，感受着壮观的景色。"
}

# 准备保存数据
post_data = {
    "language": language,
    "lesson": lesson,
    "words": ["青马大桥", "疾驰", "壮观"],
    "paragraphs": [],
    "is_simple": True
}

# 对每个段落进行拆分
for title, content in paragraphs_content.items():
    sentences = format_sentences_new(content)
    post_data["paragraphs"].append({
        "title": title,
        "sentences": sentences
    })

print("=" * 60)
print("[SAVE] Simulating frontend save request")
print("=" * 60)
print(f"\nURL: http://127.0.0.1:5002/save_content")
print(f"Method: POST")
print(f"\nRequest body:")
print(json.dumps(post_data, ensure_ascii=False, indent=2))

try:
    print(f"\n[SAVE] Sending request...")
    response = requests.post(
        'http://127.0.0.1:5002/save_content',
        json=post_data,
        timeout=60
    )
    
    print(f"\n[SAVE] Response status code: {response.status_code}")
    print(f"[SAVE] Response content-type: {response.headers.get('content-type')}")
    
    try:
        result = response.json()
        print(f"\n[SAVE] Response JSON:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        if response.status_code == 200 and result.get('status') == 'success':
            print(f"\n[SAVE] SUCCESS! Save completed!")
        else:
            print(f"\n[SAVE] FAILED! Save did not succeed!")
            if 'traceback' in result:
                print(f"\n[SAVE] Traceback:")
                print(result['traceback'])
    except json.JSONDecodeError:
        print(f"\n[SAVE] Response is not JSON:")
        print(response.text)
    
except requests.exceptions.ConnectionError as e:
    print(f"\n[SAVE] Connection error: {e}")
    print(f"       Make sure Flask is running on http://127.0.0.1:5002")
except requests.exceptions.Timeout:
    print(f"\n[SAVE] Request timeout")
except Exception as e:
    print(f"\n[SAVE] Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
