# 📊 数据同步指南 - 生产环境 → 开发环境

## 概述

你在生产环境已有数据（新课程等），需要同步到本地开发环境。本指南提供多种同步方式。

---

## 📋 数据存储位置

**数据文件**: `vocabulary_data.json`
- 包含所有课程、词语和学习进度
- JSON 格式，易于传输

**音频文件**: `static/audio/*.mp3`
- 缓存的生成音频文件
- 可选同步（首次访问会自动重新生成）

---

## 🚀 快速同步（推荐）

### 步骤 1: 从生产环境获取数据文件

选择以下方式之一：

#### 方式 A: 使用 SCP (推荐 - 最快)

如果你有 SSH 访问权限：

```bash
# Linux/Mac/Windows (with Git Bash)
scp user@your-production-server:/path/to/vocabulary_data.json ./vocabulary_data_prod.json

# 示例：
scp ubuntu@192.168.1.100:/home/ubuntu/app/vocabulary_data.json ./vocabulary_data_prod.json
```

#### 方式 B: 使用 SFTP

```bash
sftp user@your-production-server
cd /path/to/app
get vocabulary_data.json vocabulary_data_prod.json
exit
```

#### 方式 C: 使用 Web 浏览器

如果生产环境配置了文件下载：
1. 访问生产环境的管理页面（如果有）
2. 下载 `vocabulary_data.json`
3. 保存为 `vocabulary_data_prod.json`

#### 方式 D: Docker 容器

```bash
# 如果使用 Docker
docker cp container_id:/app/vocabulary_data.json ./vocabulary_data_prod.json

# 或者从运行中的容器
docker exec container_id cat /app/vocabulary_data.json > vocabulary_data_prod.json
```

#### 方式 E: 手动复制

1. SSH 进入生产服务器
2. 查看文件内容：`cat vocabulary_data.json`
3. 复制内容并在本地创建 `vocabulary_data_prod.json`

### 步骤 2: 查看并比较数据

在同步前，先预览新数据：

```bash
# 查看数据对比（不修改任何文件）
python data_sync.py --compare vocabulary_data_prod.json
```

**预期输出**:
```
============================================================
📊 数据对比
============================================================

当前开发环境数据:
  课程数: 3
  词语总数: 45
  练习次数: 100
  正确: 85, 错误: 15

生产环境新数据:
  课程数: 5
  词语总数: 67
  练习次数: 250
  正确: 210, 错误: 40

课程列表对比:
  仅在开发环境: set()
  仅在生产环境: {'新课程1', '新课程2'}
  共同存在: {'商務用語', '日常用語'}

============================================================
```

### 步骤 3: 选择同步方式

#### 选项 A: 合并数据（推荐）✅

保留开发环境的所有课程，添加生产环境的新课程和数据：

```bash
python data_sync.py --merge vocabulary_data_prod.json
```

**效果**:
- ✅ 保留开发环境中的所有课程
- ✅ 添加生产环境中的新课程
- ✅ 对相同课程，使用生产环境的数据（更新）
- ✅ 原数据自动备份到 `backups/` 目录

**什么时候使用**: 
- 生产环境有新课程需要在开发中测试
- 想保留开发环境的测试数据

#### 选项 B: 替换数据

完全用生产环境数据替换开发环境数据：

```bash
python data_sync.py --replace vocabulary_data_prod.json
```

**效果**:
- 开发环境数据完全替换为生产环境数据
- 原数据自动备份

**什么时候使用**:
- 只想在开发环境中测试生产数据
- 开发环境数据已过时

---

## 🔄 详细同步过程

### 完整示例

```bash
# 1. 从生产环境获取数据（选择一种方式）
scp user@prod-server:/app/vocabulary_data.json ./vocabulary_data_prod.json

# 2. 对比新旧数据
python data_sync.py --compare vocabulary_data_prod.json

# 3. 选择同步方式
# 方式 A: 合并（推荐）
python data_sync.py --merge vocabulary_data_prod.json

# 或者
# 方式 B: 替换
python data_sync.py --replace vocabulary_data_prod.json

# 4. 启动开发环境验证
python flask_app.py

# 5. 访问 http://127.0.0.1:5002 查看新数据
```

---

## 📂 数据备份管理

### 自动备份

每次同步时，原数据会自动备份到 `backups/` 目录：

```
backups/
├── vocabulary_data_backup_20260124_150000.json
├── vocabulary_data_backup_20260124_160000.json
├── vocabulary_data_backup_20260124_170000.json
└── ...
```

### 查看备份列表

```bash
# Linux/Mac
ls -lh backups/

# Windows PowerShell
Get-ChildItem backups/ | Select-Object FullName, Length, LastWriteTime
```

### 恢复备份

如果需要恢复到某个备份：

```bash
# 查看备份
ls backups/

# 恢复备份（替换为你的备份文件名）
cp backups/vocabulary_data_backup_20260124_150000.json vocabulary_data.json

# 或者在 Windows PowerShell 中
Copy-Item backups/vocabulary_data_backup_20260124_150000.json vocabulary_data.json
```

---

## 🔍 验证同步成功

### 方法 1: 检查数据文件

