#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""快速测试极长句子的拆分"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask_app import format_sentences_new, get_chinese_char_count

# 测试30+字的句子
test_cases = [
    ("30字句子", "这是一个包含有三十个汉字左右的长句子需要被准确地拆分成不超过十五个字的部分以便进行语音合成处理"),
    ("40字句子", "中华人民共和国是一个伟大的国家有着悠久的历史文化传统是世界上最古老的文明之一拥有丰富的自然资源和人文景观"),
    ("无标点34字", "这是一个病有任何标点符号的非常长的句子需要被自动拆分成多个较短的部分"),
]

print("\n" + "="*70)
print("极长句子拆分测试（无标点）")
print("="*70 + "\n")

for name, text in test_cases:
    char_count = get_chinese_char_count(text)
    result = format_sentences_new(text)
    
    print(f"📝 {name} ({char_count}字):")
    print(f"   原文: {text}\n")
    
    max_len = 0
    all_valid = True
    for i, part in enumerate(result, 1):
        part_count = get_chinese_char_count(part)
        max_len = max(max_len, part_count)
        status = "✓" if part_count <= 15 else "✗"
        if part_count > 15:
            all_valid = False
        print(f"   {status} [{i}] ({part_count:2d}字) {part}")
    
    print(f"   结果: {'通过 ✓' if all_valid else '失败 ✗'} (最长{max_len}字)\n")

print("="*70)
