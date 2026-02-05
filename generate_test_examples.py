#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成测试示例课程 - 用于浏览器中测试段落拆分功能
"""

import json
from datetime import datetime

# 示例课程数据
example_lessons = {
    "测试课程_拆分功能": {
        "詞語": [
            {"word": "青马大桥", "meaning": "香港跨海大桥", "attempts": 0, "correct": 0, "incorrect": 0, "history": []},
            {"word": "疾驰", "meaning": "快速行驶", "attempts": 0, "correct": 0, "incorrect": 0, "history": []},
            {"word": "壮观", "meaning": "景象气势宏大", "attempts": 0, "correct": 0, "incorrect": 0, "history": []},
        ],
        "段落": [
            {
                "title": "短句示例（无需拆分）",
                "sentences": [
                    "我很高兴。",
                    "天气很好。",
                    "今天是个好天气。"
                ],
                "attempts": 0,
                "correct": 0,
                "incorrect": 0,
                "history": []
            },
            {
                "title": "中等长句（需要拆分）",
                "sentences": [
                    "这是一个包含很多汉字的相对较长的句子。",
                    "我们都知道跨越伟大的海洋需要非常坚强的意志。"
                ],
                "attempts": 0,
                "correct": 0,
                "incorrect": 0,
                "history": []
            },
            {
                "title": "超长句示例（递归拆分）",
                "sentences": [
                    "这是一个没有任何标点符号的非常长的句子需要被自动拆分成多个较短的部分以确保每部分都不超过十五个汉字。",
                    "青马大桥是连接香港新界西北部的青衣岛与香港岛东北部的马湾半岛的一座跨海大桥，完成后成为世界上最长的混合交通大桥。"
                ],
                "attempts": 0,
                "correct": 0,
                "incorrect": 0,
                "history": []
            },
            {
                "title": "混合标点示例",
                "sentences": [
                    "书包。这是一个非常长的句子需要被拆分成多个部分。",
                    "你好吗？这是一个很长的句子包含了很多汉字需要拆分。",
                    "第一部分；第二部分包含了非常多的汉字需要被自动拆分。"
                ],
                "attempts": 0,
                "correct": 0,
                "incorrect": 0,
                "history": []
            }
        ]
    }
}

def add_example_to_existing():
    """将示例课程添加到现有的vocabulary_data.json"""
    try:
        # 读取现有数据
        with open('vocabulary_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 添加示例课程
        data.update(example_lessons)
        
        # 保存回去
        with open('vocabulary_data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print("✅ 示例课程已添加到 vocabulary_data.json")
        print(f"   课程名: 测试课程_拆分功能")
        print(f"   词语数: 3 个")
        print(f"   段落数: 4 个")
        print(f"   包含示例:")
        print(f"   - 短句（无需拆分）")
        print(f"   - 中等长句（需要拆分）")
        print(f"   - 超长句（递归拆分）")
        print(f"   - 混合标点")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False
    
    return True

def create_new_data():
    """创建新的vocabulary_data.json（如果不存在）"""
    try:
        with open('vocabulary_data.json', 'w', encoding='utf-8') as f:
            json.dump(example_lessons, f, ensure_ascii=False, indent=2)
        
        print("✅ 已创建新的 vocabulary_data.json")
        print(f"   示例课程: 测试课程_拆分功能")
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False
    
    return True

if __name__ == "__main__":
    import os
    
    print("="*70)
    print("  生成测试示例课程")
    print("="*70)
    print()
    
    if os.path.exists('vocabulary_data.json'):
        print("发现现有 vocabulary_data.json，添加示例课程...")
        if add_example_to_existing():
            print()
            print("✨ 生成完成！")
            print()
            print("接下来的步骤:")
            print("1. 运行: python flask_app.py")
            print("2. 打开浏览器: http://127.0.0.1:5002")
            print("3. 选择课程: 测试课程_拆分功能")
            print("4. 点击编辑: 编辑课程内容")
            print("5. 查看拆分效果")
            print()
    else:
        print("未找到 vocabulary_data.json，创建新文件...")
        if create_new_data():
            print()
            print("✨ 生成完成！")
            print()
            print("接下来的步骤:")
            print("1. 运行: python flask_app.py")
            print("2. 打开浏览器: http://127.0.0.1:5002")
            print("3. 选择课程: 测试课程_拆分功能")
            print("4. 查看词语和段落")
            print()
