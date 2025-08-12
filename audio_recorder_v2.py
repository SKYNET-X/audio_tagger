#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
语音录制程序 - 改进版
用于逐条录制record.txt中的语音素材
使用sounddevice库进行音频录制
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import sys
import time
import subprocess
import numpy as np
import json

# 尝试导入音频库
try:
    import sounddevice as sd
    import soundfile as sf
    AUDIO_AVAILABLE = True
    AUDIO_LIB = "sounddevice"
except ImportError:
    try:
        import pyaudio
        import wave
        AUDIO_AVAILABLE = True
        AUDIO_LIB = "pyaudio"
    except ImportError:
        AUDIO_AVAILABLE = False
        AUDIO_LIB = None
        print("Warning: No audio library available. Audio recording will be simulated.")

# 多语言支持
LANGUAGES = {
    'zh_CN': {
        'title': '语音录制助手 v2.1',
        'welcome_title': '🎤 语音录制助手 v2.1',
        'select_file': '📂 选择文本文件',
        'quick_start': '🚀 快速开始 (record.txt)',
        'start_recording': '🎤 开始录制',
        'stop_recording': '⏹️ 停止录制',
        'next_record': '⏭️ 下一条',
        'prev_record': '⏮️ 上一条',
        're_record': '🔄 重新录制',
        'menu_file': '文件',
        'menu_tools': '工具',
        'menu_help': '帮助',
        'menu_switch_file': '选择文本文件...',
        'menu_open_dir': '打开项目目录',
        'menu_jump': '跳转到指定条目...',
        'menu_batch_check': '批量检查录音',
        'menu_usage': '使用说明',
        'menu_about': '关于',
        'menu_language': '语言',
        'status_ready': '准备就绪',
        'status_recording': '录制中...',
        'status_simulated': '模拟模式',
        'progress_info': '进度：{}/{} | 项目：{}',
        'current_text': '当前文本：',
        'error_no_file': '错误：未找到指定的文本文件',
        'error_no_audio': '没有音频数据可保存',
        'confirm_switch': '确定要切换到其他文件吗？当前进度已保存。',
        'welcome_desc': '选择文本文件开始录制，或使用快速开始加载record.txt',
        'language_changed': '语言已切换，重启程序后生效',
        # 控制台输出信息
        'console_project_dir': '📁 使用项目目录：{}',
        'console_load_file': '📄 加载文本文件：{}',
        'console_total_records': '📊 总计 {} 条记录',
        'console_load_progress': '📖 加载进度：从第 {} 条开始',
        'console_load_failed': '⚠️ 加载进度失败：{}',
        'console_load_failed_restart': '⚠️ 加载进度失败：{}，从头开始',
        # 播放相关状态
        'status_playing': '🔊 正在播放...',
        'status_play_completed': '✅ 播放完成',
        'button_playing': '🔊 播放中...',
        'playback_button': '🔊 试听'
    },
    'en_US': {
        'title': 'Audio Recorder v2.1',
        'welcome_title': '🎤 Audio Recorder v2.1',
        'select_file': '📂 Select Text File',
        'quick_start': '🚀 Quick Start (record.txt)',
        'start_recording': '🎤 Start Recording',
        'stop_recording': '⏹️ Stop Recording',
        'next_record': '⏭️ Next',
        'prev_record': '⏮️ Previous',
        're_record': '🔄 Re-record',
        'menu_file': 'File',
        'menu_tools': 'Tools',
        'menu_help': 'Help',
        'menu_switch_file': 'Select Text File...',
        'menu_open_dir': 'Open Project Directory',
        'menu_jump': 'Jump to Item...',
        'menu_batch_check': 'Batch Check Recordings',
        'menu_usage': 'Usage Guide',
        'menu_about': 'About',
        'menu_language': 'Language',
        'status_ready': 'Ready',
        'status_recording': 'Recording...',
        'status_simulated': 'Simulation Mode',
        'progress_info': 'Progress: {}/{} | Project: {}',
        'current_text': 'Current Text: ',
        'error_no_file': 'Error: Text file not found',
        'error_no_audio': 'No audio data to save',
        'confirm_switch': 'Switch to another file? Current progress has been saved.',
        'welcome_desc': 'Select a text file to start recording, or use Quick Start to load record.txt',
        'language_changed': 'Language changed, restart program to take effect',
        # 控制台输出信息
        'console_project_dir': '📁 Using project directory: {}',
        'console_load_file': '📄 Loading text file: {}',
        'console_total_records': '📊 Total {} records',
        'console_load_progress': '📖 Loading progress: Starting from record {}',
        'console_load_failed': '⚠️ Failed to load progress: {}',
        'console_load_failed_restart': '⚠️ Failed to load progress: {}, starting from beginning',
        # 播放相关状态
        'status_playing': '🔊 Playing...',
        'status_play_completed': '✅ Playback completed',
        'button_playing': '🔊 Playing...',
        'playback_button': '🔊 Playback'
    }
}


