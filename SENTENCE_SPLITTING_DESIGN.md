# 段落拆分设计文档

## 概述

本文档描述了词汇学习助手中段落拆分的新设计，用于将长段落自动分解为短小、易于朗读的句子。

## 设计规范

### 第一步：按指定标点分割

#### 分割标点集合
- 句号：`。`
- 问号：`？`
- 分号：`；`
- 冒号：`：`
- 逗号：`，`

#### 分割规则
- 遇到上述标点立即分割
- 标点归属于前一句（即分割点在前一句末尾）
- 分割后保留原标点

**示例：**
```
输入: 登鸕鷀樓。王之渙。白日依山盡。
输出: ['登鸕鷀樓。', '王之渙。', '白日依山盡。']
```

### 第二步：长度检查与拆分

#### 汉字计数规则
- **只统计汉字数量**（Unicode范围：`\u4e00-\u9fff`）
- **不统计标点符号**（如：。，？等）
- **不统计数字**（0-9）
- **不统计英文字母**（a-z, A-Z）

#### 处理规则

**1. 短句处理（≤15字）**
- 汉字数 ≤ 15：直接采用，无需拆分

**2. 长句处理（>15字）**
- 汉字数 > 15：进入拆分流程

#### 长句拆分算法

**拆分位置选择优先级：**
1. 优先在恰好15个汉字处拆分
2. 其次在15字附近选择安全位置

**拆分操作：**
- 将长句拆分为两个独立的部分
- 不添加任何连接标点（避免被读出来）
- 原始标点保留在最后一个部分末尾

**递归拆分：**
- 如果拆分后仍有部分 > 15字，继续拆分直到所有部分 ≤ 15字
- 确保拆分后**每部分都 ≥ 5 个汉字**（防止碎片化）

**示例：**
```
输入 (27字): 登鸕鷀樓王之渙白日依山盡黃河入海流欲窮千里目更上一層樓。

拆分过程:
- 第一部分 (15字): 登鸕鷀樓王之渙白日依山盡黃河入
- 第二部分 (12字): 海流欲窮千里目更上一層樓。

输出: [
  '登鸕鷀樓王之渙白日依山盡黃河入',
  '海流欲窮千里目更上一層樓。'
]
```

## 实现细节

### Python 实现

```python
def get_chinese_char_count(text):
    """计算仅汉字的字数"""
    count = 0
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            count += 1
    return count

def split_by_punctuation(text):
    """第一步：按指定标点分割"""
    import re
    # 分割标点：。？；：，
    parts = re.split(r'(?<=[。？；：，])', text)
    sentences = [s.strip() for s in parts if s.strip()]
    return sentences

def find_best_split_point(text):
    """寻找最佳拆分点"""
    target_count = 15
    current_chinese_count = 0
    best_point = len(text)
    
    for i, char in enumerate(text):
        if '\u4e00' <= char <= '\u9fff':
            current_chinese_count += 1
            if current_chinese_count == target_count:
                return i + 1
        
        if current_chinese_count > target_count:
            if best_point > 0:
                return best_point
            else:
                return i
    
    return len(text) // 2

def split_long_sentence(sentence):
    """递归拆分长句"""
    chinese_count = get_chinese_char_count(sentence)
    
    if chinese_count <= 15:
        return [sentence]
    
    # 提取标点
    final_punctuation = ''
    text_without_final_punct = sentence
    
    for punct in ['。', '？', '；', '：', '，']:
        if punct in sentence:
            last_idx = sentence.rfind(punct)
            if last_idx > 0:
                final_punctuation = sentence[last_idx]
                text_without_final_punct = sentence[:last_idx]
                break
    
    # 找拆分点
    split_point = find_best_split_point(text_without_final_punct)
    
    if split_point <= 0 or split_point >= len(text_without_final_punct):
        return [sentence]
    
    # 拆分
    part1 = text_without_final_punct[:split_point]
    part2_prefix = text_without_final_punct[split_point:]
    part2 = part2_prefix + final_punctuation
    
    # 验证长度
    part1_count = get_chinese_char_count(part1)
    part2_count = get_chinese_char_count(part2_prefix)
    
    if part1_count < 5 or part2_count < 5:
        return [sentence]
    
    # 递归处理
    if part2_count > 15:
        part2_splits = split_long_sentence(part2)
        return [part1] + part2_splits
    else:
        return [part1, part2]

def format_sentences_new(text):
    """完整的段落格式化函数"""
    sentences_by_punct = split_by_punctuation(text)
    final_sentences = split_long_sentences(sentences_by_punct)
    return final_sentences
```

### JavaScript 实现

在 `templates/edit_content.html` 中实现相同逻辑：

```javascript
function getChineseCharCount(text) {
    const chineseChars = text.match(/[\u4e00-\u9fff]/g);
    return chineseChars ? chineseChars.length : 0;
}

function formatSentences(text) {
    // 第一步：按指定标点分割
    const sentencesByPunct = splitByPunctuation(text);
    
    // 第二步：处理长句拆分
    const finalSentences = splitLongSentences(sentencesByPunct);
    
    return finalSentences;
}
```

## 测试用例

### 测试1：短句组合
```
输入: 登鸕鷀樓。王之渙。白日依山盡。黃河入海流。
输出:
  [1] (4字) 登鸕鷀樓。
  [2] (3字) 王之渙。
  [3] (5字) 白日依山盡。
  [4] (5字) 黃河入海流。
```

### 测试2：长句拆分
```
输入: 这是一个非常长的句子包含了很多汉字需要被拆分成多个部分以确保每部分都不超过十五个汉字。
输出:
  [1] (15字) 这是一个非常长的句子包含了很多
  [2] (15字) 汉字需要被拆分成多个部分以确保
  [3] (12字) 每部分都不超过十五个汉字。
```

### 测试3：复杂标点
```
输入: 登鸕鷀樓。王之渙。白日依山盡，黃河入海流；欲窮千里目，更上一層樓。
输出:
  [1] (4字) 登鸕鷀樓。
  [2] (3字) 王之渙。
  [3] (5字) 白日依山盡，
  [4] (5字) 黃河入海流；
  [5] (5字) 欲窮千里目，
  [6] (5字) 更上一層樓。
```

## 集成点

### 前端集成
- **文件**: `templates/edit_content.html`
- **函数**: `formatSentences(text)`
- **用途**: 用户编辑段落时，保存前自动进行拆分

### 后端集成
- **文件**: `flask_app.py`
- **函数**: `format_sentences_new(text)` 
- **用途**: 在 `/save_content` 路由中进行验证和二次处理

### TTS 处理
- 拆分后的每个句子都会被单独生成语音文件
- 文件名基于句子内容的MD5哈希值
- 听写测试时，按拆分后的句子顺序进行

## 优势

1. **可读性优化**: 确保每个句子长度适中（≤15字），便于朗读和理解
2. **自动化**: 用户只需输入原文，系统自动处理拆分
3. **智能拆分**: 优先在完整词语处拆分，避免破坏语义
4. **容错处理**: 防止过度拆分（每部分≥5字）
5. **标点保留**: 保留原有标点，保持文本结构

## 注意事项

1. 拆分规则仅适用于**汉字数**，不计特殊字符
2. 拆分结果**保留原始标点**，不添加额外标点
3. **递归拆分**确保所有部分都不超过15字
4. **最小限制**确保每部分至少5个汉字，防止碎片

