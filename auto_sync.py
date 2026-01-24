#!/usr/bin/env python3
"""
自动数据同步脚本示例
帮助用户快速从生产环境同步数据到开发环境
"""

import subprocess
import sys
import os
from pathlib import Path

class AutoSync:
    """自动同步管理器"""
    
    def __init__(self):
        self.project_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_file = os.path.join(self.project_dir, 'vocabulary_data.json')
    
    def get_production_config(self):
        """获取生产环境配置"""
        print("\n" + "=" * 60)
        print("🔧 生产环境配置")
        print("=" * 60)
        
        print("\n请输入生产环境信息：\n")
        
        # 服务器信息
        server_type = input("1. 服务器类型 (SSH/Docker/Web) [SSH]: ").strip() or "SSH"
        
        if server_type.upper() == "SSH":
            user = input("   SSH 用户名: ").strip()
            host = input("   服务器地址 (IP 或域名): ").strip()
            path = input("   文件路径 [/app/vocabulary_data.json]: ").strip() or "/app/vocabulary_data.json"
            
            return {
                'type': 'SSH',
                'user': user,
                'host': host,
                'path': path
            }
        
        elif server_type.upper() == "DOCKER":
            container_id = input("   容器 ID 或名称: ").strip()
            path = input("   文件路径 [/app/vocabulary_data.json]: ").strip() or "/app/vocabulary_data.json"
            
            return {
                'type': 'Docker',
                'container_id': container_id,
                'path': path
            }
        
        else:
            print("   ℹ️  请手动下载文件后继续")
            return None
    
    def download_ssh(self, config):
        """通过 SSH 下载文件"""
        print(f"\n📥 正在从 {config['host']} 下载文件...")
        print(f"   命令: scp {config['user']}@{config['host']}:{config['path']} ./vocabulary_data_prod.json\n")
        
        try:
            cmd = f'scp {config["user"]}@{config["host"]}:{config["path"]} ./vocabulary_data_prod.json'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ 文件下载成功！")
                return True
            else:
                print(f"❌ 下载失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ 错误: {e}")
            return False
    
    def download_docker(self, config):
        """通过 Docker 下载文件"""
        print(f"\n📥 正在从 Docker 容器下载文件...")
        print(f"   容器: {config['container_id']}")
        print(f"   路径: {config['path']}\n")
        
        try:
            cmd = f'docker cp {config["container_id"]}:{config["path"]} ./vocabulary_data_prod.json'
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ 文件下载成功！")
                return True
            else:
                print(f"❌ 下载失败: {result.stderr}")
                print("   提示: 确保 Docker 容器正在运行")
                return False
        except Exception as e:
            print(f"❌ 错误: {e}")
            return False
    
    def show_comparison(self):
        """显示数据对比"""
        print("\n" + "=" * 60)
        print("📊 数据对比")
        print("=" * 60)
        
        try:
            result = subprocess.run(
                [sys.executable, 'data_sync.py', '--compare', 'vocabulary_data_prod.json'],
                capture_output=True,
                text=True
            )
            print(result.stdout)
            return True
        except Exception as e:
            print(f"❌ 对比失败: {e}")
            return False
    
    def choose_sync_method(self):
        """选择同步方式"""
        print("\n" + "=" * 60)
        print("🔄 选择同步方式")
        print("=" * 60)
        
        print("""
1. 合并数据（推荐 ⭐）
   - 保留开发环境的所有课程
   - 添加生产环境的新课程
   - 相同课程使用生产环境的数据

2. 替换数据
   - 完全用生产环境数据替换
   - 丢失开发环境原有数据

选择 (1/2) [1]: """)
        
        choice = input().strip() or "1"
        
        if choice == "1":
            return "merge"
        else:
            return "replace"
    
    def execute_sync(self, method):
        """执行同步"""
        print(f"\n⏳ 正在{('合并' if method == 'merge' else '替换')}数据...")
        
        try:
            cmd = [sys.executable, 'data_sync.py', f'--{method}', 'vocabulary_data_prod.json']
            
            # 对于 replace 方法，需要确认
            if method == 'replace':
                response = input("\n⚠️  确认要替换数据? (yes/no): ")
                if response.lower() != 'yes':
                    print("❌ 已取消")
                    return False
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            print(result.stdout)
            
            if result.returncode == 0:
                print("✅ 数据同步成功！")
                return True
            else:
                print(f"❌ 同步失败: {result.stderr}")
                return False
        except Exception as e:
            print(f"❌ 错误: {e}")
            return False
    
    def verify_sync(self):
        """验证同步"""
        print("\n" + "=" * 60)
        print("✓ 同步完成！")
        print("=" * 60)
        
        print("""
下一步操作：

1. 启动开发环境应用：
   python flask_app.py

2. 访问应用：
   http://127.0.0.1:5002

3. 验证：
   - 查看课程列表是否包含新课程
   - 选择新课程并点击播放
   - 查看统计信息

4. 如果有问题，可以恢复备份：
   backups/ 目录中有自动备份

注意：原数据已自动备份到 backups/ 目录！
        """)
    
    def run(self):
        """主流程"""
        print("\n" + "=" * 60)
        print("🔄 自动数据同步助手")
        print("=" * 60)
        
        # 步骤 1: 获取配置
        config = self.get_production_config()
        if not config:
            print("\n📝 请手动下载 vocabulary_data.json 文件")
            print("   然后在本目录保存为 vocabulary_data_prod.json")
            return
        
        # 步骤 2: 下载文件
        if config['type'] == 'SSH':
            if not self.download_ssh(config):
                return
        elif config['type'] == 'Docker':
            if not self.download_docker(config):
                return
        
        # 步骤 3: 对比数据
        if not self.show_comparison():
            return
        
        # 步骤 4: 选择同步方式
        method = self.choose_sync_method()
        
        # 步骤 5: 执行同步
        if not self.execute_sync(method):
            return
        
        # 步骤 6: 验证
        self.verify_sync()

def main():
    """主函数"""
    try:
        sync = AutoSync()
        sync.run()
    except KeyboardInterrupt:
        print("\n\n❌ 已取消")
    except Exception as e:
        print(f"\n❌ 错误: {e}")

if __name__ == '__main__':
    main()
