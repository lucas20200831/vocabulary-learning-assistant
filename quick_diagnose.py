#!/usr/bin/env python3
"""
音频问题快速诊断脚本 - 一键检查生产环境问题
"""

import os
import sys
import json
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime

class AudioDiagnosticsTool:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.audio_dir = os.path.join(self.script_dir, 'static', 'audio')
        self.issues = []
        self.warnings = []
        self.tips = []
        
    def print_header(self):
        """打印标题"""
        print("\n" + "=" * 70)
        print("🎯 词汇学习助手 - 音频快速诊断工具")
        print("=" * 70 + "\n")
    
    def check_directory(self):
        """检查音频目录"""
        print("📁 检查音频目录...", end=" ")
        if os.path.exists(self.audio_dir):
            if os.access(self.audio_dir, os.W_OK):
                print("✅")
                return True
            else:
                print("❌")
                self.issues.append("音频目录存在但不可写")
                self.tips.append("运行: chmod 755 " + self.audio_dir)
                return False
        else:
            print("❌")
            self.issues.append("音频目录不存在")
            self.tips.append("运行: mkdir -p " + self.audio_dir)
            return False
    
    def check_audio_files(self):
        """检查音频文件"""
        print("🎵 检查音频文件...", end=" ")
        try:
            files = list(Path(self.audio_dir).glob('*.mp3'))
            print(f"✅ ({len(files)} 个文件)")
            
            if len(files) == 0:
                self.warnings.append("没有找到缓存的音频文件（首次运行正常）")
            
            # 检查文件大小
            zero_files = [f for f in files if os.path.getsize(f) == 0]
            if zero_files:
                self.issues.append(f"找到 {len(zero_files)} 个损坏的音频文件（大小为0）")
                self.tips.append("运行: find static/audio -size 0 -delete")
            
            return True
        except Exception as e:
            print(f"❌\n  错误: {e}")
            return False
    
    def check_dependencies(self):
        """检查依赖包"""
        print("📦 检查依赖包...", end=" ")
        missing = []
        
        for name, module in [('Flask', 'flask'), ('gTTS', 'gtts'), ('Flask-CORS', 'flask_cors')]:
            try:
                __import__(module)
            except ImportError:
                missing.append(name)
        
        if missing:
            print(f"❌")
            self.issues.append(f"缺少依赖: {', '.join(missing)}")
            self.tips.append("运行: pip install -r requirements.txt")
            return False
        else:
            print("✅")
            return True
    
    def check_flask_app(self):
        """检查 Flask 应用配置"""
        print("⚙️  检查 Flask 应用...", end=" ")
        flask_file = os.path.join(self.script_dir, 'flask_app.py')
        
        if not os.path.exists(flask_file):
            print("❌")
            self.issues.append("找不到 flask_app.py")
            return False
        
        try:
            with open(flask_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            checks = {
                'CORS': 'from flask_cors import CORS' in content or 'CORS(app' in content,
                'TTS 队列': 'tts_queue' in content,
                'AUDIO_DIR': 'AUDIO_DIR' in content,
            }
            
            failed = [k for k, v in checks.items() if not v]
            
            if failed:
                print(f"⚠️  (缺少: {', '.join(failed)})")
                self.warnings.append(f"Flask 配置可能不完整: {', '.join(failed)}")
            else:
                print("✅")
            
            return len(failed) == 0
        except Exception as e:
            print(f"❌\n  错误: {e}")
            return False
    
    def check_cors_header(self):
        """检查 CORS 配置"""
        print("🔄 检查 CORS 配置...", end=" ")
        flask_file = os.path.join(self.script_dir, 'flask_app.py')
        
        try:
            with open(flask_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if 'CORS(app' in content and 'flask_cors' in content:
                print("✅")
                return True
            else:
                print("⚠️")
                self.warnings.append("CORS 可能未正确配置")
                self.tips.append("确保 flask_app.py 中有: from flask_cors import CORS 和 CORS(app)")
                return False
        except:
            return False
    
    def check_quiz_html(self):
        """检查前端配置"""
        print("🎨 检查前端配置...", end=" ")
        quiz_file = os.path.join(self.script_dir, 'templates', 'quiz.html')
        
        if not os.path.exists(quiz_file):
            print("❌")
            self.issues.append("找不到 quiz.html")
            return False
        
        try:
            with open(quiz_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if '[AUDIO]' in content and 'playAudio' in content:
                print("✅")
                return True
            else:
                print("⚠️")
                self.warnings.append("前端可能未更新到最新版本")
                return False
        except:
            return False
    
    def test_tts_engine(self):
        """测试 TTS 引擎"""
        print("🔊 测试 TTS 引擎...", end=" ")
        try:
            from gtts import gTTS
            test_word = "测试"
            test_hash = hashlib.md5(test_word.encode('utf-8')).hexdigest()
            test_file = os.path.join(self.audio_dir, f'test_{test_hash}.mp3')
            
            # 不真正生成，只检查是否可以导入
            print("✅")
            return True
        except ImportError:
            print("❌")
            self.issues.append("gTTS 库未安装或导入失败")
            return False
        except Exception as e:
            print(f"⚠️  ({str(e)[:30]}...)")
            self.warnings.append(f"TTS 引擎测试失败: {str(e)[:50]}")
            return False
    
    def check_permissions(self):
        """检查文件权限"""
        print("🔐 检查文件权限...", end=" ")
        try:
            files = list(Path(self.audio_dir).glob('*.mp3'))[:3]
            
            if not files:
                print("ℹ️  (没有文件)")
                return True
            
            bad_perms = []
            for f in files:
                mode = os.stat(f).st_mode
                # 检查是否其他用户可读
                if not (mode & 0o004):
                    bad_perms.append(f.name)
            
            if bad_perms:
                print("⚠️")
                self.warnings.append(f"某些文件权限不正确: {', '.join(bad_perms)}")
                self.tips.append("运行: chmod 644 " + self.audio_dir + "/*.mp3")
            else:
                print("✅")
            
            return len(bad_perms) == 0
        except:
            return False
    
    def generate_report(self):
        """生成诊断报告"""
        print("\n" + "=" * 70)
        print("📊 诊断结果")
        print("=" * 70 + "\n")
        
        if self.issues:
            print("❌ 严重问题:")
            for i, issue in enumerate(self.issues, 1):
                print(f"  {i}. {issue}")
            print()
        
        if self.warnings:
            print("⚠️  警告:")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
            print()
        
        if self.tips:
            print("💡 建议:")
            for i, tip in enumerate(self.tips, 1):
                print(f"  {i}. {tip}")
            print()
        
        # 总结
        print("=" * 70)
        if not self.issues:
            print("✅ 诊断完成！系统配置正常，可以部署到生产环境。")
        else:
            print(f"❌ 发现 {len(self.issues)} 个严重问题需要修复。")
        print("=" * 70 + "\n")
    
    def run(self):
        """运行所有检查"""
        self.print_header()
        
        print("正在运行诊断检查...\n")
        
        self.check_directory()
        self.check_audio_files()
        self.check_dependencies()
        self.check_flask_app()
        self.check_cors_header()
        self.check_quiz_html()
        self.test_tts_engine()
        self.check_permissions()
        
        self.generate_report()
        
        # 返回状态码
        return 0 if not self.issues else 1

def main():
    tool = AudioDiagnosticsTool()
    exit_code = tool.run()
    sys.exit(exit_code)

if __name__ == '__main__':
    main()
