# 🔄 数据同步快速参考

## 三步快速同步

### 1️⃣ 从生产环境获取数据文件

```bash
# 使用 SCP（最快，需要 SSH 权限）
scp user@production-server:/path/to/vocabulary_data.json ./vocabulary_data_prod.json

# 或使用 SFTP
sftp user@production-server
get /path/to/vocabulary_data.json ./vocabulary_data_prod.json
exit
```

### 2️⃣ 对比数据（可选但推荐）

```bash
python data_sync.py --compare vocabulary_data_prod.json
```

输出示例：
```
当前开发环境: 3 个课程，45 个词语
生产环境新数据: 5 个课程，67 个词语
新增课程: 新课程1, 新课程2
```

### 3️⃣ 选择同步方式

#### A. 合并数据（推荐 ⭐）
保留开发环境的课程，添加生产环境的新课程：
```bash
python data_sync.py --merge vocabulary_data_prod.json
```

#### B. 替换数据
完全用生产数据替换开发数据：
```bash
python data_sync.py --replace vocabulary_data_prod.json
```

### 4️⃣ 验证

```bash
# 启动应用
python flask_app.py

# 访问 http://127.0.0.1:5002
# 检查新课程是否出现
```

---

## 常用命令

| 命令 | 说明 | 何时使用 |
|------|------|---------|
| `python data_sync.py --compare FILE` | 查看对比（不修改数据） | 同步前预览 |
| `python data_sync.py --merge FILE` | 合并数据 | ⭐ 推荐 |
| `python data_sync.py --replace FILE` | 替换数据 | 只想要生产数据 |
| `ls backups/` | 查看备份列表 | 恢复数据 |
| `cp backups/vocabulary_data_backup_XXX.json vocabulary_data.json` | 恢复备份 | 撤销同步 |

---

## 各种传输方式

### SCP (最快 ⚡)
```bash
scp user@host:/app/vocabulary_data.json ./vocabulary_data_prod.json
```
**需要**: SSH 权限  
**速度**: 最快  
**复杂度**: 简单  

### SFTP (交互式)
```bash
sftp user@host
cd /app
get vocabulary_data.json
exit
```
**需要**: SSH 权限  
**速度**: 中等  
**复杂度**: 中等  

### Web 浏览器 (图形化)
1. 访问生产环境的管理页面
2. 下载 vocabulary_data.json
3. 保存为 vocabulary_data_prod.json

**需要**: Web 访问  
**速度**: 取决于网络  
**复杂度**: 简单  

### Docker
```bash
docker cp container_id:/app/vocabulary_data.json ./vocabulary_data_prod.json
```
**需要**: Docker 访问  
**速度**: 最快  
**复杂度**: 简单  

### SSH 命令行
```bash
ssh user@host "cat /app/vocabulary_data.json" > vocabulary_data_prod.json
```
**需要**: SSH 权限  
**速度**: 快  
**复杂度**: 中等  

---

## 故障排除

### 传输文件失败？
- ✅ 检查 SSH 权限
- ✅ 尝试 SFTP 或 Web 下载
- ✅ 确保文件路径正确

### 同步后数据没有显示？
- ✅ 重启 Flask 应用：Ctrl+C → `python flask_app.py`
- ✅ 清除浏览器缓存：F12 → Application → Clear storage
- ✅ 检查数据：`python -c "import json; print(json.load(open('vocabulary_data.json')))"`

### JSON 格式错误？
- ✅ 确保文件完整传输
- ✅ 检查文件大小是否正确
- ✅ 重新从生产环境获取

### 想恢复原数据？
```bash
ls backups/                                              # 列出备份
cp backups/vocabulary_data_backup_20260124_150000.json vocabulary_data.json  # 恢复
```

---

## 文件对应关系

| 文件 | 说明 |
|------|------|
| `vocabulary_data.json` | 开发环境当前数据 |
| `vocabulary_data_prod.json` | 从生产环境获取的数据文件 |
| `backups/vocabulary_data_backup_*.json` | 同步前的自动备份 |
| `data_sync.py` | 数据同步工具 |

---

## 同步流程图

```
生产环境                    本地开发环境
vocabulary_data.json
        ↓ (SCP/SFTP)
vocabulary_data_prod.json
        ↓
(对比预览)
--compare
        ↓
(选择同步方式)
--merge 或 --replace
        ↓
vocabulary_data.json (更新)
        ↓
(自动备份)
backups/vocabulary_data_backup_*.json
        ↓
(重启应用)
python flask_app.py
        ↓
访问应用验证
http://127.0.0.1:5002 ✅
```

---

## 💡 提示

- 🎯 **推荐**: 先用 `--compare` 查看数据，再用 `--merge` 同步
- 📦 **备份**: 每次同步自动备份到 `backups/` 目录
- 🔄 **定期**: 生产环境经常更新？创建定时任务定期同步
- ⏮️ **撤销**: 随时可以从 `backups/` 目录恢复原数据
- 🔍 **验证**: 同步后一定要启动应用验证数据是否正确显示

---

**更新日期**: 2026-01-24  
**工具**: data_sync.py  
**详细文档**: DATA_SYNC_GUIDE.md
