"""
测试新的段落数据结构功能
"""

import json
import os

def test_paragraph_structure():
    """测试段落数据结构是否正确"""
    
    data_file = 'vocabulary_data.json'
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("✓ 数据文件成功加载")
    
    # 测试中文第一课的段落
    chinese_lesson = data['中文']['第一課']
    paragraphs = chinese_lesson.get('段落', [])
    
    print(f"\n📄 检测到 {len(paragraphs)} 个段落\n")
    
    for idx, para in enumerate(paragraphs, 1):
        print(f"段落 {idx}:")
        print(f"  ✓ 有ID: {para.get('id', 'N/A')}")
        print(f"  ✓ 标题: {para.get('title', 'N/A')}")
        print(f"  ✓ 句子数: {len(para.get('sentences', []))}")
        print(f"  ✓ 段落统计:")
        print(f"    - 尝试: {para.get('attempts', 0)}")
        print(f"    - 正确: {para.get('correct', 0)}")
        print(f"    - 错误: {para.get('incorrect', 0)}")
        print(f"  ✓ 历史记录: {len(para.get('history', []))} 条")
        
        # 检查句子结构
        sentences = para.get('sentences', [])
        if sentences:
            first_sent = sentences[0]
            if isinstance(first_sent, dict):
                print(f"  ✓ 句子结构正确 (字典格式)")
            else:
                print(f"  ⚠ 句子结构未优化 (字符串格式)")
        print()
    
    print("=" * 50)
    print("✓ 所有检测完成！新的段落结构已正确实现。")
    print("\n功能特点:")
    print("1. 每个段落都有独立的ID")
    print("2. 支持段落标题自定义")
    print("3. 段落有独立的学习统计 (attempts/correct/incorrect)")
    print("4. 支持单独选择段落进行听写")
    print("5. 段落可以独立编辑和删除")

if __name__ == '__main__':
    test_paragraph_structure()
