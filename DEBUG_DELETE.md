# 刪除功能調試指南

## 當前狀況
- ✅ **後端刪除功能**: 完全正常運作
- ✅ **Flask 路由**: 正確處理 DELETE 請求
- ⚠️ **前端按鈕**: 用戶報告按鈕點擊無反應

## 測試結果
已驗證後端刪除功能通過直接 Python 請求成功運作：
- 發送 POST 到 `/delete_content/中文/第一課`
- 收到 200 status 和 success 響應
- 課程數據已從 JSON 文件中刪除

## 前端調試步驟

### 1. 打開瀏覽器開發者工具
- **Windows/Linux**: 按 `F12` 或 `Ctrl+Shift+I`
- **Mac**: 按 `Cmd+Option+I`

### 2. 進入控制台 (Console) 選項卡

### 3. 訪問課程列表頁面
- 打開 http://127.0.0.1:5002/vocab_list
- 確保頁面加載成功

### 4. 測試刪除按鈕
1. 展開一個課程（點擊課程標題）
2. 找到紅色的 "🗑️ 刪除" 按鈕
3. **保持開發者工具的控制台打開**
4. 點擊刪除按鈕
5. **觀察控制台輸出**

### 5. 檢查期望的日誌消息
刪除按鈕應該會在控制台顯示以下消息（按順序）：

```
=== deleteLesson CALLED ===
Parameters: {language: "中文", lessonNum: "第二課"}
Parameters type: {language: "string", lessonNum: "string"}
Confirmation message: 確認要刪除 中文 - 第二課 嗎？此操作不可撤銷！
```

### 6. 確認對話框
- 控制台應顯示 `User confirmed: true`（如果你點擊確定）
- 或 `User cancelled deletion`（如果你點擊取消）

### 7. 如果繼續執行
應該看到：
```
Starting deletion process...
Encoded parameters: {language: "%E4%B8%AD%E6%96%87", lesson: "%E7%AC%AC%E4%BA%8C%E8%AA%B2"}
Sending POST request to: /delete_content/%E4%B8%AD%E6%96%87/%E7%AC%AC%E4%BA%8C%E8%AA%B2
Response received:
  Status: 200
  Ok: true
  Status Text: OK
  Response text: {"status":"success","message":"內容已成功刪除"}
  Parsed JSON: {status: "success", message: "內容已成功刪除"}
✓ Deletion successful, showing alert...
```

## 可能的問題

### 問題 1: 控制台沒有任何消息
**原因**: JavaScript 代碼沒有執行
**解決方案**:
- 檢查按鈕是否確實是 `<button>` 標籤
- 確認 `onclick` 屬性正確
- 在瀏覽器控制台輸入: `typeof deleteLesson` 應返回 "function"

### 問題 2: 顯示"User cancelled deletion"
**原因**: 用戶點擊了確認對話框中的"取消"
**解決方案**: 再試一次並點擊"確定"

### 問題 3: 響應狀態不是 200
**原因**: 可能的路由問題或參數編碼問題
**解決方案**: 檢查 Flask 控制台的 DEBUG 消息

### 問題 4: 錯誤訊息出現
**原因**: JavaScript 拋出異常
**解決方案**:
- 在控制台查看完整的錯誤堆棧
- 複製錯誤訊息進行搜索

## Flask 後端日誌

檢查 Flask 控制台（運行 `python flask_app.py` 的終端）：

應該看到：
```
[DEBUG] Attempting to delete: language=中文, lesson_num=第二課
[DEBUG] Data keys: ['中文', '英文']
[DEBUG] Language '中文' lessons: ['第二課', '第三課', '第一课']
[DEBUG] Deleting: 中文/第二課
[DEBUG] Successfully deleted: 中文/第二課
127.0.0.1 - - [DATE] "POST /delete_content/%E4%B8%AD%E6%96%87/%E7%AC%AC%E4%BA%8C%E8%AA%B2 HTTP/1.1" 200 -
```

## 測試刪除端點（不使用按鈕）

如果需要直接測試，可以在瀏覽器控制台執行：

```javascript
// 測試刪除第二課
fetch('/delete_content/%E4%B8%AD%E6%96%87/%E7%AC%AC%E4%BA%8C%E8%AA%B2', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'}
}).then(r => r.json()).then(d => console.log(d))
```

應返回: `{status: "success", message: "內容已成功刪除"}`

## 下一步
請按照上述步驟進行，並提供:
1. 控制台中显示的日誌消息（或沒有消息）
2. 是否顯示了確認對話框
3. 任何錯誤訊息

這樣可以幫助識別問題所在。
