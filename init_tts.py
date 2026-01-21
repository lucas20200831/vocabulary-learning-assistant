#!/usr/bin/env python3
"""
初始化脚本：为现有库中的所有词语和段落生成 gTTS 音频
"""
import json
import os
import hashlib
import time
from gtts import gTTS

# 配置
DATA_FILE = 'vocabulary_data.json'
AUDIO_DIR = os.path.join('static', 'audio')

# 确保音频目录存在
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)
    print(f"创建音频目录: {AUDIO_DIR}")

# 加载数据
print("加载词汇数据...")
with open(DATA_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

# 收集所有需要生成的文本
texts_to_generate = []
lesson_info = {}

print("\n扫描所有课程和内容...")
for lesson_name, lesson_content in data.items():
    if not isinstance(lesson_content, dict):
        continue
    
    lesson_texts = []
    
    # 收集词语
    words = lesson_content.get('詞語', [])
    for word_obj in words:
        word = word_obj.get('word', '').strip()
        if word:
            texts_to_generate.append(word)
            lesson_texts.append(word)
    
    # 收集段落中的句子
    paragraphs = lesson_content.get('段落', [])
    for para_obj in paragraphs:
        sentences = para_obj.get('sentences', [])
        for sent_obj in sentences:
            sent = sent_obj.get('sentence', '').strip()
            if sent:
                texts_to_generate.append(sent)
                lesson_texts.append(sent)
    
    if lesson_texts:
        lesson_info[lesson_name] = {
            'words': len(words),
            'paragraphs': len(paragraphs),
            'texts': len(lesson_texts)
        }
        print(f"  {lesson_name}: {len(words)} 词语 + {len(lesson_texts) - len(words)} 句子")

print(f"\n总计: {len(texts_to_generate)} 个文本需要生成语音")

# 去重
unique_texts = list(set(texts_to_generate))
print(f"去重后: {len(unique_texts)} 个独特文本")

# 生成语音
print(f"\n开始生成语音 (使用 gTTS)...\n")
generated_count = 0
skipped_count = 0
start_time = time.time()

for i, text in enumerate(unique_texts, 1):
    try:
        # 生成文件名
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        audio_file = os.path.join(AUDIO_DIR, f'{text_hash}.mp3')
        
        # 检查是否已存在
        if os.path.exists(audio_file):
            skipped_count += 1
            status = "✓ 已存在"
        else:
            # 生成音频
            tts = gTTS(text=text, lang='zh-CN', slow=False)
            tts.save(audio_file)
            generated_count += 1
            status = "✓ 已生成"
        
        # 进度显示
        print(f"[{i}/{len(unique_texts)}] {status} | {text[:30]}...")
        
        # 每生成5个文件暂停一下，避免网络过载
        if generated_count % 5 == 0:
            time.sleep(0.5)
    
    except Exception as e:
        print(f"[{i}/{len(unique_texts)}] ✗ 错误 | {text[:30]}... | {str(e)}")

elapsed_time = time.time() - start_time

# 输出统计信息
print(f"\n{'='*60}")
print(f"初始化完成!")
print(f"{'='*60}")
print(f"生成新文件: {generated_count}")
print(f"跳过已有: {skipped_count}")
print(f"总文件数: {generated_count + skipped_count}")
print(f"耗时: {elapsed_time:.1f} 秒")
print(f"平均速度: {len(unique_texts)/elapsed_time:.1f} 文件/秒")
print(f"\n课程统计:")
for lesson_name, info in sorted(lesson_info.items()):
    print(f"  {lesson_name}: {info['words']} 词语 + {info['texts'] - info['words']} 句子 = {info['texts']} 个语音")

print(f"\n✅ 所有语音已生成完毕，可以开始使用听写功能!")
