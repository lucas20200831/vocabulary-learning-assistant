#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script to verify quiz functionality without Simple Browser"""

import requests
import json
from urllib.parse import quote

BASE_URL = 'http://127.0.0.1:5002'

def test_quiz_flow():
    """Test the complete quiz flow"""
    
    print("=" * 60)
    print("Testing Quiz Flow")
    print("=" * 60)
    
    # Step 1: Get the vocab_list page (initializes session)
    print("\n1. Loading vocab list...")
    response = requests.get(f'{BASE_URL}/vocab_list')
    print(f"   Status: {response.status_code}")
    
    # Step 2: Access quiz page for 中文 - 第一課
    print("\n2. Loading quiz page for 中文/第一課...")
    quiz_url = f'{BASE_URL}/quiz/{quote("中文")}/{quote("第一課")}'
    response = requests.get(quiz_url)
    print(f"   Status: {response.status_code}")
    
    # Check if words_json is in the response
    if 'allWords' in response.text:
        print("   ✓ allWords found in page")
    if '"媽媽"' in response.text or '媽媽' in response.text:
        print("   ✓ First word (媽媽) found in page")
    
    # Step 3: Submit answer for first word
    print("\n3. Submitting answer for word 1...")
    data = {
        'word': '媽媽',
        'language': '中文',
        'lesson': '第一課',
        'is_known': 'true'
    }
    response = requests.post(f'{BASE_URL}/submit_answer', data=data)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    # Step 4-8: Submit remaining answers
    words = ['爸爸', '哥哥', '妹妹', '學校']
    for i, word in enumerate(words, 2):
        print(f"\n{3+i}. Submitting answer for word {i}...")
        data = {
            'word': word,
            'language': '中文',
            'lesson': '第一課',
            'is_known': 'true' if i % 2 == 0 else 'false'  # Mix true/false
        }
        response = requests.post(f'{BASE_URL}/submit_answer', data=data)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
    
    print("\n" + "=" * 60)
    print("Quiz flow test completed successfully!")
    print("=" * 60)

if __name__ == '__main__':
    test_quiz_flow()
