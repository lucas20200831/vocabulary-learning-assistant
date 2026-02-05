# 完整测试指南 - 浏览器保存功能

## 快速开始

### 第 1 步：启动 Flask 服务器

在终端中运行：

```bash
cd d:\Education_Lucas\vocabulary-learning-assistant
python start_server.py
```

等待看到：
```
[INIT] Starting Flask development server...
[INIT] Server will run on http://127.0.0.1:5002
 * Running on http://127.0.0.1:5002
```

### 第 2 步：打开浏览器

访问编辑页面：
```
http://127.0.0.1:5002/edit_content/测试课程_拆分功能
```

### 第 3 步：打开开发者工具

按 **F12** 打开开发者工具

### 第 4 步：进行测试

1. 修改某个段落的内容（例如，添加更长的句子）
2. 点击"保存"按钮
3. 观察以下位置：

#### 检查 Console 标签
- 查看是否有红色的错误消息
- 注意任何 JavaScript 错误

#### 检查 Network 标签
1. 在 Network 标签中，筛选"XHR"（XMLHttpRequest）
2. 查找 /save_content 请求
3. 检查：
   - 请求方法：应该是 POST
   - 响应状态：应该是 200
   - 响应内容：应该包含 `"status": "success"`

## 预期结果

### 保存成功
- 按钮文本变为 "✓ 已保存"
- 按钮颜色变绿
- 页面会在几秒后重定向到 /vocab_list

### 保存失败
- 按钮显示错误状态
- Console 中有错误消息
- Network 标签中 /save_content 请求状态不是 200

## 测试用例

### 测试 1：简单保存（无改动）
1. 打开编辑页面
2. 直接点击保存（不修改任何内容）
3. 预期：保存成功，页面返回 /vocab_list

### 测试 2：修改词语
1. 修改第一个段落的标题
2. 点击保存
3. 预期：保存成功

### 测试 3：修改长段落
1. 修改"中等长句"段落，添加更长的内容
2. 点击保存  
3. 预期：保存成功，长句被正确拆分

### 测试 4：添加新段落
1. 点击"添加新段落"按钮
2. 填写标题和内容
3. 点击保存
4. 预期：新段落被保存

## 常见问题诊断

### 问题：按钮点击无反应

**检查步骤：**
1. 打开 Console（F12 → Console）
2. 手动输入：`saveContent()` 并按 Enter
3. 查看是否有错误输出
4. 查看是否有 "Parsed words:" 和 "Parsed paragraphs:" 的日志

### 问题：请求发送但无响应

**检查步骤：**
1. 打开 Network 标签
2. 查看 /save_content 请求
3. 点击请求查看详细信息
4. 检查 Response 和 Preview 标签中的返回数据

### 问题：服务器错误（500）

**检查步骤：**
1. 查看 /save_content 的响应内容
2. 复制 traceback（追踪信息）
3. 查看具体错误位置和错误消息

## 日志收集

如果有问题，请收集以下信息：

### 1. 浏览器 Console 输出
```
右键 → 检查 → 选择 Console 标签
Ctrl+A 全选，Ctrl+C 复制
```

### 2. 网络请求详情
```
Network 标签 → 找到 /save_content 请求
右键 → Copy as cURL
```

### 3. 服务器日志
```
查看 Flask 服务器窗口中的输出
特别是 [SAVE] 开头的日志行
```

## 验证清单

保存成功应该满足以下条件：

- [ ] Flask 服务器在 http://127.0.0.1:5002 运行
- [ ] 浏览器能访问编辑页面
- [ ] 点击保存按钮后，按钮状态变化
- [ ] Network 中 /save_content 返回 HTTP 200
- [ ] 响应中包含 `"status": "success"`
- [ ] 音频文件被生成（在 /static/audio 目录中）
- [ ] 页面重定向到 /vocab_list 或显示成功消息

## 成功标志

✅ 保存功能正常工作的标志：
1. 按钮显示 "✓ 已保存" 且为绿色
2. Network 中 /save_content 返回 200
3. 服务器日志显示"✓ Generation complete: X/X successful"
4. 音频文件在 static/audio 目录中
5. 页面成功重定向
