#!/usr/bin/env python3
"""
音频诊断工具 - 检查和修复生产环境音频问题
"""

import os
import sys
import json
import hashlib
from pathlib import Path

def diagnose_audio_setup():
    """诊断音频设置"""
    print("=" * 60)
    print("🔍 词汇学习助手 - 音频诊断报告")
    print("=" * 60)
    
    # 1. 检查 AUDIO_DIR
    print("\n✓ 1. 检查音频目录")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    audio_dir = os.path.join(script_dir, 'static', 'audio')
    
    print(f"   预期路径: {audio_dir}")
    if os.path.exists(audio_dir):
        print(f"   ✅ 目录存在")
        # 检查权限
        if os.access(audio_dir, os.W_OK):
            print(f"   ✅ 目录可写")
        else:
            print(f"   ❌ 目录不可写，需要修复权限")
    else:
        print(f"   ❌ 目录不存在，正在创建...")
        try:
            os.makedirs(audio_dir, mode=0o755)
            print(f"   ✅ 目录已创建")
        except Exception as e:
            print(f"   ❌ 创建失败: {e}")
            return False
    
    # 2. 检查现有音频文件
    print("\n✓ 2. 检查现有音频文件")
    audio_files = list(Path(audio_dir).glob('*.mp3'))
    print(f"   找到 {len(audio_files)} 个音频文件")
    if audio_files:
        for f in audio_files[:5]:
            size = os.path.getsize(f)
            print(f"   - {f.name} ({size} bytes)")
        if len(audio_files) > 5:
            print(f"   ... 及其他 {len(audio_files) - 5} 个文件")
    
    # 3. 检查依赖
    print("\n✓ 3. 检查依赖")
    dependencies = {
        'Flask': 'flask',
        'gTTS': 'gtts',
        'Flask-CORS': 'flask_cors'
    }
    
    for name, module in dependencies.items():
        try:
            __import__(module)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ❌ {name} 未安装")
    
    # 4. 测试 gTTS
    print("\n✓ 4. 测试 gTTS 功能")
    try:
        from gtts import gTTS
        test_word = "测试"
        test_hash = hashlib.md5(test_word.encode('utf-8')).hexdigest()
        test_file = os.path.join(audio_dir, f'{test_hash}.mp3')
        
        if os.path.exists(test_file):
            print(f"   ℹ️ 测试文件已存在，跳过生成")
        else:
            print(f"   生成测试音频文件...")
            tts = gTTS(text=test_word, lang='zh-CN', slow=False)
            tts.save(test_file)
            
            if os.path.exists(test_file):
                size = os.path.getsize(test_file)
                print(f"   ✅ 生成成功 ({size} bytes)")
                os.chmod(test_file, 0o644)
                print(f"   ✅ 文件权限已设置")
            else:
                print(f"   ❌ 生成失败")
    except ImportError:
        print(f"   ❌ gTTS 未安装")
    except Exception as e:
        print(f"   ❌ 生成错误: {e}")
    
    # 5. 检查 static 目录结构
    print("\n✓ 5. 检查 static 目录结构")
    static_dir = os.path.join(script_dir, 'static')
    if os.path.exists(static_dir):
        print(f"   ✅ static 目录存在")
        subdirs = [d for d in os.listdir(static_dir) if os.path.isdir(os.path.join(static_dir, d))]
        print(f"   包含子目录: {', '.join(subdirs) if subdirs else '无'}")
    else:
        print(f"   ❌ static 目录不存在")
    
    # 6. 配置建议
    print("\n✓ 6. 生产环境配置建议")
    print("""
   📋 确保以下配置：
   
   a) Web 服务器配置（Nginx/Apache）:
      - 确保 /static/audio/ 目录在 Web 服务器配置中可访问
      - 设置正确的 MIME 类型: audio/mpeg for .mp3
      - 启用 CORS headers（或使用 Flask-CORS）
      
   b) 文件系统权限:
      - static/audio 目录权限: 755 (drwxr-xr-x)
      - 音频文件权限: 644 (-rw-r--r--)
      
   c) Flask 应用配置:
      - CORS 已启用
      - 静态文件路径正确配置
      - 后台线程权限正确
      
   d) 调试检查清单:
      ✓ 浏览器开发者工具 -> Network 查看 /static/audio/*.mp3 请求
      ✓ 查看 /tts/<word> 端点的响应
      ✓ 检查 Flask 日志中是否有 [TTS] 错误信息
      ✓ 验证音频文件确实存在于服务器文件系统
    """)
    
    print("\n" + "=" * 60)
    print("✅ 诊断完成")
    print("=" * 60)
    
    return True

if __name__ == '__main__':
    diagnose_audio_setup()
