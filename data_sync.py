#!/usr/bin/env python3
"""
数据同步工具 - 将生产环境数据同步到开发环境

支持的同步方式：
1. SCP (Linux/Mac/Windows with Git Bash)
2. 手动下载 (通过浏览器或SFTP)
3. Docker volume 挂载
"""

import json
import os
import sys
import shutil
from datetime import datetime
from pathlib import Path

class DataSync:
    """数据同步管理器"""
    
    def __init__(self):
        self.dev_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_file = os.path.join(self.dev_dir, 'vocabulary_data.json')
        self.backup_dir = os.path.join(self.dev_dir, 'backups')
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 创建备份目录
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def backup_current_data(self):
        """备份当前开发环境数据"""
        if os.path.exists(self.data_file):
            backup_file = os.path.join(
                self.backup_dir, 
                f'vocabulary_data_backup_{self.timestamp}.json'
            )
            shutil.copy2(self.data_file, backup_file)
            print(f"✅ 已备份当前数据: {backup_file}")
            return backup_file
        return None
    
    def validate_json(self, filepath):
        """验证 JSON 文件格式"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                json.load(f)
            print(f"✅ JSON 格式验证通过: {filepath}")
            return True
        except json.JSONDecodeError as e:
            print(f"❌ JSON 格式错误: {e}")
            return False
        except Exception as e:
            print(f"❌ 文件读取错误: {e}")
            return False
    
    def get_statistics(self, filepath):
        """获取数据统计信息"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            stats = {
                'lessons': len(data),
                'total_words': 0,
                'total_attempts': 0,
                'total_correct': 0,
                'total_incorrect': 0,
            }
            
            for lesson_name, lesson_data in data.items():
                if '詞語' in lesson_data:
                    words = lesson_data['詞語']
                    stats['total_words'] += len(words)
                    for word in words:
                        stats['total_attempts'] += word.get('attempts', 0)
                        stats['total_correct'] += word.get('correct', 0)
                        stats['total_incorrect'] += word.get('incorrect', 0)
            
            return stats
        except Exception as e:
            print(f"❌ 统计错误: {e}")
            return None
    
    def merge_data(self, new_data_file):
        """合并新旧数据（保留两边的课程）"""
        try:
            # 读取当前数据
            with open(self.data_file, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
            
            # 读取新数据
            with open(new_data_file, 'r', encoding='utf-8') as f:
                new_data = json.load(f)
            
            # 合并：新数据优先，但保留旧数据中新数据没有的课程
            merged_data = old_data.copy()
            merged_data.update(new_data)
            
            # 保存合并后的数据
            merge_backup = os.path.join(
                self.backup_dir,
                f'vocabulary_data_merged_{self.timestamp}.json'
            )
            with open(merge_backup, 'w', encoding='utf-8') as f:
                json.dump(merged_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 数据合并成功: {merge_backup}")
            return merged_data
        except Exception as e:
            print(f"❌ 合并错误: {e}")
            return None
    
    def replace_data(self, new_data_file):
        """替换为新数据"""
        try:
            # 验证新数据
            if not self.validate_json(new_data_file):
                return False
            
            # 备份当前数据
            self.backup_current_data()
            
            # 替换数据
            shutil.copy2(new_data_file, self.data_file)
            print(f"✅ 数据已替换为: {new_data_file}")
            return True
        except Exception as e:
            print(f"❌ 替换错误: {e}")
            return False
    
    def compare_data(self, new_data_file):
        """比较新旧数据"""
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                old_data = json.load(f)
            
            with open(new_data_file, 'r', encoding='utf-8') as f:
                new_data = json.load(f)
            
            old_stats = self.get_statistics(self.data_file)
            new_stats = self.get_statistics(new_data_file)
            
            print("\n" + "=" * 60)
            print("📊 数据对比")
            print("=" * 60)
            
            print("\n当前开发环境数据:")
            print(f"  课程数: {old_stats['lessons']}")
            print(f"  词语总数: {old_stats['total_words']}")
            print(f"  练习次数: {old_stats['total_attempts']}")
            print(f"  正确: {old_stats['total_correct']}, 错误: {old_stats['total_incorrect']}")
            
            print("\n生产环境新数据:")
            print(f"  课程数: {new_stats['lessons']}")
            print(f"  词语总数: {new_stats['total_words']}")
            print(f"  练习次数: {new_stats['total_attempts']}")
            print(f"  正确: {new_stats['total_correct']}, 错误: {new_stats['total_incorrect']}")
            
            print("\n课程列表对比:")
            old_lessons = set(old_data.keys())
            new_lessons = set(new_data.keys())
            
            print(f"  仅在开发环境: {old_lessons - new_lessons}")
            print(f"  仅在生产环境: {new_lessons - old_lessons}")
            print(f"  共同存在: {old_lessons & new_lessons}")
            
            print("\n" + "=" * 60)
        except Exception as e:
            print(f"❌ 对比错误: {e}")
    
    def print_help(self):
        """打印帮助信息"""
        print("""
使用说明：

1. 从生产环境获取数据文件:
   
   方式 A - 使用 SCP (Linux/Mac/Windows with Git Bash):
   ------
   scp user@production-server:/path/to/vocabulary_data.json ./vocabulary_data_prod.json
   
   方式 B - 使用 SFTP:
   ------
   sftp user@production-server
   get /path/to/vocabulary_data.json ./vocabulary_data_prod.json
   
   方式 C - Web 界面下载:
   ------
   如果你有 Web 访问，可能可以直接下载
   
   方式 D - Docker 容器:
   ------
   docker cp container_id:/app/vocabulary_data.json ./vocabulary_data_prod.json

2. 同步数据到开发环境:
   
   # 查看并比较数据（推荐先做这个）
   python data_sync.py --compare vocabulary_data_prod.json
   
   # 合并数据（保留两边的课程）
   python data_sync.py --merge vocabulary_data_prod.json
   
   # 替换数据（用生产环境数据替换）
   python data_sync.py --replace vocabulary_data_prod.json

3. 恢复备份:
   
   备份文件位置: backups/ 目录
   
   恢复方法:
   cp backups/vocabulary_data_backup_YYYYMMDD_HHMMSS.json vocabulary_data.json

选项说明:
  --compare FILE    比较新旧数据（不修改任何文件）
  --merge FILE      合并数据（新数据优先，保留旧的课程）
  --replace FILE    替换数据（完全用新数据替换）
  --help            显示此帮助信息
        """)

def main():
    """主函数"""
    sync = DataSync()
    
    if len(sys.argv) < 2:
        sync.print_help()
        return
    
    command = sys.argv[1]
    
    if command == '--help':
        sync.print_help()
    
    elif command == '--compare' and len(sys.argv) > 2:
        prod_file = sys.argv[2]
        if os.path.exists(prod_file):
            sync.compare_data(prod_file)
        else:
            print(f"❌ 文件不存在: {prod_file}")
    
    elif command == '--merge' and len(sys.argv) > 2:
        prod_file = sys.argv[2]
        if os.path.exists(prod_file):
            if sync.validate_json(prod_file):
                merged = sync.merge_data(prod_file)
                if merged:
                    # 保存合并结果
                    with open(sync.data_file, 'w', encoding='utf-8') as f:
                        json.dump(merged, f, ensure_ascii=False, indent=2)
                    print(f"✅ 数据已合并到: {sync.data_file}")
                    print("✅ 原数据已备份到: backups/ 目录")
        else:
            print(f"❌ 文件不存在: {prod_file}")
    
    elif command == '--replace' and len(sys.argv) > 2:
        prod_file = sys.argv[2]
        if os.path.exists(prod_file):
            response = input(f"⚠️  确认要用 {prod_file} 替换当前数据? (yes/no): ")
            if response.lower() == 'yes':
                if sync.replace_data(prod_file):
                    print("✅ 数据已替换")
            else:
                print("❌ 已取消")
        else:
            print(f"❌ 文件不存在: {prod_file}")
    
    else:
        print(f"❌ 未知命令: {command}")
        sync.print_help()

if __name__ == '__main__':
    main()
