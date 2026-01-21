"""
迁移脚本：将段落数据从嵌套结构转换为扁平化结构
旧结构: 段落 -> title + sentences (每个句子包含attempts/correct/incorrect)
新结构: 段落 -> 每个段落是独立项，有自己的attempts/correct/incorrect
"""

import json
import os
from datetime import datetime

DATA_FILE = 'vocabulary_data.json'

def migrate_paragraphs():
    """将现有段落数据迁移到新结构"""
    if not os.path.exists(DATA_FILE):
        print(f"{DATA_FILE} 不存在，跳过迁移。")
        return
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    migrated = False
    
    for language in data:
        for lesson_num in data[language]:
            lesson_content = data[language][lesson_num]
            
            # 检查是否需要迁移段落
            if '段落' in lesson_content and isinstance(lesson_content['段落'], list):
                old_paragraphs = lesson_content['段落']
                
                # 检查是否已经是新格式（有 'id' 字段）
                if len(old_paragraphs) > 0 and 'id' not in old_paragraphs[0]:
                    print(f"迁移 {language}/{lesson_num} 中的段落...")
                    
                    new_paragraphs = []
                    for idx, para in enumerate(old_paragraphs):
                        para_id = f"para_{idx+1}"
                        
                        # 创建新段落对象
                        new_para = {
                            'id': para_id,
                            'title': para.get('title', f'段落{idx+1}'),
                            'sentences': para.get('sentences', []),
                            'attempts': 0,
                            'correct': 0,
                            'incorrect': 0,
                            'history': []
                        }
                        
                        new_paragraphs.append(new_para)
                    
                    lesson_content['段落'] = new_paragraphs
                    migrated = True
    
    if migrated:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("✓ 段落数据迁移完成！")
    else:
        print("✓ 段落数据已是最新格式，无需迁移。")

if __name__ == '__main__':
    migrate_paragraphs()
