"""
检查vocabulary_data.json的数据结构变化
帮助决定是否需要更新PythonAnywhere上的数据
"""

import json
import os

# 读取当前的数据文件
with open('vocabulary_data.json', 'r', encoding='utf-8') as f:
    current_data = json.load(f)

print("=" * 80)
print("数据结构分析")
print("=" * 80)

# 检查所有课程
for lesson_name, lesson_data in current_data.items():
    print(f"\n【{lesson_name}】")
    
    # 检查词语数据
    if "詞語" in lesson_data:
        words = lesson_data["詞語"]
        if words:
            print(f"  词语数量: {len(words)}")
            sample_word = words[0]
            print(f"  词语结构: {list(sample_word.keys())}")
    else:
        print("  ⚠️  缺少'詞語'字段")
    
    # 检查段落数据
    if "段落" in lesson_data:
        paragraphs = lesson_data["段落"]
        if paragraphs:
            print(f"  段落数量: {len(paragraphs)}")
            sample_para = paragraphs[0]
            print(f"  段落结构: {list(sample_para.keys())}")
            
            # 检查段落是否有新的字段
            if "attempts" in sample_para and "history" in sample_para:
                print(f"  ✓ 段落有attempts/history字段 (新结构)")
            else:
                print(f"  • 段落没有attempts/history字段 (旧结构)")
            
            # 检查句子结构
            if "sentences" in sample_para and sample_para["sentences"]:
                sample_sentence = sample_para["sentences"][0]
                print(f"  句子结构: {list(sample_sentence.keys())}")
        else:
            print(f"  段落: 空")
    else:
        print("  ⚠️  缺少'段落'字段")

print("\n" + "=" * 80)
print("建议:")
print("=" * 80)
print("""
根据数据分析：

1. 【词语数据】
   - 数据结构没有改变
   - 存储的是学习历史和统计数据
   - 不需要重置，直接保留

2. 【段落数据】
   - 如果网站上的段落数据有 'attempts' 和 'history' 字段
     → 数据结构相同，可以直接同步（git pull）
   
   - 如果网站上的段落数据没有这些字段
     → 需要在PythonAnywhere上手动迁移或重新部署
   
3. 【建议操作】
   
   方案A - 保留网站上的学习数据（推荐）：
   
   a) ssh 进入 PythonAnywhere bash
   b) 备份旧数据：
      cp /home/Lucas2002/vocabulary-learning-assistant/vocabulary_data.json \\
         /home/Lucas2002/vocabulary-learning-assistant/vocabulary_data.json.backup
   
   c) 运行这个迁移脚本on网站上（复制下面的代码到PythonAnywhere）
   
   方案B - 完全重置数据（丢失学习历史）：
   
   a) 直接替换，git pull 后最新的vocabulary_data.json会覆盖旧的
   
   === 数据迁移脚本 ===
""")

print("""
import json
import os

DATA_FILE = '/home/Lucas2002/vocabulary-learning-assistant/vocabulary_data.json'

# 检查是否需要迁移
with open(DATA_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

needs_migration = False

for lesson_name, lesson_data in data.items():
    if "段落" in lesson_data:
        for para in lesson_data["段落"]:
            if "attempts" not in para:
                needs_migration = True
                break

if needs_migration:
    print("检测到需要迁移...")
    
    # 迁移逻辑：为每个段落添加统计数据
    for lesson_name, lesson_data in data.items():
        if "段落" in lesson_data:
            for para in lesson_data["段落"]:
                if "attempts" not in para:
                    # 统计所有句子的学习情况
                    total_attempts = 0
                    total_correct = 0
                    combined_history = []
                    
                    if "sentences" in para:
                        for sentence in para["sentences"]:
                            if "attempts" in sentence:
                                total_attempts += sentence["attempts"]
                            if "correct" in sentence:
                                total_correct += sentence["correct"]
                            if "history" in sentence:
                                combined_history.extend(sentence["history"])
                    
                    # 添加新字段
                    para["attempts"] = total_attempts
                    para["correct"] = total_correct
                    para["history"] = sorted(
                        combined_history, 
                        key=lambda x: x.get("timestamp", "")
                    )
    
    # 保存更新后的数据
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print("✓ 迁移完成！")
else:
    print("✓ 数据结构已经是最新的，无需迁移")
""")
