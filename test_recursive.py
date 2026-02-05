#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask_app import split_long_sentence, get_chinese_char_count

# Test the problematic sentence
sentence = "长的句子需要被自动拆分成多个较短的部分"
print(f"Testing: {sentence}")
print(f"Chinese count: {get_chinese_char_count(sentence)}")

result = split_long_sentence(sentence)
print(f"Result: {len(result)} parts")
for i, part in enumerate(result, 1):
    count = get_chinese_char_count(part)
    print(f"  [{i}] ({count} chars): {part}")
