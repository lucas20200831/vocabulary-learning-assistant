# 📊 生产环境数据同步方案

## 🎯 问题

你在生产环境已经生成了一些数据（特别是新的课程），想要同步到本地开发环境进行测试和开发。

## ✅ 解决方案

已为你创建了完整的数据同步解决方案，包括：

### 核心工具

#### 1️⃣ `data_sync.py` - 数据同步工具
```bash
python data_sync.py --compare FILE      # 对比数据（预览）
python data_sync.py --merge FILE        # 合并数据（推荐）
python data_sync.py --replace FILE      # 替换数据
python data_sync.py --help              # 显示帮助
```

**功能**:
- ✅ 对比新旧数据（统计信息、课程对比）
- ✅ 合并数据（保留两边的课程）
- ✅ 替换数据（用生产数据替换）
- ✅ 自动备份（每次同步前备份）
- ✅ 数据验证（JSON 格式检查）

#### 2️⃣ `auto_sync.py` - 自动同步脚本（交互式）
```bash
python auto_sync.py
```

**特点**:
- 🎯 交互式引导（一步步提示）
- 📥 支持多种下载方式（SSH/Docker/Web）
- 📊 自动显示数据对比
- 🔄 自动执行同步
- ✓ 完整的验证流程

---

## 🚀 快速使用（3 种方式）

### 方式 A: 自动同步（推荐 - 最简单）⭐

```bash
python auto_sync.py
```

交互式指引，全程自动完成：
1. 输入生产服务器信息
2. 自动下载数据文件
3. 显示数据对比
4. 选择同步方式（合并/替换）
5. 自动执行同步

**适合**: 第一次同步，或不熟悉命令行

---

### 方式 B: 手动同步（最灵活）

#### 步骤 1: 从生产环境获取数据文件

```bash
# 使用 SCP（推荐 - 最快）
scp user@production-server:/path/to/vocabulary_data.json ./vocabulary_data_prod.json

# 或使用 SFTP
sftp user@production-server
get /path/to/vocabulary_data.json
exit

# 或使用 Docker
docker cp container_id:/app/vocabulary_data.json ./vocabulary_data_prod.json

# 或手动从 Web 下载后保存为 vocabulary_data_prod.json
```

#### 步骤 2: 对比数据（可选）

```bash
python data_sync.py --compare vocabulary_data_prod.json
```

**输出示例**:
```
当前开发环境: 3 个课程, 45 个词语
生产环境新数据: 5 个课程, 67 个词语
新增课程: 新课程1, 新课程2
仅在开发环境: 测试课程
```

#### 步骤 3: 同步数据

```bash
# 合并数据（推荐 ⭐）
# 保留开发数据中的所有课程，添加生产环境的新课程
python data_sync.py --merge vocabulary_data_prod.json

# 或替换数据
# 完全用生产数据替换开发数据
python data_sync.py --replace vocabulary_data_prod.json
```

#### 步骤 4: 验证

```bash
# 启动应用
python flask_app.py

# 访问 http://127.0.0.1:5002
# 检查新课程是否出现
```

---

### 方式 C: 脚本自动化（定期同步）

创建定时同步脚本：

#### Linux/Mac - 使用 cron

```bash
# 编辑 crontab
crontab -e

# 添加以下行（每周一 9:00 自动同步）
0 9 * * 1 cd /path/to/app && python auto_sync.py

# 或使用自定义脚本
0 9 * * 1 bash ~/sync_prod_data.sh
```

#### Windows - 使用任务计划程序