class AudioRecorder:
    def __init__(self, root):
        self.root = root
        
        # 加载配置
        self.config = self.load_config()
        
        # 语言设置
        self.current_language = self.config.get('ui_settings', {}).get('language', 'zh_CN')
        self.lang = LANGUAGES.get(self.current_language, LANGUAGES['zh_CN'])
        
        # 设置窗口标题
        self.root.title(self.lang['title'])
        self.root.geometry("950x750")
        
        # 录音参数
        self.sample_rate = self.config.get('audio_settings', {}).get('sample_rate', 16000)
        self.channels = self.config.get('audio_settings', {}).get('channels', 1)
        
        # 文件相关变量
        self.current_text_file = None
        self.current_project_name = None
        self.recordings_base_dir = self.config.get('file_settings', {}).get('output_directory', './recordings')
        self.recordings_dir = None
        self.progress_file = None
        
        # 状态变量
        self.is_recording = False
        self.current_index = 0
        self.records = []
        self.audio_data = []
        self.current_audio_file = None
        
        # 音频相关变量
        if AUDIO_LIB == "pyaudio":
            self.chunk = 1024
            self.format = pyaudio.paInt16
            self.audio = pyaudio.PyAudio()
            self.stream = None
        else:
            self.audio_data_sd = []
        
        # 初始化界面（不加载文件）
        self.setup_main_ui()

    def setup_main_ui(self):
        """设置主界面"""
        # 创建主界面，显示文件选择区域
        self.create_welcome_interface()

    def create_welcome_interface(self):
        """创建欢迎界面"""
        # 配置样式
        style = ttk.Style()
        style.theme_use('clam')
        
        # 主框架
        main_frame = ttk.Frame(self.root, padding="30")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text=self.lang['welcome_title'], 
                               font=("微软雅黑", 24, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 30))
        
        # 音频库状态
        if AUDIO_AVAILABLE:
            if self.current_language == 'zh_CN':
                audio_status = f"✅ 音频库状态：{AUDIO_LIB} 已就绪"
            else:
                audio_status = f"✅ Audio Library: {AUDIO_LIB} Ready"
            status_color = "green"
        else:
            if self.current_language == 'zh_CN':
                audio_status = "⚠️ 音频库状态：模拟模式"
            else:
                audio_status = "⚠️ Audio Library: Simulation Mode"
            status_color = "orange"
        
        status_label = ttk.Label(main_frame, text=audio_status, 
                                font=("微软雅黑", 12), foreground=status_color)
        status_label.grid(row=1, column=0, pady=(0, 40))
        
        # 文件选择区域
        if self.current_language == 'zh_CN':
            file_frame_text = "📁 选择录音项目"
            info_text = "请选择要录制的文本文件开始录音项目\n支持的格式：每行格式为 'ID 录音内容'"
        else:
            file_frame_text = "📁 Select Recording Project"
            info_text = "Please select a text file to start recording project\nSupported format: Each line as 'ID recording_content'"
            
        file_frame = ttk.LabelFrame(main_frame, text=file_frame_text, padding="30")
        file_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        file_frame.columnconfigure(0, weight=1)
        
        # 说明文字
        info_label = ttk.Label(file_frame, 
                              text=info_text, 
                              font=("微软雅黑", 12), 
                              justify=tk.CENTER)
        info_label.grid(row=0, column=0, pady=(0, 20))
        
        # 按钮区域
        button_frame = ttk.Frame(file_frame)
        button_frame.grid(row=1, column=0)
        
        # 样式设置
        style.configure("Large.TButton", font=("微软雅黑", 14, "bold"), padding=(30, 15))
        
        # 选择文件按钮
        select_button = ttk.Button(button_frame, text=self.lang['select_file'], 
                                  command=self.select_text_file_manual,
                                  style="Large.TButton")
        select_button.pack(side=tk.LEFT, padx=(0, 20))
        
        # 快速开始按钮（如果有record.txt）
        if os.path.exists('record.txt'):
            quick_button = ttk.Button(button_frame, text=self.lang['quick_start'], 
                                     command=lambda: self.load_text_file_and_start('record.txt'),
                                     style="Large.TButton")
            quick_button.pack(side=tk.LEFT)
        
        # 创建菜单栏
        self.create_welcome_menu()

    def create_welcome_menu(self):
        """创建欢迎界面的菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.lang['menu_file'], menu=file_menu)
        file_menu.add_command(label=self.lang['menu_switch_file'], command=self.select_text_file_manual)
        file_menu.add_separator()
        if self.current_language == 'zh_CN':
            file_menu.add_command(label="退出", command=self.root.quit)
        else:
            file_menu.add_command(label="Exit", command=self.root.quit)
        
        # 语言菜单
        language_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.lang['menu_language'], menu=language_menu)
        language_menu.add_command(label="中文", command=lambda: self.switch_language('zh_CN'))
        language_menu.add_command(label="English", command=lambda: self.switch_language('en_US'))
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.lang['menu_help'], menu=help_menu)
        help_menu.add_command(label="使用说明", command=self.show_usage_help)
        help_menu.add_command(label="关于", command=self.show_about_welcome)

    def switch_language(self, language_code):
        """切换语言"""
        if language_code in LANGUAGES:
            # 更新配置文件
            self.config['ui_settings']['language'] = language_code
            self.save_config()
            
            # 显示提示信息
            messagebox.showinfo("语言切换", self.lang['language_changed'])
        
    def save_config(self):
        """保存配置到文件"""
        try:
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置失败: {e}")

    def select_text_file_manual(self):
        """手动选择文本文件"""
        if self.current_language == 'zh_CN':
            dialog_title = "选择要录制的文本文件"
            file_types = [("文本文件", "*.txt"), ("所有文件", "*.*")]
        else:
            dialog_title = "Select Text File to Record"
            file_types = [("Text Files", "*.txt"), ("All Files", "*.*")]
            
        file_path = filedialog.askopenfilename(
            title=dialog_title,
            filetypes=file_types
        )
        
        if file_path:
            # 如果已经在录音界面，需要重新初始化
            if hasattr(self, 'current_text_file') and self.current_text_file:
                self.load_text_file_and_restart(file_path)
            else:
                self.load_text_file_and_start(file_path)

    def load_text_file_and_restart(self, file_path):
        """重新加载文本文件（用于切换文件）"""
        try:
            self.current_text_file = file_path
            self.current_project_name = os.path.splitext(os.path.basename(file_path))[0]
            
            # 创建项目特定的录音目录
            self.recordings_dir = os.path.join(self.recordings_base_dir, self.current_project_name)
            self.progress_file = os.path.join(self.recordings_dir, 'progress.json')
            
            # 创建目录
            self.create_recordings_directory()
            
            # 读取记录
            self.load_records()
            
            # 加载进度
            self.load_progress()
            
            # 清除当前界面
            for widget in self.root.winfo_children():
                widget.destroy()
            
            # 重新创建录音界面
            self.setup_recording_ui()
            
            # 显示当前记录
            self.show_current_record()
            
            messagebox.showinfo("成功", f"已切换到项目：{self.current_project_name}")
            
        except Exception as e:
            messagebox.showerror("错误", f"切换文件失败：{str(e)}")

    def load_text_file_and_start(self, file_path):
        """加载文本文件并开始录音项目"""
        try:
            self.current_text_file = file_path
            self.current_project_name = os.path.splitext(os.path.basename(file_path))[0]
            
            # 创建项目特定的录音目录
            self.recordings_dir = os.path.join(self.recordings_base_dir, self.current_project_name)
            self.progress_file = os.path.join(self.recordings_dir, 'progress.json')
            
            # 创建目录
            self.create_recordings_directory()
            
            # 读取记录
            self.load_records()
            
            # 加载进度
            self.load_progress()
            
            # 清除欢迎界面
            for widget in self.root.winfo_children():
                widget.destroy()
            
            # 创建录音界面
            self.setup_recording_ui()
            
            # 显示当前记录
            self.show_current_record()
            
        except Exception as e:
            messagebox.showerror("错误", f"加载文件失败：{str(e)}")

    def show_usage_help(self):
        """显示使用说明"""
        help_text = """📖 使用说明

