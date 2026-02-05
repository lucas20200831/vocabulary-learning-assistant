#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试新的段落拆分逻辑"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask_app import (
    get_chinese_char_count,
    split_by_punctuation,
    split_long_sentence,
    split_long_sentences,
    format_sentences_new
)

def test_chinese_char_count():
    """测试汉字计数"""
    print("="*60)
    print("测试1：汉字计数")
    print("="*60)
    
    tests = [
        ("你好", 2),
        ("你好吗？", 3),  # 只计汉字，不计标点
        ("Hello世界123", 2),  # 只计汉字
        ("登鸕鷀樓王之渙白日依山盡黃河入海流欲窮千里目更上一層樓", 26),
    ]
    
    for text, expected in tests:
        result = get_chinese_char_count(text)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{text}' -> {result} (期望: {expected})")

def test_split_by_punctuation():
    """测试按标点分割"""
    print("\n" + "="*60)
    print("测试2：按标点分割")
    print("="*60)
    
    text = "登鸕鷀樓。王之渙。白日依山盡。黃河入海流。"
    result = split_by_punctuation(text)
    print(f"输入: {text}")
    print(f"输出: {result}")
    for i, sent in enumerate(result, 1):
        count = get_chinese_char_count(sent)
        print(f"  [{i}] ({count}字) {sent}")

def test_split_long_sentence():
    """测试长句拆分"""
    print("\n" + "="*60)
    print("测试3：长句拆分")
    print("="*60)
    
    # 测试用例：长度超过15字的句子
    long_sentence = "登鸕鷀樓王之渙白日依山盡黃河入海流欲窮千里目更上一層樓。"
    print(f"输入 ({get_chinese_char_count(long_sentence)}字): {long_sentence}")
    
    result = split_long_sentence(long_sentence)
    print(f"拆分结果 ({len(result)} 个部分):")
    for i, sent in enumerate(result, 1):
        count = get_chinese_char_count(sent)
        print(f"  [{i}] ({count}字) {sent}")

def test_format_sentences_new():
    """测试完整的段落格式化"""
    print("\n" + "="*60)
    print("测试4：完整段落格式化")
    print("="*60)
    
    # 测试用例1：短句和长句的混合
    text1 = "这是一个短句。这是一个非常长的句子包含了很多汉字需要被拆分成多个部分以确保每部分都不超过十五个汉字。最后是个短句。"
    print(f"\n用例1 ({get_chinese_char_count(text1)}字):")
    print(f"输入: {text1}")
    result1 = format_sentences_new(text1)
    print(f"输出 ({len(result1)} 个句子):")
    for i, sent in enumerate(result1, 1):
        count = get_chinese_char_count(sent)
        print(f"  [{i}] ({count}字) {sent}")
    
    # 测试用例2：古文
    text2 = "登鸕鷀樓。王之渙。白日依山盡，黃河入海流；欲窮千里目，更上一層樓。"
    print(f"\n用例2 ({get_chinese_char_count(text2)}字):")
    print(f"输入: {text2}")
    result2 = format_sentences_new(text2)
    print(f"输出 ({len(result2)} 个句子):")
    for i, sent in enumerate(result2, 1):
        count = get_chinese_char_count(sent)
        print(f"  [{i}] ({count}字) {sent}")

def main():
    test_chinese_char_count()
    test_split_by_punctuation()
    test_split_long_sentence()
    test_format_sentences_new()
    
    print("\n" + "="*60)
    print("✓ 所有测试完成！")
    print("="*60)

if __name__ == '__main__':
    main()
