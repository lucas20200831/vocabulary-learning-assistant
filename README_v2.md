# 詞彙學習助手

一個基於Flask的Web應用程式，幫助學生透過聽寫練習鞏固新詞彙。

## 🆕 重要更新 (v2.0)

### 🔊 音頻功能增強
已修復生產環境中音頻無聲的問題。詳見：
- **快速指南**: [QUICK_FIX_GUIDE.md](QUICK_FIX_GUIDE.md) 
- **完整方案**: [AUDIO_FIX_SUMMARY.md](AUDIO_FIX_SUMMARY.md)
- **部署指南**: [PRODUCTION_DEPLOYMENT_GUIDE.md](PRODUCTION_DEPLOYMENT_GUIDE.md)

### 📋 主要改進
1. ✅ 添加 CORS 支持（解決跨域問題）
2. ✅ 改進音頻生成和加載（解決延遲問題）
3. ✅ 增強調試日誌（易於診斷）
4. ✅ 新增診斷工具（快速排查）

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
- Flask 2.3.3 + Flask-CORS
- gTTS (Google Text-to-Speech)
- HTML/CSS/JavaScript

## 項目結構

```
.
├── flask_app.py                          # 主應用檔案
├── vocabulary_data.json                  # 詞彙數據存儲
├── requirements.txt                      # 依賴聲明
├── audio_diagnostics.py                  # 音頻診斷工具
├── quick_diagnose.py                     # 快速診斷工具
├── README.md                             # 項目說明
├── CHANGELOG.md                          # 變更記錄
├── QUICK_FIX_GUIDE.md                    # 快速修復指南
├── AUDIO_FIX_SUMMARY.md                  # 音頻問題解決方案
├── PRODUCTION_DEPLOYMENT_GUIDE.md        # 詳細部署指南
├── templates/                            # HTML模板
│   ├── index.html
│   ├── vocab_list.html
│   ├── create_lesson.html
│   ├── quiz.html
│   └── review.html
└── static/                               # 靜態文件
    └── audio/                            # 生成的音頻文件
```

## 快速開始

### 1. 安裝依賴
```bash
pip install -r requirements.txt
```

### 2. 診斷系統（推薦）
```bash
python quick_diagnose.py
```

### 3. 啟動應用
```bash
python flask_app.py
```

### 4. 訪問應用
在瀏覽器中開啟 `http://127.0.0.1:5002`

## 🔧 生產環境部署

### 對於生產環境部署
請參考 [PRODUCTION_DEPLOYMENT_GUIDE.md](PRODUCTION_DEPLOYMENT_GUIDE.md)

關鍵步驟：
1. 確保安裝了最新的依賴（包括 flask-cors）
2. 運行 `python quick_diagnose.py` 驗證配置
3. 配置 Web 服務器（Nginx/Apache）
4. 設置正確的文件權限

### 快速檢查清單
- [ ] `pip install -r requirements.txt`
- [ ] `python quick_diagnose.py` ✅
- [ ] 訪問應用並測試音頻播放
- [ ] 查看瀏覽器控制台的 `[AUDIO]` 日誌
- [ ] 查看 Flask 日誌的 `[TTS]` 消息

## 📊 數據存儲

- 應用程序數據保存在 `vocabulary_data.json` 檔案中
- 音頻文件緩存在 `static/audio/` 目錄中

## 🔊 音頻功能說明

### 工作原理
1. 用戶點擊播放按鈕
2. 應用調用後端 `/tts/<word>` 端點
3. 後端使用 gTTS 生成中文語音（首次）或返回緩存（後續）
4. 前端播放生成的 MP3 文件

### 常見問題

**如果沒有聲音，請：**
1. 打開瀏覽器開發者工具 (F12 → Console)
2. 查看 `[AUDIO]` 開頭的日誌信息
3. 運行 `python quick_diagnose.py` 診斷

詳見 [AUDIO_FIX_SUMMARY.md](AUDIO_FIX_SUMMARY.md) 的故障排除章節

## 環境要求

- Python 3.x
- 支持現代 HTML5 Audio 的瀏覽器
- 互聯網連接（首次生成音頻時）
- 磁盤空間（存儲緩存的音頻文件）

## 重要說明

- 詞彙按新增順序進行聽寫練習
- 未掌握的詞彙會在後續練習中優先出現
- 音頻文件自動緩存，後續訪問無需重新生成
- 生產環境需要配置正確的 CORS 和文件權限

## 💡 版本歷史

### v2.0 (2026-01-24)
- ✅ 修復生產環境音頻無聲問題
- ✅ 添加 CORS 支持
- ✅ 改進音頻加載和錯誤處理
- ✅ 新增診斷和部署工具

### v1.0
- 初始版本

## 📞 獲取幫助

1. **快速診斷**
   ```bash
   python quick_diagnose.py
   ```

2. **詳細診斷**
   ```bash
   python audio_diagnostics.py
   ```

3. **查閱文檔**
   - 快速指南：[QUICK_FIX_GUIDE.md](QUICK_FIX_GUIDE.md)
   - 完整方案：[AUDIO_FIX_SUMMARY.md](AUDIO_FIX_SUMMARY.md)
   - 部署指南：[PRODUCTION_DEPLOYMENT_GUIDE.md](PRODUCTION_DEPLOYMENT_GUIDE.md)

## 許可證

MIT License