```bash
# 查看文件大小（应该比原来大）
ls -lh vocabulary_data.json

# 查看文件修改时间（应该是最新的）
stat vocabulary_data.json

# Windows PowerShell
Get-Item vocabulary_data.json | Select-Object FullName, Length, LastWriteTime
```

### 方法 2: 启动应用并验证

```bash
# 启动 Flask 应用
python flask_app.py
```

访问 http://127.0.0.1:5002

1. 检查课程列表 → 应该看到生产环境的新课程
2. 选择新课程 → 应该能看到新词语
3. 点击播放按钮 → 应该有声音

### 方法 3: 查看 JSON 内容

```bash
# 查看数据文件的课程列表
python -c "import json; data = json.load(open('vocabulary_data.json')); print(list(data.keys()))"

# 应该输出包含新课程的列表
```

---

## ⚠️ 常见问题

### Q1: 传输文件时遇到权限拒绝错误
```
Permission denied (publickey)
```

**解决方案**:
- 确保你有生产服务器的 SSH 访问权限
- 检查 SSH 密钥配置
- 使用 SFTP 作为替代方案

### Q2: JSON 格式错误

```
JSONDecodeError: ...
```

**解决方案**:
- 确保文件完整传输（检查文件大小）
- 在本地查看文件是否损坏
- 重新从生产环境获取文件

### Q3: 数据没有显示在开发环境中

**诊断步骤**:
1. 检查文件是否真的被替换了：
   ```bash
   ls -l vocabulary_data.json
   ```

2. 检查数据是否加载：
   ```bash
   python -c "import json; print(json.load(open('vocabulary_data.json')))"
   ```

3. 重启 Flask 应用：
   ```bash
   # 停止当前应用 (Ctrl+C)
   # 然后重新启动
   python flask_app.py
   ```

4. 清除浏览器缓存并刷新页面

### Q4: 我想只同步某个特定课程的数据

**解决方案**:
1. 手动编辑 `vocabulary_data_prod.json`，保留只需要的课程
2. 然后再同步

```python
# 或者使用 Python 脚本
import json

# 读取生产环境数据
with open('vocabulary_data_prod.json', 'r', encoding='utf-8') as f:
    prod_data = json.load(f)

# 只保留特定课程
courses_to_sync = ['新课程1', '新课程2']
filtered_data = {k: v for k, v in prod_data.items() if k in courses_to_sync}

# 保存
with open('vocabulary_data_prod_filtered.json', 'w', encoding='utf-8') as f:
    json.dump(filtered_data, f, ensure_ascii=False, indent=2)

# 然后同步
# python data_sync.py --merge vocabulary_data_prod_filtered.json
```

### Q5: 生产环境数据经常更新，如何保持同步？

**解决方案**:
- 定期重复同步过程
- 建议每周同步一次
- 可以写成定时任务（cron job）

```bash
# 创建同步脚本 sync_data.sh
#!/bin/bash
scp user@prod-server:/app/vocabulary_data.json ~/app/vocabulary_data_prod.json
cd ~/app
python data_sync.py --merge vocabulary_data_prod.json

# 添加到 crontab（每周一 9:00 执行）
0 9 * * 1 bash ~/sync_data.sh
```

---

## 🔐 数据安全注意事项

### 1. 备份很重要

- 同步前确保备份原数据
- `data_sync.py` 会自动备份到 `backups/` 目录
- 定期备份 `backups/` 目录到其他地方

### 2. 验证文件完整性

```bash
# 获取文件的 SHA256 哈希值
sha256sum vocabulary_data.json
sha256sum vocabulary_data_prod.json

# 应该不同（不同的数据）
```

### 3. 保护敏感数据

- 不要在公开渠道传输文件
- 使用 SSH/SFTP 传输（加密）
- 避免使用明文 FTP

### 4. 权限管理

```bash
# 确保本地文件不被意外修改
chmod 644 vocabulary_data.json

# 确保备份目录的读取权限
chmod 755 backups/
```

---

## 📚 相关命令速查

```bash
# 比较数据（预览，不修改）
python data_sync.py --compare vocabulary_data_prod.json

# 合并数据（推荐）
python data_sync.py --merge vocabulary_data_prod.json

# 替换数据
python data_sync.py --replace vocabulary_data_prod.json

# 查看帮助
python data_sync.py --help

# 列出备份
ls -lh backups/

# 恢复备份
cp backups/vocabulary_data_backup_YYYYMMDD_HHMMSS.json vocabulary_data.json

# 验证 JSON 格式
python -c "import json; json.load(open('vocabulary_data.json'))" && echo "✅ Valid"

# 查看课程列表
python -c "import json; print(list(json.load(open('vocabulary_data.json')).keys()))"
```

---

## 🎯 推荐流程总结

```
1️⃣ 从生产环境获取数据
   scp user@prod-server:/app/vocabulary_data.json ./vocabulary_data_prod.json

2️⃣ 对比数据（预览）
   python data_sync.py --compare vocabulary_data_prod.json

3️⃣ 合并数据（推荐选择）
   python data_sync.py --merge vocabulary_data_prod.json

4️⃣ 启动应用验证
   python flask_app.py

5️⃣ 访问应用确认新数据
   http://127.0.0.1:5002

✅ 完成！新数据已同步到开发环境
```

---

**更新日期**: 2026-01-24  
**版本**: 1.0  
**相关工具**: `data_sync.py`
