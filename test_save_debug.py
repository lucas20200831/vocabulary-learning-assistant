#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""调试保存功能"""

import sys
import json
from flask_app import format_sentences_new, get_chinese_char_count

test_text = "这是一个包含很多汉字的相对较长的句子。"
print(f"输入: {test_text}")
print(f"汉字数: {get_chinese_char_count(test_text)}")

try:
    result = format_sentences_new(test_text)
    print(f"\n拆分结果: {result}")
    print(f"拆分结果类型: {type(result)}")
    print(f"结果长度: {len(result) if result else 0}")
    
    if result:
        print("\n详细信息:")
        for i, sent in enumerate(result, 1):
            count = get_chinese_char_count(sent)
            print(f"  [{i}] {repr(sent)}")
            print(f"      长度: {len(sent)}, 汉字: {count}字")
    
    # 模拟保存格式
    print("\n模拟保存的 JSON 格式:")
    test_paragraphs = [
        {
            "title": "测试段落",
            "sentences": result
        }
    ]
    print(json.dumps(test_paragraphs, ensure_ascii=False, indent=2))
    
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
