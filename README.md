# 詞彙學習助手

一個基於Flask的Web應用程式，幫助學生透過聽寫練習鞏固新詞彙。

## 功能特點

1. **聽寫內容管理**
   - 輸入新的聽寫內容（詞語或段落）
   - 支持多個段落，每個段落包含多個句子

2. **聽寫測試**
   - 按順序播放詞語或句子
   - 記錄學生對每個項目的掌握情況
   - 優先練習掌握程度較低的項目

3. **鞏固複習**
   - 自動識別需要複習的項目
   - 按掌握程度排序顯示

## 技術棧

- Python 3.x
- Flask 2.3.3
- HTML/CSS/JavaScript
- Web Speech API（瀏覽器內置語音功能）

## 項目結構

```
c:\Lucas_Python\
├── flask_app.py              # 主應用檔案
├── vocabulary_data.json      # 詞彙數據存儲
├── requirements.txt          # 依賴聲明
├── README.md               # 項目說明
└── templates/              # HTML模板目錄
    ├── index.html          # 首頁
    ├── vocab_list.html     # 課程列表頁
    ├── create_lesson.html  # 建立課程頁
    ├── quiz.html           # 聽寫測試頁
    └── review.html         # 複習頁
```

## 使用方法

1. 安裝依賴：
   ```
   pip install -r requirements.txt
   ```

2. 啟動應用：
   ```
   python flask_app.py
   ```

3. 訪問應用：
   在瀏覽器中開啟 `http://127.0.0.1:5002`

## 重要說明

- 應用程序數據保存在 `vocabulary_data.json` 檔案中
- 聽寫功能使用瀏覽器內置的 Web Speech API 進行語音播放
- 詞彙按新增順序進行聽寫練習
- 未掌握的詞彙會在後續練習中優先出現

## 環境要求

- Python 3.x
- 支持 Web Speech API 的現代瀏覽器（Chrome、Edge、Firefox等）