1. 🎯 准备文本文件
   - 每行格式：ID 录音内容
   - 例如：000001 这是要录制的文本

2. 📂 选择文件
   - 点击"选择文本文件"按钮
   - 或使用"快速开始"加载record.txt

3. 🎤 开始录音
   - 空格键：开始/停止录制
   - 回车键：下一条
   - 退格键：上一条
   - P键：试听录音

4. 💾 自动保存
   - 录音文件自动保存到项目目录
   - 进度自动保存，下次启动可继续"""
        
        messagebox.showinfo("使用说明", help_text)

    def show_about_welcome(self):
        """显示关于信息（欢迎界面版本）"""
        about_text = f"""语音录制助手 v2.1

🎤 专业的语音数据录制工具
🎵 音频格式：16kHz WAV
📁 支持多项目管理
💾 自动进度保存

© 2025 语音录制助手"""
        
        messagebox.showinfo("关于", about_text)

    def load_config(self):
        """加载配置文件"""
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("⚠️ 配置文件config.json不存在，使用默认配置")
            return {}
        except Exception as e:
            print(f"⚠️ 加载配置文件失败：{e}，使用默认配置")
            return {}

    def show_file_selection(self):
        """显示文件选择对话框"""
        # 首先检查是否有record.txt作为默认选项
        if os.path.exists('record.txt'):
            result = messagebox.askyesnocancel(
                "选择文本文件", 
                "发现record.txt文件，是否使用该文件进行录制？\n\n"
                "是: 使用record.txt\n"
                "否: 选择其他文件\n"
                "取消: 退出程序"
            )
            if result is True:
                self.load_text_file('record.txt')
                return
            elif result is False:
                self.select_text_file()
                return
            else:
                self.root.quit()
                return
        else:
            self.select_text_file()

    def select_text_file(self):
        """选择文本文件"""
        file_path = filedialog.askopenfilename(
            title="选择要录制的文本文件",
            filetypes=[
                ("文本文件", "*.txt"),
                ("所有文件", "*.*")
            ]
        )
        
        if file_path:
            self.load_text_file(file_path)
        else:
            self.root.quit()

    def load_text_file(self, file_path):
        """加载文本文件并初始化项目"""
        self.current_text_file = file_path
        self.current_project_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # 创建项目特定的录音目录
        self.recordings_dir = os.path.join(self.recordings_base_dir, self.current_project_name)
        self.progress_file = os.path.join(self.recordings_dir, 'progress.json')
        
        # 创建目录
        self.create_recordings_directory()
        
        # 读取记录
        self.load_records()
        
        # 验证和修复进度文件
        self.validate_progress_file()
        
        # 加载进度
        self.load_progress()
        
        # 创建界面
        self.setup_recording_ui()
        
        # 显示当前记录
        self.show_current_record()

    def load_progress(self):
        """加载录制进度"""
        try:
            if os.path.exists(self.progress_file):
                # 检查文件大小
                if os.path.getsize(self.progress_file) == 0:
                    print(f"⚠️ 进度文件为空，删除并重新检测进度")
                    os.remove(self.progress_file)
                    self.current_index = self.detect_current_progress()
                    print(f"📝 自动检测进度：从第 {self.current_index + 1} 条开始")
                    return
                
                # 尝试读取JSON文件
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    file_content = f.read().strip()
                    if not file_content:
                        print(f"⚠️ 进度文件内容为空，自动检测进度")
                        self.current_index = self.detect_current_progress()
                        print(f"📝 自动检测进度：从第 {self.current_index + 1} 条开始")
                        return
                    
                    progress_data = json.loads(file_content)
                    self.current_index = progress_data.get('current_index', 0)
                    
                    # 确保索引在有效范围内
                    if self.current_index >= len(self.records):
                        self.current_index = len(self.records) - 1
                    elif self.current_index < 0:
                        self.current_index = 0
                    
                    print(self.lang['console_load_progress'].format(self.current_index + 1))
            else:
                # 如果没有进度文件，尝试自动检测已录制的文件
                self.current_index = self.detect_current_progress()
                if self.current_language == 'zh_CN':
                    print(f"📝 自动检测进度：从第 {self.current_index + 1} 条开始")
                else:
                    print(f"📝 Auto-detected progress: Starting from record {self.current_index + 1}")
        except json.JSONDecodeError as e:
            if self.current_language == 'zh_CN':
                print(f"⚠️ 进度文件JSON格式错误：{e}")
                print(f"🔧 尝试修复：备份损坏文件并重新检测进度")
            else:
                print(f"⚠️ Progress file JSON format error: {e}")
                print(f"🔧 Attempting repair: Backing up corrupted file and re-detecting progress")
            try:
                # 备份损坏的文件
                backup_file = self.progress_file + f".backup_{int(time.time())}"
                os.rename(self.progress_file, backup_file)
                if self.current_language == 'zh_CN':
                    print(f"📦 已备份损坏文件到：{backup_file}")
                else:
                    print(f"📦 Backed up corrupted file to: {backup_file}")
            except:
                pass
            # 重新检测进度
            self.current_index = self.detect_current_progress()
            if self.current_language == 'zh_CN':
                print(f"📝 自动检测进度：从第 {self.current_index + 1} 条开始")
            else:
                print(f"📝 Auto-detected progress: Starting from record {self.current_index + 1}")
        except Exception as e:
            print(self.lang['console_load_failed'].format(e))
            if self.current_language == 'zh_CN':
                print(f"🔧 尝试自动检测进度")
            else:
                print(f"🔧 Attempting auto-detection of progress")
            try:
                self.current_index = self.detect_current_progress()
                if self.current_language == 'zh_CN':
                    print(f"📝 自动检测进度：从第 {self.current_index + 1} 条开始")
                else:
                    print(f"📝 Auto-detected progress: Starting from record {self.current_index + 1}")
            except:
                if self.current_language == 'zh_CN':
                    print(f"⚠️ 自动检测也失败，从头开始")
                else:
                    print(f"⚠️ Auto-detection also failed, starting from beginning")
                self.current_index = 0

    def create_recordings_directory(self):
        """加载录制进度"""
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
                    self.current_index = progress_data.get('current_index', 0)
                    
                    # 确保索引在有效范围内
                    if self.current_index >= len(self.records):
                        self.current_index = len(self.records) - 1
                    
                    print(self.lang['console_load_progress'].format(self.current_index + 1))
            else:
                # 如果没有进度文件，尝试自动检测已录制的文件
                self.current_index = self.detect_current_progress()
                if self.current_language == 'zh_CN':
                    print(f"📝 自动检测进度：从第 {self.current_index + 1} 条开始")
                else:
                    print(f"📝 Auto-detected progress: Starting from record {self.current_index + 1}")
        except Exception as e:
            print(self.lang['console_load_failed_restart'].format(e))
            self.current_index = 0

    def detect_current_progress(self):
        """自动检测当前录制进度"""
        # 检查已录制的文件，找到最后一个连续的录制文件
        for i, record in enumerate(self.records):
            audio_file = os.path.join(self.recordings_dir, f"{record['id']}.wav")
            if not os.path.exists(audio_file):
                return i  # 返回第一个未录制的文件索引
        
        # 如果所有文件都存在，返回最后一个索引
        return len(self.records) - 1 if self.records else 0

    def save_progress(self):
        """保存录制进度"""
        # 如果没有进度文件路径，则跳过保存
        if not self.progress_file:
            return
            
        try:
            progress_data = {
                'current_index': self.current_index,
                'project_name': self.current_project_name,
                'text_file': self.current_text_file,
                'total_records': len(self.records),
                'last_updated': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # 使用临时文件进行原子写入，避免写入过程中被读取
            temp_file = self.progress_file + '.tmp'
            
            # 写入临时文件
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
            
            # 原子替换：先删除旧文件（如果存在），再重命名临时文件
            if os.path.exists(self.progress_file):
                os.remove(self.progress_file)
            os.rename(temp_file, self.progress_file)
            
        except Exception as e:
            print(f"⚠️ 保存进度失败：{e}")
            # 清理临时文件
            temp_file = self.progress_file + '.tmp'
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
    
    def create_recordings_directory(self):
        """创建录音文件夹"""
        try:
            if not os.path.exists(self.recordings_dir):
                os.makedirs(self.recordings_dir)
                if self.current_language == 'zh_CN':
                    print(f"📁 创建项目目录：{self.recordings_dir}")
                else:
                    print(f"📁 Created project directory: {self.recordings_dir}")
                
                # 检查是否有旧的录音文件需要迁移
                self.migrate_old_recordings()
            else:
                print(self.lang['console_project_dir'].format(self.recordings_dir))
        except Exception as e:
            if self.current_language == 'zh_CN':
                print(f"⚠️ 创建项目目录失败：{e}")
            else:
                print(f"⚠️ Failed to create project directory: {e}")
            self.recordings_dir = "."  # 使用当前目录作为备选

    def migrate_old_recordings(self):
        """迁移旧的录音文件到新的项目目录结构"""
        if self.current_project_name != "record":
            return  # 只有record项目需要迁移
        
        old_recordings_dir = "./recordings"
        if not os.path.exists(old_recordings_dir):
            return
        
        migrated_count = 0
        try:
            for file in os.listdir(old_recordings_dir):
                if file.endswith('.wav') and file.startswith('0000'):
                    old_path = os.path.join(old_recordings_dir, file)
                    new_path = os.path.join(self.recordings_dir, file)
                    
                    if os.path.isfile(old_path):
                        # 移动文件到新目录
                        os.rename(old_path, new_path)
                        migrated_count += 1
            
            if migrated_count > 0:
                print(f"📦 迁移了 {migrated_count} 个旧录音文件")
                
        except Exception as e:
            print(f"⚠️ 迁移录音文件时出错：{e}")
    
    def load_records(self):
        """读取文本文件"""
        try:
            with open(self.current_text_file, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if line:
                        parts = line.split(' ', 1)
                        if len(parts) == 2:
                            record_id, text = parts
                            self.records.append({'id': record_id, 'text': text})
            print(self.lang['console_load_file'].format(self.current_text_file))
            print(self.lang['console_total_records'].format(len(self.records)))
        except FileNotFoundError:
            if self.current_language == 'zh_CN':
                messagebox.showerror("错误", f"找不到文件：{self.current_text_file}！")
            else:
                messagebox.showerror("Error", f"File not found: {self.current_text_file}!")
            self.root.quit()
        except Exception as e:
            if self.current_language == 'zh_CN':
                messagebox.showerror("错误", f"读取文件时出错：{str(e)}")
            else:
                messagebox.showerror("Error", f"Error reading file: {str(e)}")
            self.root.quit()

    def validate_progress_file(self):
        """验证和修复进度文件"""
        if not os.path.exists(self.progress_file):
            return  # 文件不存在，稍后会自动创建
        
        try:
            # 检查文件大小
            if os.path.getsize(self.progress_file) == 0:
                print(f"🔧 检测到空的进度文件，将删除")
                os.remove(self.progress_file)
                return
            
            # 尝试解析JSON
            with open(self.progress_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    print(f"🔧 检测到空内容的进度文件，将删除")
                    os.remove(self.progress_file)
                    return
                
                # 验证JSON格式
                progress_data = json.loads(content)
                
                # 验证必要字段
                required_fields = ['current_index', 'project_name', 'text_file', 'total_records']
                for field in required_fields:
                    if field not in progress_data:
                        print(f"🔧 进度文件缺少字段 {field}，将重新生成")
                        os.remove(self.progress_file)
                        return
                
                # 验证数据类型
                if not isinstance(progress_data['current_index'], int) or progress_data['current_index'] < 0:
                    print(f"🔧 进度文件索引值无效，将重新生成")
                    os.remove(self.progress_file)
                    return
                
                print(f"✅ 进度文件验证通过")
                
        except json.JSONDecodeError as e:
            print(f"🔧 进度文件JSON格式错误，将删除并重新生成：{e}")
            try:
                os.remove(self.progress_file)
            except:
                pass
        except Exception as e:
            print(f"🔧 验证进度文件时出错，将删除：{e}")
            try:
                os.remove(self.progress_file)
            except:
                pass
    
    def setup_recording_ui(self):
        """创建录音界面"""
        # 配置样式
        style = ttk.Style()
        style.theme_use('clam')
        
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)
        
        # 标题和状态
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 20))
        header_frame.columnconfigure(0, weight=1)
        
        title_label = ttk.Label(header_frame, text=self.lang['welcome_title'], 
                               font=("微软雅黑", 18, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 5))
        
        # 项目信息
        if self.current_language == 'zh_CN':
            project_info = f"📁 项目：{self.current_project_name} | 📄 文件：{os.path.basename(self.current_text_file)}"
        else:
            project_info = f"📁 Project: {self.current_project_name} | 📄 File: {os.path.basename(self.current_text_file)}"
        project_label = ttk.Label(header_frame, text=project_info, 
                                 font=("微软雅黑", 10), foreground="blue")
        project_label.grid(row=1, column=0, pady=(0, 10))
        
        # 音频库状态
        if AUDIO_AVAILABLE:
            if self.current_language == 'zh_CN':
                audio_status = f"✅ 音频库：{AUDIO_LIB}"
            else:
                audio_status = f"✅ Audio: {AUDIO_LIB}"
            status_color = "green"
        else:
            if self.current_language == 'zh_CN':
                audio_status = "⚠️ 音频库：模拟模式"
            else:
                audio_status = "⚠️ Audio: Simulation Mode"
            status_color = "orange"
        
        status_label = ttk.Label(header_frame, text=audio_status, 
                                font=("微软雅黑", 10), foreground=status_color)
        status_label.grid(row=2, column=0)
        
        # 进度信息框架
        if self.current_language == 'zh_CN':
            progress_frame_text = "录制进度"
            current_progress_text = "当前进度："
            current_id_text = "当前ID："
        else:
            progress_frame_text = "Recording Progress"
            current_progress_text = "Current Progress:"
            current_id_text = "Current ID:"
            
        progress_frame = ttk.LabelFrame(main_frame, text=progress_frame_text, padding="15")
        progress_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        progress_frame.columnconfigure(1, weight=1)
        
        # 进度信息
        ttk.Label(progress_frame, text=current_progress_text, font=("微软雅黑", 11)).grid(row=0, column=0, sticky=tk.W)
        self.progress_label = ttk.Label(progress_frame, text="", font=("微软雅黑", 11, "bold"))
        self.progress_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        ttk.Label(progress_frame, text=current_id_text, font=("微软雅黑", 11)).grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.id_label = ttk.Label(progress_frame, text="", font=("微软雅黑", 11, "bold"), 
                                 foreground="blue")
        self.id_label.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(5, 0))
        
        # 录制内容显示
        if self.current_language == 'zh_CN':
            content_frame_text = "📝 要录制的内容"
        else:
            content_frame_text = "📝 Content to Record"
            
        content_frame = ttk.LabelFrame(main_frame, text=content_frame_text, padding="15")
        content_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)
        
        # 文本显示区域
        text_frame = ttk.Frame(content_frame)
        text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        text_frame.columnconfigure(0, weight=1)
        text_frame.rowconfigure(0, weight=1)
        
        self.text_display = tk.Text(text_frame, wrap=tk.WORD, font=("微软雅黑", 16),
                                   height=6, state=tk.DISABLED, bg="white", 
                                   relief="solid", borderwidth=1)
        self.text_display.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 5))
        
        # 滚动条
        text_scrollbar = ttk.Scrollbar(text_frame, orient="vertical", 
                                      command=self.text_display.yview)
        text_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.text_display.configure(yscrollcommand=text_scrollbar.set)
        
        # 录制状态框架
        if self.current_language == 'zh_CN':
            status_frame_text = "🔴 录制状态"
            initial_status = "准备录制"
        else:
            status_frame_text = "🔴 Recording Status"
            initial_status = "Ready to record"
            
        status_frame = ttk.LabelFrame(main_frame, text=status_frame_text, padding="15")
        status_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        
        self.recording_status = ttk.Label(status_frame, text=initial_status, 
                                         font=("微软雅黑", 14, "bold"), foreground="green")
        self.recording_status.pack()
        
        # 控制按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, pady=(0, 10))
        
        # 按钮样式
        style.configure("Record.TButton", font=("微软雅黑", 12, "bold"), padding=(20, 10))
        style.configure("Next.TButton", font=("微软雅黑", 12), padding=(20, 10))
        style.configure("Finish.TButton", font=("微软雅黑", 12), padding=(20, 10))
        style.configure("Play.TButton", font=("微软雅黑", 12), padding=(20, 10))
        
        self.record_button = ttk.Button(button_frame, text=self.lang['start_recording'], 
                                       command=self.toggle_recording,
                                       style="Record.TButton")
        self.record_button.pack(side=tk.LEFT, padx=(0, 15))
        
        self.play_button = ttk.Button(button_frame, text=self.lang['playback_button'], 
                                     command=self.play_audio,
                                     state=tk.DISABLED, style="Play.TButton")
        self.play_button.pack(side=tk.LEFT, padx=(0, 15))
        
        self.prev_button = ttk.Button(button_frame, text=self.lang['prev_record'], 
                                     command=self.prev_record,
                                     state=tk.DISABLED, style="Next.TButton")
        self.prev_button.pack(side=tk.LEFT, padx=(0, 15))
        
        self.next_button = ttk.Button(button_frame, text=self.lang['next_record'], 
                                     command=self.next_record,
                                     state=tk.DISABLED, style="Next.TButton")
        self.next_button.pack(side=tk.LEFT, padx=(0, 15))
        
        if self.current_language == 'zh_CN':
            finish_text = "🏁 结束录制"
            help_text = "💡 提示：按 空格键 开始/停止录制，按 Enter键 下一条，按 Backspace键 上一条，按 P键 试听"
        else:
            finish_text = "🏁 Finish"
            help_text = "💡 Tip: Press Space to start/stop recording, Enter for next, Backspace for previous, P for playback"
            
        self.finish_button = ttk.Button(button_frame, text=finish_text, 
                                       command=self.finish_recording,
                                       style="Finish.TButton")
        self.finish_button.pack(side=tk.LEFT)
        
        # 快捷键说明
        help_frame = ttk.Frame(main_frame)
        help_frame.grid(row=5, column=0, pady=(10, 0))
        
        help_label = ttk.Label(help_frame, text=help_text, 
                              font=("微软雅黑", 9), foreground="gray")
        help_label.pack()
        
        # 绑定快捷键
        self.root.bind('<space>', lambda e: self.toggle_recording())
        self.root.bind('<Return>', lambda e: self.next_record() if self.next_button['state'] != tk.DISABLED else None)
        self.root.bind('<BackSpace>', lambda e: self.prev_record() if self.prev_button['state'] != tk.DISABLED else None)
        self.root.bind('<KeyPress-p>', lambda e: self.play_audio() if self.play_button['state'] != tk.DISABLED else None)
        self.root.bind('<KeyPress-P>', lambda e: self.play_audio() if self.play_button['state'] != tk.DISABLED else None)
        self.root.bind('<Control-o>', lambda e: self.switch_text_file())
        self.root.bind('<Control-e>', lambda e: self.open_project_directory())
        self.root.bind('<Control-g>', lambda e: self.jump_to_record())
        self.root.focus_set()
        
        # 创建菜单栏
        self.create_menu()

    def create_menu(self):
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.lang['menu_file'], menu=file_menu)
        file_menu.add_command(label=self.lang['menu_switch_file'], command=self.switch_text_file)
        file_menu.add_separator()
        file_menu.add_command(label=self.lang['menu_open_dir'], command=self.open_project_directory)
        file_menu.add_separator()
        if self.current_language == 'zh_CN':
            file_menu.add_command(label="退出", command=self.on_closing)
        else:
            file_menu.add_command(label="Exit", command=self.on_closing)
        
        # 工具菜单
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.lang['menu_tools'], menu=tools_menu)
        tools_menu.add_command(label=self.lang['menu_jump'], command=self.jump_to_record)
        tools_menu.add_command(label=self.lang['menu_batch_check'], command=self.batch_check_recordings)
        
        # 语言菜单
        language_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.lang['menu_language'], menu=language_menu)
        language_menu.add_command(label="中文", command=lambda: self.switch_language('zh_CN'))
        language_menu.add_command(label="English", command=lambda: self.switch_language('en_US'))
        
        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label=self.lang['menu_help'], menu=help_menu)
        if self.current_language == 'zh_CN':
            help_menu.add_command(label="快捷键说明", command=self.show_shortcuts)
            help_menu.add_command(label="关于", command=self.show_about)
        else:
            help_menu.add_command(label="Shortcuts", command=self.show_shortcuts)
            help_menu.add_command(label="About", command=self.show_about)

    def switch_text_file(self):
        """切换文本文件"""
        if self.is_recording:
            if self.current_language == 'zh_CN':
                messagebox.showwarning("警告", "请先停止录制再切换文件！")
            else:
                messagebox.showwarning("Warning", "Please stop recording before switching files!")
            return
        
        if self.current_language == 'zh_CN':
            result = messagebox.askyesno("确认", "切换文件将保存当前进度，确定继续吗？")
        else:
            result = messagebox.askyesno("Confirm", "Switching files will save current progress, continue?")
        if result:
            self.save_progress()
            # 直接调用文件选择，不需要额外处理
            if self.current_language == 'zh_CN':
                dialog_title = "选择要录制的文本文件"
                file_types = [("文本文件", "*.txt"), ("所有文件", "*.*")]
            else:
                dialog_title = "Select Text File to Record"
                file_types = [("Text Files", "*.txt"), ("All Files", "*.*")]
                
            file_path = filedialog.askopenfilename(
                title=dialog_title,
                filetypes=file_types
            )
            
            if file_path:
                self.load_text_file_and_restart(file_path)

    def open_project_directory(self):
        """打开项目目录"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(self.recordings_dir)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.call(('open' if sys.platform == 'darwin' else 'xdg-open', self.recordings_dir))
        except Exception as e:
            messagebox.showerror("错误", f"无法打开目录：{str(e)}")

    def jump_to_record(self):
        """跳转到指定条目"""
        if self.is_recording:
            messagebox.showwarning("警告", "请先停止录制再跳转！")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("跳转到条目")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 居中显示
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text=f"请输入条目编号 (1-{len(self.records)}):").pack(pady=(0, 10))
        
        entry = ttk.Entry(frame, width=10)
        entry.pack(pady=(0, 20))
        entry.focus()
        
        def jump():
            try:
                index = int(entry.get()) - 1
                if 0 <= index < len(self.records):
                    self.current_index = index
                    self.save_progress()
                    self.show_current_record()
                    dialog.destroy()
                else:
                    messagebox.showerror("错误", f"编号必须在1-{len(self.records)}之间！")
            except ValueError:
                messagebox.showerror("错误", "请输入有效的数字！")
        
        button_frame = ttk.Frame(frame)
        button_frame.pack()
        
        ttk.Button(button_frame, text="跳转", command=jump).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="取消", command=dialog.destroy).pack(side=tk.LEFT)
        
        entry.bind('<Return>', lambda e: jump())

    def batch_check_recordings(self):
        """批量检查录音文件"""
        missing_files = []
        for i, record in enumerate(self.records):
            audio_file = os.path.join(self.recordings_dir, f"{record['id']}.wav")
            if not os.path.exists(audio_file):
                missing_files.append(f"{i+1}: {record['id']}")
        
        if missing_files:
            message = f"发现 {len(missing_files)} 个缺失的录音文件：\n\n"
            message += "\n".join(missing_files[:10])  # 只显示前10个
            if len(missing_files) > 10:
                message += f"\n... 还有 {len(missing_files) - 10} 个"
        else:
            message = "🎉 所有录音文件都已存在！"
        
        messagebox.showinfo("录音检查结果", message)

    def show_shortcuts(self):
        """显示快捷键说明"""
        shortcuts = """快捷键说明：

🎤 空格键：开始/停止录制
⏭️ 回车键：下一条
⏮️ 退格键：上一条
🔊 P 键：试听当前录音

📁 Ctrl+O：切换文本文件
📂 Ctrl+E：打开项目目录
🔍 Ctrl+G：跳转到指定条目"""
        
        messagebox.showinfo("快捷键说明", shortcuts)

    def show_about(self):
        """显示关于信息"""
        about_text = f"""语音录制助手 v2.1

📁 当前项目：{self.current_project_name}
📄 文本文件：{os.path.basename(self.current_text_file)}
📊 总计条目：{len(self.records)}
📈 当前进度：{self.current_index + 1}/{len(self.records)}
🎵 音频格式：{self.sample_rate}Hz, {self.channels}声道

© 2025 语音录制助手"""
        
        messagebox.showinfo("关于", about_text)
    
    def show_current_record(self):
        """显示当前记录"""
        if self.current_index < len(self.records):
            record = self.records[self.current_index]
            
            # 更新进度
            progress_text = f"{self.current_index + 1} / {len(self.records)}"
            self.progress_label.config(text=progress_text)
            
            # 更新ID
            self.id_label.config(text=record['id'])
            
            # 更新文本内容
            self.text_display.config(state=tk.NORMAL)
            self.text_display.delete(1.0, tk.END)
            self.text_display.insert(1.0, record['text'])
            self.text_display.config(state=tk.DISABLED)
            
            # 初始化按钮状态
            self.record_button.config(state=tk.NORMAL)
            
            # 控制上一条按钮状态
            if self.current_index > 0:
                self.prev_button.config(state=tk.NORMAL)
            else:
                self.prev_button.config(state=tk.DISABLED)
            
            # 检查是否已有录制的文件
            self.current_audio_file = os.path.join(self.recordings_dir, f"{record['id']}.wav")
            if os.path.exists(self.current_audio_file):
                # 已有录制文件的情况
                self.play_button.config(state=tk.NORMAL)
                self.next_button.config(state=tk.NORMAL)  # 已录制，可以进入下一条
                self.record_button.config(text=self.lang['re_record'])
                if self.current_language == 'zh_CN':
                    self.recording_status.config(text="✅ 已有录制文件", foreground="blue")
                else:
                    self.recording_status.config(text="✅ Recording exists", foreground="blue")
            else:
                # 没有录制文件的情况
                self.play_button.config(state=tk.DISABLED)
                self.next_button.config(state=tk.DISABLED)  # 未录制，不能进入下一条
                self.record_button.config(text=self.lang['start_recording'])
                if self.current_language == 'zh_CN':
                    self.recording_status.config(text="准备录制", foreground="green")
                else:
                    self.recording_status.config(text="Ready to record", foreground="green")
        else:
            # 所有记录已完成
            if self.current_language == 'zh_CN':
                complete_msg = f"🎉 所有 {len(self.records)} 条语音录制已完成！"
                complete_title = "完成"
            else:
                complete_msg = f"🎉 All {len(self.records)} recordings completed!"
                complete_title = "Completed"
            messagebox.showinfo(complete_title, complete_msg)
            self.root.quit()
    
    def toggle_recording(self):
        """切换录制状态"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        """开始录制"""
        self.is_recording = True
        self.audio_data = []
        
        # 更新界面状态
        if self.current_language == 'zh_CN':
            status_text = "🔴 正在录制..."
        else:
            status_text = "🔴 Recording..."
        self.recording_status.config(text=status_text, foreground="red")
        self.record_button.config(text=self.lang['stop_recording'])
        
        if AUDIO_AVAILABLE:
            if AUDIO_LIB == "sounddevice":
                self.start_sounddevice_recording()
            elif AUDIO_LIB == "pyaudio":
                self.start_pyaudio_recording()
        else:
            # 模拟录制
            self.recording_status.config(text="🔴 正在录制（模拟）...", foreground="red")
    
    def start_sounddevice_recording(self):
        """使用sounddevice开始录制"""
        try:
            self.audio_data_sd = []
            
            def audio_callback(indata, frames, time, status):
                if status:
                    print(f"Audio callback status: {status}")
                if self.is_recording:
                    self.audio_data_sd.append(indata.copy())
            
            # 开始录制流
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=audio_callback,
                dtype=np.float32
            )
            self.stream.start()
            
        except Exception as e:
            messagebox.showerror("错误", f"开始录制失败：{str(e)}")
            self.is_recording = False
            self.recording_status.config(text="录制失败", foreground="red")
    
    def start_pyaudio_recording(self):
        """使用pyaudio开始录制"""
        try:
            self.stream = self.audio.open(
                format=self.format,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk
            )
            
            # 开始录制线程
            self.recording_thread = threading.Thread(target=self._record_pyaudio)
            self.recording_thread.start()
            
        except Exception as e:
            messagebox.showerror("错误", f"开始录制失败：{str(e)}")
            self.is_recording = False
            self.recording_status.config(text="录制失败", foreground="red")
    
    def _record_pyaudio(self):
        """PyAudio录制线程"""
        try:
            while self.is_recording:
                data = self.stream.read(self.chunk)
                self.audio_data.append(data)
        except Exception as e:
            print(f"录制过程中出错：{str(e)}")
    
    def stop_recording(self):
        """停止录制"""
        if not self.is_recording:
            return
        
        self.is_recording = False
        
        # 停止音频流
        if AUDIO_AVAILABLE and hasattr(self, 'stream') and self.stream:
            if AUDIO_LIB == "sounddevice":
                self.stream.stop()
                self.stream.close()
            elif AUDIO_LIB == "pyaudio":
                self.stream.stop_stream()
                self.stream.close()
            self.stream = None
        
        # 更新界面状态
        if self.current_language == 'zh_CN':
            complete_text = "✅ 录制完成"
        else:
            complete_text = "✅ Recording completed"
        self.recording_status.config(text=complete_text, foreground="blue")
        self.record_button.config(text=self.lang['re_record'])
        self.next_button.config(state=tk.NORMAL)
        
        # 控制上一条按钮状态
        if self.current_index > 0:
            self.prev_button.config(state=tk.NORMAL)
        else:
            self.prev_button.config(state=tk.DISABLED)
        
        # 保存音频文件
        self.save_audio()
        
        # 启用试听按钮
        self.play_button.config(state=tk.NORMAL)
    
    def save_audio(self):
        """保存音频文件"""
        if self.current_index >= len(self.records):
            return
        
        record = self.records[self.current_index]
        filename = f"{record['id']}.wav"
        filepath = os.path.join(self.recordings_dir, filename)
        self.current_audio_file = filepath
        
        try:
            if AUDIO_AVAILABLE:
                if AUDIO_LIB == "sounddevice" and hasattr(self, 'audio_data_sd') and self.audio_data_sd:
                    # 使用soundfile保存
                    audio_data = np.concatenate(self.audio_data_sd, axis=0)
                    sf.write(filepath, audio_data, self.sample_rate)
                    
                elif AUDIO_LIB == "pyaudio" and self.audio_data:
                    # 使用wave保存
                    with wave.open(filepath, 'wb') as wf:
                        wf.setnchannels(self.channels)
                        wf.setsampwidth(self.audio.get_sample_size(self.format))
                        wf.setframerate(self.sample_rate)
                        wf.writeframes(b''.join(self.audio_data))
                
                self.recording_status.config(text=f"💾 已保存：{filepath}", foreground="green")
            else:
                # 模拟保存
                self.recording_status.config(text=f"💾 已保存（模拟）：{filepath}", foreground="green")
                
        except Exception as e:
            messagebox.showerror("错误", f"保存音频文件失败：{str(e)}")
    
    def next_record(self):
        """切换到下一条记录"""
        self.current_index += 1
        self.save_progress()  # 自动保存进度
        self.show_current_record()

    def prev_record(self):
        """切换到上一条记录"""
        if self.current_index > 0:
            self.current_index -= 1
            self.save_progress()  # 自动保存进度
            self.show_current_record()
        else:
            messagebox.showinfo("提示", "已经是第一条记录了！")
    
    def play_audio(self):
        """试听当前录制的音频"""
        if not self.current_audio_file or not os.path.exists(self.current_audio_file):
            messagebox.showwarning("警告", "没有找到音频文件！")
            return
        
        try:
            if AUDIO_AVAILABLE and AUDIO_LIB == "sounddevice":
                # 使用sounddevice播放
                threading.Thread(target=self._play_with_sounddevice, daemon=True).start()
            else:
                # 使用系统默认播放器
                threading.Thread(target=self._play_with_system, daemon=True).start()
        except Exception as e:
            messagebox.showerror("错误", f"播放音频失败：{str(e)}")
    
    def _play_with_sounddevice(self):
        """使用sounddevice播放音频"""
        try:
            # 更新状态
            self.root.after(0, lambda: self.recording_status.config(text=self.lang['status_playing'], foreground="orange"))
            self.root.after(0, lambda: self.play_button.config(text=self.lang['button_playing'], state=tk.DISABLED))
            
            # 读取并播放音频
            data, samplerate = sf.read(self.current_audio_file)
            sd.play(data, samplerate)
            sd.wait()  # 等待播放完成
            
            # 恢复状态
            self.root.after(0, lambda: self.recording_status.config(text=self.lang['status_play_completed'], foreground="blue"))
            self.root.after(0, lambda: self.play_button.config(text=self.lang['playback_button'], state=tk.NORMAL))
            
        except Exception as e:
            if self.current_language == 'zh_CN':
                self.root.after(0, lambda: messagebox.showerror("错误", f"播放失败：{str(e)}"))
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Playback failed: {str(e)}"))
            self.root.after(0, lambda: self.play_button.config(text=self.lang['playback_button'], state=tk.NORMAL))
    
    def _play_with_system(self):
        """使用系统默认播放器播放音频"""
        try:
            # 更新状态
            self.root.after(0, lambda: self.recording_status.config(text=self.lang['status_playing'], foreground="orange"))
            self.root.after(0, lambda: self.play_button.config(text=self.lang['button_playing'], state=tk.DISABLED))
            
            # 使用系统默认程序打开音频文件
            if os.name == 'nt':  # Windows
                os.startfile(self.current_audio_file)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.call(('open' if sys.platform == 'darwin' else 'xdg-open', self.current_audio_file))
            
            # 短暂延迟后恢复按钮状态
            time.sleep(1)
            if self.current_language == 'zh_CN':
                self.root.after(0, lambda: self.recording_status.config(text="🔊 播放器已启动", foreground="blue"))
            else:
                self.root.after(0, lambda: self.recording_status.config(text="🔊 Player started", foreground="blue"))
            self.root.after(0, lambda: self.play_button.config(text=self.lang['playback_button'], state=tk.NORMAL))
            
        except Exception as e:
            if self.current_language == 'zh_CN':
                self.root.after(0, lambda: messagebox.showerror("错误", f"播放失败：{str(e)}"))
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Playback failed: {str(e)}"))
            self.root.after(0, lambda: self.play_button.config(text=self.lang['playback_button'], state=tk.NORMAL))
    
    def finish_recording(self):
        """结束录制"""
        if self.is_recording:
            self.stop_recording()
        
        result = messagebox.askyesno("确认", "确定要结束录制吗？\n\n当前进度将被保存。")
        if result:
            self.save_progress()
            self.cleanup()
            self.root.quit()
    
    def cleanup(self):
        """清理资源"""
        if self.is_recording:
            self.is_recording = False
        
        if AUDIO_AVAILABLE:
            if hasattr(self, 'stream') and self.stream:
                try:
                    if AUDIO_LIB == "sounddevice":
                        self.stream.stop()
                        self.stream.close()
                    elif AUDIO_LIB == "pyaudio":
                        self.stream.stop_stream()
                        self.stream.close()
                except:
                    pass
            
            if AUDIO_LIB == "pyaudio" and hasattr(self, 'audio'):
                try:
                    self.audio.terminate()
                except:
                    pass
    
    def on_closing(self):
        """窗口关闭时的处理"""
        if self.is_recording:
            result = messagebox.askyesno("确认", "录制正在进行中，确定要退出吗？")
            if not result:
                return
        
        self.save_progress()  # 保存进度
        self.cleanup()
        self.root.destroy()


def main():
    """主函数"""
    # 先检测语言配置
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        current_language = config.get('ui_settings', {}).get('language', 'zh_CN')
    except:
        current_language = 'zh_CN'
    
    # 根据语言显示启动信息
    if current_language == 'zh_CN':
        print("🎤 语音录制程序 v2.1 启动成功！")
        print(f"📁 工作目录：{os.getcwd()}")
        print(f"🎵 音频库：{AUDIO_LIB if AUDIO_AVAILABLE else '模拟模式'}")
    else:
        print("🎤 Audio Recorder v2.1 started successfully!")
        print(f"📁 Working directory: {os.getcwd()}")
        print(f"🎵 Audio library: {AUDIO_LIB if AUDIO_AVAILABLE else 'Simulation mode'}")
    
    # 创建主窗口
    root = tk.Tk()
    
    # 设置窗口图标（如果有的话）
    try:
        root.iconbitmap('icon.ico')
    except:
        pass
    
    # 创建录制程序实例
    app = AudioRecorder(root)
    
    # 设置窗口关闭事件
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # 居中显示窗口
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
    y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
    root.geometry(f"+{x}+{y}")
    
    # 启动GUI主循环
    root.mainloop()


if __name__ == "__main__":
    main()
