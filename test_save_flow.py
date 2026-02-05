#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试整个保存流程 - 模拟前端发送的数据
"""

import json
from flask_app import format_sentences_new, get_chinese_char_count

# 模拟前端的 formatSentences 结果
# 使用测试课程中的段落
test_paragraph_content = """青马大桥向前延伸，疾驰而去。我们乘坐着快速列车，感受着壮观的景色。"""

print("=" * 60)
print("🔍 调试保存流程")
print("=" * 60)

print(f"\n原始段落内容:")
print(f"  {repr(test_paragraph_content)}")

# 模拟前端的 formatSentences
sentences = format_sentences_new(test_paragraph_content)

print(f"\n✓ 拆分后的句子数: {len(sentences)}")
for i, sent in enumerate(sentences, 1):
    count = get_chinese_char_count(sent)
    print(f"  [{i}] {repr(sent)}")
    print(f"       长度: {len(sent)}, 汉字: {count}字")

# 模拟前端发送的 JSON 数据结构
post_data = {
    "language": "中文",
    "lesson": "测试课程_拆分功能",
    "words": ["青马大桥", "疾驰", "壮观"],
    "paragraphs": [
        {
            "title": "混合标点示例",
            "sentences": sentences
        }
    ],
    "is_simple": True
}

print(f"\n📤 前端将发送以下 JSON:")
print(json.dumps(post_data, ensure_ascii=False, indent=2))

print(f"\n✅ 数据格式检查:")
print(f"  - 语言: {post_data['language']} ✓")
print(f"  - 课程: {post_data['lesson']} ✓")
print(f"  - 词语数: {len(post_data['words'])} ✓")
print(f"  - 段落数: {len(post_data['paragraphs'])} ✓")

for i, para in enumerate(post_data['paragraphs'], 1):
    print(f"\n段落 {i}:")
    print(f"  - 标题: {para['title']}")
    print(f"  - 句子数: {len(para['sentences'])}")
    print(f"  - 句子类型:")
    for j, sent in enumerate(para['sentences'], 1):
        print(f"    [{j}] {type(sent).__name__}: {repr(sent)}")
        
        # 检查是否有任何问题
        if not isinstance(sent, str):
            print(f"        ⚠️  ERROR: Not a string! Type: {type(sent)}")
        elif not sent:
            print(f"        ⚠️  ERROR: Empty string!")
        elif not sent.strip():
            print(f"        ⚠️  ERROR: Only whitespace!")
        else:
            print(f"        ✓ Valid")

print("\n" + "=" * 60)
print("✅ 保存流程检查完成")
print("=" * 60)
