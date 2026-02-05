#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from flask_app import find_best_split_point, get_chinese_char_count

text = "长的句子需要被自动拆分成多个较短的部分"
print(f"Text: {text}")
print(f"Length: {len(text)} chars, {get_chinese_char_count(text)} Chinese chars")

split_point = find_best_split_point(text)
print(f"Split point: {split_point}")

if split_point > 0 and split_point < len(text):
    part1 = text[:split_point]
    part2 = text[split_point:]
    print(f"Part1: {part1} ({get_chinese_char_count(part1)} chars)")
    print(f"Part2: {part2} ({get_chinese_char_count(part2)} chars)")
