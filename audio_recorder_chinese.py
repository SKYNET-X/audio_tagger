#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
语音录制助手 v2.1 - 中文版
中文界面启动脚本
"""

import json
import os
import sys

def set_chinese_language():
    """设置语言为中文"""
    config_file = 'config.json'
    
    try:
        # 加载现有配置
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            # 创建默认配置
            config = {
                "audio_settings": {
                    "sample_rate": 16000,
                    "channels": 1,
                    "audio_format": "WAV",
                    "bit_depth": 16
                },
                "ui_settings": {
                    "window_width": 900,
                    "window_height": 700,
                    "font_family": "微软雅黑",
                    "text_font_size": 16,
                    "ui_font_size": 12,
                    "language": "zh_CN"
                },
                "recording_settings": {
                    "auto_save": True,
                    "confirm_next": False,
                    "show_waveform": False,
                    "enable_shortcuts": True
                },
                "file_settings": {
                    "output_directory": "./recordings",
                    "backup_directory": "./backup",
                    "create_directories": True
                }
            }
        
        # 设置语言为中文
        if 'ui_settings' not in config:
            config['ui_settings'] = {}
        config['ui_settings']['language'] = 'zh_CN'
        
        # 保存配置
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
            
        print("✅ 语言已设置为中文")
        
    except Exception as e:
        print(f"⚠️ 警告：无法设置语言为中文：{e}")

if __name__ == "__main__":
    print("🎤 语音录制助手 v2.1 - 中文版")
    print("=" * 50)
    
    # 设置语言为中文
    set_chinese_language()
    
    # 导入并启动主程序
    try:
        from audio_recorder_v2 import *
        
        # 创建并运行应用程序
        root = tk.Tk()
        app = AudioRecorder(root)
        
        # 设置窗口关闭处理
        def on_closing():
            try:
                app.on_closing()
            except:
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()
        
    except ImportError as e:
        print(f"❌ 错误：无法导入 audio_recorder_v2：{e}")
        print("请确保 audio_recorder_v2.py 在同一目录中。")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 启动应用程序时出错：{e}")
        sys.exit(1)
