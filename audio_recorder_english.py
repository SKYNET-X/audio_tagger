#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Audio Recorder v2.1 - English Version
Launch script for English interface
"""

import json
import os
import sys

def set_english_language():
    """Set language to English before starting the program"""
    config_file = 'config.json'
    
    try:
        # Load existing config
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            # Create default config
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
                    "language": "en_US"
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
        
        # Set language to English
        if 'ui_settings' not in config:
            config['ui_settings'] = {}
        config['ui_settings']['language'] = 'en_US'
        
        # Save config
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
            
        print("✅ Language set to English")
        
    except Exception as e:
        print(f"⚠️ Warning: Could not set language to English: {e}")

if __name__ == "__main__":
    print("🎤 Audio Recorder v2.1 - English Version")
    print("=" * 50)
    
    # Set language to English
    set_english_language()
    
    # Import and start the main program
    try:
        from audio_recorder_v2 import *
        
        # Create and run the application
        root = tk.Tk()
        app = AudioRecorder(root)
        
        # Setup window close handler
        def on_closing():
            try:
                app.on_closing()
            except:
                root.destroy()
        
        root.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()
        
    except ImportError as e:
        print(f"❌ Error: Could not import audio_recorder_v2: {e}")
        print("Please make sure audio_recorder_v2.py is in the same directory.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        sys.exit(1)
