#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
严格测试：专门测试极长句子的拆分，以及词语识别
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask_app import (
    format_sentences_new, 
    get_chinese_char_count,
    split_by_punctuation,
    split_long_sentence,
    split_long_sentences
)

def test_extreme_long_sentences():
    """测试极长句子（30+字）"""
    print("\n" + "="*80)
    print("【严格测试】极长句子拆分（30+字符）")
    print("="*80)
    
    test_cases = [
        # 30字的句子
        "这是一个包含有三十个汉字左右的长句子，它需要被准确地拆分成不超过十五个字的部分以便进行语音合成处理。",
        
        # 40字的句子
        "中华人民共和国是一个伟大的国家，有着悠久的历史文化传统，是世界上最古老的文明之一，拥有丰富的自然资源和人文景观，是一个充满生机活力的国家。",
        
        # 50字的句子
        "学习汉语是一个长期而又充满挑战的过程，需要我们不断地积累词汇知识，提高语言理解能力，同时还要培养批判性思维和创造性思维能力，才能真正掌握这门语言的精髓。",
    ]
    
    for i, text in enumerate(test_cases, 1):
        char_count = get_chinese_char_count(text)
        print(f"\n🔹 测试 {i}: {char_count}个汉字")
        print(f"   原文: {text}\n")
        
        result = format_sentences_new(text)
        print(f"   ✂️  拆分结果 ({len(result)}个部分):")
        
        max_chars = 0
        all_valid = True
        for j, sentence in enumerate(result, 1):
            sent_count = get_chinese_char_count(sentence)
            max_chars = max(max_chars, sent_count)
            status = "✓" if sent_count <= 15 else "✗"
            if sent_count > 15:
                all_valid = False
            print(f"      {status} [{j:2d}] ({sent_count:2d}字) {sentence}")
        
        print(f"   📊 最大长度: {max_chars}字, 拆分: {'通过 ✓' if all_valid else '失败 ✗'}")

def test_word_vs_sentence_distinction():
    """测试词语识别与句子拆分的区别"""
    print("\n" + "="*80)
    print("【词语识别测试】区分词语和句子")
    print("="*80)
    
    print("""
📝 词语特点:
   - 通常没有标点符号
   - 长度通常较短（1-5个字）
   - 作为整体被学习和记忆
   
📄 句子特点:
   - 包含一个或多个标点符号
   - 长度可能较长（需要拆分）
   - 需要根据长度进行拆分处理
    """)
    
    test_cases = [
        {
            'name': '词语列表',
            'text': '青馬大橋、疾馳、遠眺、俯瞰、怡然',
            'type': '词语'
        },
        {
            'name': '短句列表',
            'text': '我很高兴。你呢。他们都很开心。',
            'type': '句子'
        },
        {
            'name': '长句',
            'text': '这是一个包含了很多汉字的长句子，需要被拆分成多个较短的部分以便语音合成。',
            'type': '句子'
        },
    ]
    
    for case in test_cases:
        text = case['text']
        char_count = get_chinese_char_count(text)
        
        print(f"\n🔹 {case['name']} ({case['type']}, {char_count}字):")
        print(f"   原文: {text}\n")
        
        result = format_sentences_new(text)
        print(f"   ✂️  处理结果 ({len(result)}个部分):")
        
        for j, part in enumerate(result, 1):
            part_count = get_chinese_char_count(part)
            is_word = '词语' in part or (part_count <= 5 and '。' not in part)
            part_type = '词语' if is_word else '句子'
            print(f"      [{j:2d}] ({part_count:2d}字, {part_type:2s}) {part}")

def test_punctuation_handling():
    """测试各种标点符号的正确处理"""
    print("\n" + "="*80)
    print("【标点符号测试】验证所有支持的标点符号")
    print("="*80)
    
    punctuation_cases = [
        ('句号', '这是第一句。这是第二句。', '。'),
        ('问号', '你好吗？我很好。', '？'),
        ('分号', '春天来了；鲜花盛开。', '；'),
        ('冒号', '请注意：这很重要。', '：'),
        ('逗号', '红、黄、蓝，三种颜色。', '，'),
    ]
    
    for name, text, punct in punctuation_cases:
        print(f"\n🔹 {name}（{punct}）:")
        print(f"   原文: {text}")
        
        result = split_by_punctuation(text)
        print(f"   ✂️  按标点分割:")
        for j, part in enumerate(result, 1):
            count = get_chinese_char_count(part)
            print(f"      [{j}] ({count}字) {part}")

def test_edge_cases():
    """测试边界情况"""
    print("\n" + "="*80)
    print("【边界测试】测试特殊情况")
    print("="*80)
    
    cases = [
        ('恰好15字', '这是一个恰好十五个字的句子测试案例'),
        ('恰好16字', '这是一个恰好十六个字的长句子测试案例处'),
        ('5字（最小）', '这是五字句。'),
        ('4字（最小-1）', '这是四字句。'),
        ('无标点长句', '这是一个没有任何标点符号的非常长的句子需要被自动拆分成多个较短的部分'),
        ('混合内容', '词语：书籍、笔、纸张。句子是由多个词语组成的。'),
    ]
    
    for name, text in cases:
        char_count = get_chinese_char_count(text)
        print(f"\n🔹 {name} ({char_count}字):")
        print(f"   原文: {text}\n")
        
        result = format_sentences_new(text)
        print(f"   ✂️  处理结果 ({len(result)}个部分):")
        
        max_chars = 0
        min_chars = float('inf')
        all_valid = True
        
        for j, part in enumerate(result, 1):
            part_count = get_chinese_char_count(part)
            max_chars = max(max_chars, part_count)
            min_chars = min(min_chars, part_count)
            status = "✓" if part_count <= 15 else "✗"
            if part_count > 15:
                all_valid = False
            print(f"      {status} [{j:2d}] ({part_count:2d}字) {part}")
        
        print(f"   📊 范围: {min_chars}-{max_chars}字, 状态: {'通过 ✓' if all_valid else '失败 ✗'}")

def main():
    test_extreme_long_sentences()
    test_word_vs_sentence_distinction()
    test_punctuation_handling()
    test_edge_cases()
    
    print("\n" + "="*80)
    print("✓ 所有严格测试完成！")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
