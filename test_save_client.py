#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用 Flask test client 直接测试保存功能
"""

import json
import sys
import os

os.chdir(r'd:\Education_Lucas\vocabulary-learning-assistant')

print("[TEST] Using Flask test client for save_content...")

try:
    from flask_app import app, format_sentences_new
    
    # 创建测试客户端
    client = app.test_client()
    
    print("[TEST] Preparing test data...")
    
    # 段落内容
    paragraphs_content = {
        "短句示例": "青马大桥很壮观。我们乘坐快速列车。",
        "中等长句": "我们乘坐着快速列车，沿着青马大桥向前疾驰而去。壮观的景色展现在我们眼前。",
        "混合标点示例": "青马大桥向前延伸，疾驰而去。我们乘坐着快速列车，感受着壮观的景色。"
    }
    
    # 准备保存数据
    post_data = {
        "language": "中文",
        "lesson": "测试课程_拆分功能",
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
    
    print(f"\n[TEST] Sending POST to /save_content...")
    print(f"[TEST] Data: {len(post_data['words'])} words, {len(post_data['paragraphs'])} paragraphs")
    
    # 发送 POST 请求
    response = client.post(
        '/save_content',
        data=json.dumps(post_data),
        content_type='application/json'
    )
    
    print(f"\n[TEST] Response status: {response.status_code}")
    print(f"[TEST] Response type: {response.content_type}")
    
    try:
        result = response.get_json()
        print(f"\n[TEST] Response JSON:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        if response.status_code == 200 and result.get('status') == 'success':
            print(f"\n[TEST] SUCCESS! Save completed!")
        else:
            print(f"\n[TEST] FAILED! Status code: {response.status_code}")
            print(f"[TEST] Status from response: {result.get('status')}")
            
            if 'message' in result:
                print(f"[TEST] Message: {result['message']}")
            
            if 'traceback' in result:
                print(f"\n[TEST] Full traceback:")
                print(result['traceback'])
    except Exception as e:
        print(f"\n[TEST] Error parsing response: {e}")
        print(f"[TEST] Raw response: {response.data}")
    
except Exception as e:
    print(f"\n[TEST] Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n[TEST] Done")