```powershell
# 创建任务计划
New-ScheduledTask -TaskName "VocabSync" `
  -Action (New-ScheduledTaskAction `
    -Execute "python" `
    -Argument "auto_sync.py" `
    -WorkingDirectory "C:\path\to\app") `
  -Trigger (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 9am) `
  -RunLevel Highest
```

#### 自定义脚本示例

```bash
#!/bin/bash
# sync_prod_data.sh

cd /path/to/app

# 下载最新数据
scp user@prod-server:/app/vocabulary_data.json ./vocabulary_data_prod.json

# 合并数据（自动响应）
python data_sync.py --merge vocabulary_data_prod.json

# 发送通知邮件
echo "数据已同步" | mail -s "生产数据同步完成" your-email@example.com
```

---

## 📚 详细文档

### 快速参考
📄 [DATA_SYNC_QUICK_REFERENCE.md](DATA_SYNC_QUICK_REFERENCE.md)
- 常用命令速查
- 各种传输方式对比
- 故障排除

### 完整指南
📄 [DATA_SYNC_GUIDE.md](DATA_SYNC_GUIDE.md)
- 详细的同步过程
- 数据备份管理
- 安全建议
- 常见问题解决

---

## 🔑 关键概念

### 合并（Merge）vs 替换（Replace）

| 操作 | 合并 | 替换 |
|------|------|------|
| 效果 | 保留开发课程 + 添加生产课程 | 完全用生产数据替换 |
| 何时用 | 开发环境有测试数据需要保留 | 只想要生产数据 |
| 风险 | 低 | 中等（会丢失开发数据） |
| 推荐 | ⭐⭐⭐ | ⭐⭐ |

### 数据备份

所有同步操作都会自动备份原数据到 `backups/` 目录：

```
backups/
├── vocabulary_data_backup_20260124_150000.json
├── vocabulary_data_backup_20260124_160000.json
└── ...
```

恢复方法：
```bash
cp backups/vocabulary_data_backup_20260124_150000.json vocabulary_data.json
python flask_app.py  # 重启应用
```

---

## 🎯 推荐流程

```
1️⃣ 方案选择
   └─ 新用户 → auto_sync.py（交互式）
   └─ 熟悉命令 → data_sync.py（手动）
   └─ 定期同步 → 脚本自动化（cron/定时任务）

2️⃣ 获取数据
   └─ SSH → scp (最快)
   └─ Docker → docker cp
   └─ Web → 浏览器下载
   └─ SFTP → 交互式

3️⃣ 预览和对比
   └─ python data_sync.py --compare vocabulary_data_prod.json

4️⃣ 执行同步
   └─ python data_sync.py --merge vocabulary_data_prod.json (推荐)
   └─ python data_sync.py --replace vocabulary_data_prod.json

5️⃣ 验证
   └─ python flask_app.py
   └─ 访问 http://127.0.0.1:5002
   └─ 检查新课程是否出现

✅ 完成！原数据已备份，随时可恢复
```

---

## 📊 文件对应关系

| 文件 | 说明 | 位置 |
|------|------|------|
| `vocabulary_data.json` | 开发环境当前数据 | 项目根目录 |
| `vocabulary_data_prod.json` | 生产环境下载的数据 | 项目根目录（临时）|
| `data_sync.py` | 数据同步工具 | 项目根目录 |
| `auto_sync.py` | 自动同步脚本 | 项目根目录 |
| `backups/` | 自动备份目录 | 项目根目录 |
| `DATA_SYNC_GUIDE.md` | 完整指南 | 项目根目录 |
| `DATA_SYNC_QUICK_REFERENCE.md` | 快速参考 | 项目根目录 |

---

## 🔒 安全建议

1. **使用加密传输**
   - 使用 SCP 或 SFTP（加密）
   - 不要使用明文 FTP

2. **定期备份**
   - 备份会自动创建
   - 定期备份整个 `backups/` 目录

3. **权限管理**
   ```bash
   chmod 644 vocabulary_data.json
   chmod 755 backups/
   ```

4. **版本控制**
   - 考虑将数据文件加入 Git
   - 便于追踪变更历史

---

## ⚠️ 常见问题

### Q1: 我不知道生产服务器的路径
**A**: 
```bash
# SSH 到服务器
ssh user@server

# 查找文件
find / -name "vocabulary_data.json" 2>/dev/null

# 或者看应用配置
cat /app/flask_app.py | grep "vocabulary_data"
```

### Q2: SCP 出现权限拒绝
**A**: 
- 检查 SSH 密钥：`ssh-add ~/.ssh/id_rsa`
- 使用密码认证：`scp -P 22 user@server:...`
- 尝试 SFTP 或 Web 下载

### Q3: 同步后数据没有显示
**A**:
1. 重启应用：`Ctrl+C` → `python flask_app.py`
2. 清除浏览器缓存：F12 → Application → Clear storage
3. 检查文件：`python -c "import json; print(json.load(open('vocabulary_data.json')))"`

### Q4: 我不小心替换了开发数据
**A**: 
```bash
ls backups/  # 查看备份列表
cp backups/vocabulary_data_backup_*.json vocabulary_data.json
```

### Q5: 生产环境数据经常更新，如何保持同步？
**A**: 
- 使用 `auto_sync.py` 定期手动同步
- 或使用 cron/任务计划程序自动同步（参考方式 C）

---

## 📈 同步流程概览

```
生产环境
vocabulary_data.json
        │
        ├─ SCP ──────────┐
        ├─ SFTP ─────────┤
        ├─ Docker ───────┤─→ vocabulary_data_prod.json
        └─ Web 下载 ─────┘
                         │
                         ├─ --compare (预览)
                         │
                         ├─ --merge (推荐)
                         │   ↓
                         │   vocabulary_data.json (更新)
                         │
                         └─ --replace
                             ↓
                             vocabulary_data.json (替换)
                         │
                         ↓
                    自动备份
                         │
                    backups/vocabulary_data_backup_*.json
                         │
                         ↓
                    python flask_app.py
                         │
                    http://127.0.0.1:5002
                         │
                         ✅ 验证成功！
```

---

## 🎯 总结

| 需求 | 推荐方案 |
|------|---------|
| 第一次同步 | `python auto_sync.py` |
| 快速查看数据对比 | `python data_sync.py --compare file` |
| 定期从生产同步数据 | 设置 cron/定时任务 |
| 只想要生产数据 | `python data_sync.py --replace file` |
| 保留开发测试数据 | `python data_sync.py --merge file` ⭐ |
| 恢复原数据 | `cp backups/vocabulary_data_backup_*.json vocabulary_data.json` |

---

**创建日期**: 2026-01-24  
**相关工具**: data_sync.py, auto_sync.py  
**详细文档**: DATA_SYNC_GUIDE.md, DATA_SYNC_QUICK_REFERENCE.md
