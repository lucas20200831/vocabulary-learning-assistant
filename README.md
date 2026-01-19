# 词汇学习助手

一个基于Flask的Web应用程序，帮助学生通过听写练习巩固新词汇。

## 功能特点

1. **生词表管理**
   - 创建新课程并添加词汇
   - 词汇只需输入单词，无需解释

2. **听写测试**
   - 按顺序播放词汇发音
   - 记录学生对每个词汇的掌握情况
   - 优先练习掌握程度较低的词汇

3. **巩固复习**
   - 自动识别需要复习的词汇
   - 按掌握程度排序显示

## 技术栈

- Python 3.x
- Flask 2.3.3
- HTML/CSS/JavaScript
- Web Speech API（浏览器内置语音功能）

## 项目结构

```
c:\Lucas_Python\
├── flask_app.py              # 主应用文件
├── vocabulary_data.json      # 词汇数据存储
├── requirements.txt          # 依赖声明
├── README.md               # 项目说明
└── templates/              # HTML模板目录
    ├── index.html          # 首页
    ├── vocab_list.html     # 课程列表页
    ├── create_lesson.html  # 创建课程页
    ├── quiz.html           # 听写测试页
    └── review.html         # 复习页
```

## 使用方法

1. 安装依赖：
   ```
   pip install -r requirements.txt
   ```

2. 启动应用：
   ```
   python flask_app.py
   ```

3. 访问应用：
   在浏览器中打开 `http://127.0.0.1:5002`

## 重要说明

- 应用程序数据保存在 `vocabulary_data.json` 文件中
- 听写功能使用浏览器内置的 Web Speech API 进行语音播放
- 词汇按添加顺序进行听写练习
- 未掌握的词汇会在后续练习中优先出现

## 环境要求

- Python 3.x
- 支持 Web Speech API 的现代浏览器（Chrome、Edge、Firefox等）