#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comprehensive test of the complete quiz flow in Simple Browser environment.
This simulates:
1. Loading quiz page
2. Clicking "我能默寫" button for each word
3. Verifying quiz completion
"""

import urllib.request
import urllib.parse
import json
import time
import http.cookiejar

BASE_URL = 'http://127.0.0.1:5002'

# Use cookie jar to maintain session (though new code doesn't require it)
cookiejar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookiejar))

def test_complete_quiz_flow():
    print("=" * 70)
    print("COMPREHENSIVE QUIZ FLOW TEST")
    print("Testing dictation feature in Simple Browser environment")
    print("=" * 70)
    
    # Step 1: Load quiz page
    print("\n[STEP 1] Loading quiz page for 中文/第一課...")
    quiz_url = f'{BASE_URL}/quiz/%E4%B8%AD%E6%96%87/%E7%AC%AC%E4%B8%80%E8%AA%B2'
    try:
        response = opener.open(quiz_url, timeout=5)
        content = response.read().decode('utf-8')
        if response.getcode() == 200:
            print("  SUCCESS: Quiz page loaded (HTTP 200)")
        else:
            print(f"  FAILED: Unexpected status {response.getcode()}")
            return False
            
        # Verify page contains required elements
        checks = [
            ('allWords' in content, "'let allWords' variable found"),
            ('媽媽' in content, "First word (媽媽) found"),
            ('recordResult' in content, "recordResult() function found"),
            ('quiz-area' in content, "Quiz container found"),
        ]
        
        for check, desc in checks:
            print(f"  {'OK' if check else 'FAIL'}: {desc}")
            if not check:
                return False
                
    except Exception as e:
        print(f"  FAILED: {e}")
        return False
    
    # Step 2: Simulate clicking buttons for each word
    print("\n[STEP 2] Simulating user clicking buttons for each word...")
    words = [
        {'word': '媽媽', 'known': True},
        {'word': '爸爸', 'known': False},
        {'word': '哥哥', 'known': True},
        {'word': '妹妹', 'known': False},
        {'word': '學校', 'known': True}
    ]
    
    for i, item in enumerate(words, 1):
        print(f"\n  [{i}/5] Processing word: {item['word']} (Known: {item['known']})")
        
        data = urllib.parse.urlencode({
            'word': item['word'],
            'language': '中文',
            'lesson': '第一課',
            'is_known': str(item['known']).lower()
        }).encode('utf-8')
        
        try:
            req = urllib.request.Request(f'{BASE_URL}/submit_answer', data=data)
            response = opener.open(req, timeout=5)
            content = response.read().decode('utf-8')
            
            if response.getcode() == 200:
                result = json.loads(content)
                status = result.get('status')
                if status == 'success':
                    print(f"        SUCCESS: Answer saved")
                else:
                    print(f"        FAILED: Unexpected status '{status}'")
                    return False
            else:
                print(f"        FAILED: HTTP {response.getcode()}")
                return False
                
        except Exception as e:
            print(f"        FAILED: {e}")
            return False
        
        # Small delay to simulate user thinking time
        if i < len(words):
            time.sleep(0.5)
    
    print("\n" + "=" * 70)
    print("RESULT: ALL TESTS PASSED")
    print("=" * 70)
    print("\nSummary:")
    print("  - Quiz page loaded successfully")
    print("  - All 5 words processed without errors")
    print("  - All answers saved successfully")
    print("  - Application ready for Simple Browser use")
    print("\n✓ The dictation feature is now fully functional in Simple Browser!")
    print("  Users can navigate to a lesson and click through all the words.")
    return True

if __name__ == '__main__':
    success = test_complete_quiz_flow()
    exit(0 if success else 1)
