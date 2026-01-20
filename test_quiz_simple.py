#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test script to verify quiz functionality"""

import urllib.request
import urllib.parse
import json
import http.cookiejar

BASE_URL = 'http://127.0.0.1:5002'

# Create cookie jar to maintain session
cookiejar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookiejar))

def test_quiz_flow():
    """Test the complete quiz flow"""
    
    print("=" * 60)
    print("Testing Quiz Flow")
    print("=" * 60)
    
    # Step 1: Get the vocab_list page (initializes session)
    print("\n1. Loading quiz page for 中文/第一課...")
    quiz_url = f'{BASE_URL}/quiz/%E4%B8%AD%E6%96%87/%E7%AC%AC%E4%B8%80%E8%AA%B2'
    try:
        response = opener.open(quiz_url)
        content = response.read().decode('utf-8')
        print(f"   Status: {response.status}")
        
        # Check if words are in the response
        if '"媽媽"' in content or '媽媽' in content:
            print("   ✓ First word (媽媽) found in page")
            print("   ✓ Page loaded successfully")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    
    # Step 2: Submit answer for first word
    print("\n2. Submitting answer for word 1 (媽媽)...")
    data = urllib.parse.urlencode({
        'word': '媽媽',
        'language': '中文',
        'lesson': '第一課',
        'is_known': 'true'
    }).encode('utf-8')
    
    try:
        req = urllib.request.Request(f'{BASE_URL}/submit_answer', data=data)
        response = opener.open(req)
        content = response.read().decode('utf-8')
        print(f"   Status: {response.status}")
        result = json.loads(content)
        print(f"   Response: {result}")
        if result.get('status') == 'success':
            print("   ✓ Answer submitted successfully")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    
    # Step 3-6: Submit remaining answers
    words = ['爸爸', '哥哥', '妹妹', '學校']
    for i, word in enumerate(words, 2):
        print(f"\n{1+i}. Submitting answer for word {i} ({word})...")
        data = urllib.parse.urlencode({
            'word': word,
            'language': '中文',
            'lesson': '第一課',
            'is_known': 'true' if i % 2 == 0 else 'false'
        }).encode('utf-8')
        
        try:
            req = urllib.request.Request(f'{BASE_URL}/submit_answer', data=data)
            response = opener.open(req)
            content = response.read().decode('utf-8')
            print(f"   Status: {response.status}")
            result = json.loads(content)
            print(f"   Response: {result.get('message', 'Success')}")
        except Exception as e:
            print(f"   ✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Quiz flow test completed!")
    print("=" * 60)

if __name__ == '__main__':
    test_quiz_flow()
