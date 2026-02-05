#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask_app import format_sentences_new, get_chinese_char_count

# Test case with 34 characters
text = "这是一个没有任何标点符号的非常长的句子需要被自动拆分成多个较短的部分"
char_count = get_chinese_char_count(text)
result = format_sentences_new(text)

print(f"Original text ({char_count} chars): {text}")
print(f"Split into {len(result)} parts:")

all_valid = True
for i, part in enumerate(result, 1):
    part_count = get_chinese_char_count(part)
    status = "PASS" if part_count <= 15 else "FAIL"
    if part_count > 15:
        all_valid = False
    print(f"  [{i}] ({part_count:2d} chars) {status}: {part}")

print(f"\nOverall: {'PASS' if all_valid else 'FAIL'}")
print(f"Max length: {max(get_chinese_char_count(p) for p in result)} chars")
