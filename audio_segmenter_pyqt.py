import sys
import os
import logging
import threading
from pydub import AudioSegment
from pydub.silence import split_on_silence
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, QLineEdit, 
                            QFileDialog, QSlider, QProgressBar, QTextEdit, QVBoxLayout, 
                            QHBoxLayout, QWidget, QMessageBox, QFrame, QGroupBox, QStyleFactory, 
                            QDialog, QMenu, QAction, QMenuBar, QSizePolicy, QListWidget, QListWidgetItem)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QIntValidator, QColor, QPalette, QFont

# 导入音频播放器组件
from audio_player import AudioPlayer

# 设置应用程序样式
QApplication.setStyle(QStyleFactory.create('Fusion'))

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SettingsDialog(QDialog):
    """设置对话框类"""
    def __init__(self, main_window=None):
        super().__init__(main_window)
        self.main_window = main_window
        self.setWindowTitle("设置")
        self.setMinimumSize(450, 450)
        self.setModal(True)
        
        # 设置对话框样式
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {self.main_window.background_color.name()};
            }}
            QLabel {{
                color: {self.main_window.text_color.name()};
                font-size: 10pt;
            }}
        """)

        # 从父窗口获取当前设置
        if self.main_window:
            self.output_dir = self.main_window.output_dir
            self.min_silence = self.main_window.min_silence
            self.silence_threshold = self.main_window.silence_threshold
        else:
            self.output_dir = os.path.join(os.path.expanduser("~"), "Downloads", "segments")
            self.min_silence = 1000
            self.silence_threshold = -40

        # 创建布局
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        self.main_layout.setSpacing(5)

        # 创建输出目录设置
        self.create_output_group()

        # 创建分段参数设置
        self.create_params_group()

        # 创建按钮
        self.create_buttons()

    def create_output_group(self):
        """创建输出目录设置组"""
        group = QGroupBox("输出设置")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 10pt;
                color: {self.main_window.text_color.name()};
                border: 1px solid {self.main_window.border_color.name()};
                border-radius: 6px;
                margin-top: 8px;
                padding: 10px;
                background-color: {self.main_window.background_color.name()};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px 0 5px;
            }}
        """)

        layout = QVBoxLayout()

        dir_layout = QHBoxLayout()
        self.output_label = QLabel("输出目录:")
        self.output_label.setFixedWidth(100)
        self.output_lineedit = QLineEdit(self.output_dir)
        self.output_lineedit.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {self.main_window.border_color.name()};
                border-radius: 6px;
                padding: 8px;
                background-color: white;
                color: {self.main_window.text_color.name()};
                font-size: 10pt;
                selection-background-color: {self.main_window.primary_color.name()};
            }}
            QLineEdit:focus {{
                border: 1px solid {self.main_window.primary_color.name()};
            }}
        """)

        self.browse_output_btn = QPushButton("浏览")
        self.browse_output_btn.clicked.connect(self.browse_output_dir)
        self.browse_output_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.main_window.primary_color.name()};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 15px;
                font-size: 10pt;
                font-weight: bold;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {QColor(52, 152, 219).name()};
            }}
            QPushButton:pressed {{
                background-color: {QColor(30, 96, 146).name()};
            }}
        """)

        dir_layout.addWidget(self.output_label)
        dir_layout.addWidget(self.output_lineedit)
        dir_layout.addWidget(self.browse_output_btn)

        layout.addLayout(dir_layout)
        group.setLayout(layout)
        self.main_layout.addWidget(group)

    def create_params_group(self):
        """创建分段参数设置组"""
        group = QGroupBox("分段参数设置")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 11pt;
                color: {self.main_window.text_color.name()};
                border: 1px solid {self.main_window.border_color.name()};
                border-radius: 8px;
                margin-top: 12px;
                padding: 15px;
                background-color: white;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px 0 5px;
            }}
        """)

        layout = QVBoxLayout()

        # 最小静默长度
        silence_layout = QHBoxLayout()
        self.silence_label = QLabel("最小静默长度 (毫秒):")
        self.silence_label.setFixedWidth(140)
        self.silence_slider = QSlider(Qt.Horizontal)
        self.silence_slider.setMinimum(200)
        self.silence_slider.setMaximum(3000)
        self.silence_slider.setValue(self.min_silence)
        self.silence_slider.setTickInterval(200)
        self.silence_slider.setTickPosition(QSlider.TicksBelow)
        self.silence_slider.valueChanged.connect(self.update_silence_value)
        self.silence_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: 1px solid {self.main_window.border_color.name()};
                height: 10px;
                background: white;
                margin: 2px 0;
                border-radius: 5px;
            }}
            QSlider::handle:horizontal {{
                background: {self.main_window.primary_color.name()};
                border: 2px solid white;
                width: 20px;
                height: 20px;
                margin: -6px 0;
                border-radius: 10px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {QColor(52, 152, 219).name()};
            }}
        """)

        self.silence_value_label = QLabel(f"{self.min_silence}ms")
        self.silence_value_label.setFixedWidth(60)
        self.silence_value_label.setAlignment(Qt.AlignRight)

        silence_layout.addWidget(self.silence_label)
        silence_layout.addWidget(self.silence_slider)
        silence_layout.addWidget(self.silence_value_label)

        # 静默阈值
        threshold_layout = QHBoxLayout()
        self.threshold_label = QLabel("静默阈值 (dB):")
        self.threshold_label.setFixedWidth(140)
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setMinimum(-60)
        self.threshold_slider.setMaximum(-10)
        self.threshold_slider.setValue(self.silence_threshold)
        self.threshold_slider.setTickInterval(5)
        self.threshold_slider.setTickPosition(QSlider.TicksBelow)
        self.threshold_slider.valueChanged.connect(self.update_threshold_value)
        self.threshold_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: 1px solid {self.main_window.border_color.name()};
                height: 10px;
                background: white;
                margin: 2px 0;
                border-radius: 5px;
            }}
            QSlider::handle:horizontal {{
                background: {self.main_window.primary_color.name()};
                border: 2px solid white;
                width: 20px;
                height: 20px;
                margin: -6px 0;
                border-radius: 10px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {QColor(52, 152, 219).name()};
            }}
        """)

        self.threshold_value_label = QLabel(f"{self.silence_threshold}dB")
        self.threshold_value_label.setFixedWidth(60)
        self.threshold_value_label.setAlignment(Qt.AlignRight)

        threshold_layout.addWidget(self.threshold_label)
        threshold_layout.addWidget(self.threshold_slider)
        threshold_layout.addWidget(self.threshold_value_label)

        layout.addLayout(silence_layout)
        layout.addLayout(threshold_layout)
        group.setLayout(layout)
        self.main_layout.addWidget(group)

    def update_silence_value(self):
        """更新最小静默长度值"""
        value = self.silence_slider.value()
        self.silence_value_label.setText(f"{value}ms")
        self.min_silence = value

    def update_threshold_value(self):
        """更新静默阈值"""
        value = self.threshold_slider.value()
        self.threshold_value_label.setText(f"{value}dB")
        self.silence_threshold = value

    def browse_output_dir(self):
        """浏览输出目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择输出目录", self.output_dir)
        if dir_path:
            self.output_dir = dir_path
            self.output_lineedit.setText(dir_path)

    def create_buttons(self):
        """创建按钮框"""
        button_layout = QHBoxLayout()
 


        # 按钮通用样式
        button_common_style = f"""
            QPushButton {{
                color: white;
                border-radius: 8px;
                padding: 5px 8px;
                font-weight: bold;
                font-size: 9pt;
                min-height: 20px;
            }}
            QPushButton:focus {{
                outline: none;
            }}
        """

        self.restore_btn = QPushButton("恢复默认设置")
        self.restore_btn.clicked.connect(self.restore_default_settings)
        self.restore_btn.setStyleSheet(button_common_style + f"""
            QPushButton {{
                background-color: {self.main_window.secondary_color.name()};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 9pt;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background-color: #7F8C8D;
            }}
            QPushButton:pressed {{
                background-color: #708090;
            }}
        """)

        self.save_btn = QPushButton("保存设置")
        self.save_btn.clicked.connect(self.save_settings)
        self.save_btn.setStyleSheet(button_common_style + f"""
            QPushButton {{
                background-color: {self.main_window.secondary_color.name()};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 8pt;
                min-width: 70px;
            }}
            QPushButton:hover {{
                background-color: {QColor(39, 174, 96).name()};

            }}
            QPushButton:pressed {{
                background-color: {QColor(33, 150, 83).name()};

            }}
        """)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet(button_common_style + f"""
            QPushButton {{
                background-color: {self.main_window.accent_color.name()};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 8pt;
                min-width: 70px;
            }}
            QPushButton:hover {{
                background-color: {QColor(220, 63, 48).name()};

            }}
            QPushButton:pressed {{
                background-color: {QColor(186, 52, 42).name()};

            }}
        """)

        button_layout.addStretch(1)
        button_layout.addWidget(self.restore_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)

        self.main_layout.addLayout(button_layout)

    def restore_default_settings(self):
        """恢复默认设置"""
        # 询问用户是否确定要恢复默认设置
        reply = QMessageBox.question(self, "确认", "确定要恢复默认设置吗？", 
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # 默认值
            default_output_dir = os.path.join(os.path.expanduser("~"), "Downloads", "segments")
            default_min_silence = 1000
            default_silence_threshold = -40

            # 恢复默认设置
            self.output_dir = default_output_dir
            self.min_silence = default_min_silence
            self.silence_threshold = default_silence_threshold

            # 更新界面
            self.output_lineedit.setText(self.output_dir)
            self.silence_slider.setValue(self.min_silence)
            self.silence_value_label.setText(f"{self.min_silence}ms")
            self.threshold_slider.setValue(self.silence_threshold)
            self.threshold_value_label.setText(f"{self.silence_threshold}dB")

            # 通知主窗口更新设置，但不自动保存
            if self.main_window:
                self.main_window.output_dir = self.output_dir
                self.main_window.min_silence = self.min_silence
                self.main_window.silence_threshold = self.silence_threshold
                logger.info(f"恢复默认设置: output_dir={self.output_dir}, min_silence={self.min_silence}, silence_threshold={self.silence_threshold}")

    def save_settings(self):
        """保存设置"""
        # 获取输出目录
        self.output_dir = self.output_lineedit.text()
        
        # 处理特殊路径语法
        if hasattr(self.parent, 'input_file') and self.parent.input_file and '<文件>' in self.output_dir:
            input_dir = os.path.dirname(self.parent.input_file)
            self.output_dir = self.output_dir.replace('<文件>', input_dir)
            # 更新输入框显示实际路径
            self.output_lineedit.setText(self.output_dir)

        # 确保输出目录存在
        if not os.path.exists(self.output_dir):
            try:
                os.makedirs(self.output_dir)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建输出目录失败: {str(e)}")
                return

        # 保存设置到主窗口
        if self.main_window:
            self.main_window.output_dir = self.output_dir
            self.main_window.min_silence = self.min_silence
            self.main_window.silence_threshold = self.silence_threshold
            self.main_window.output_lineedit.setText(self.output_dir)
            self.main_window.save_config()

        self.accept()

class ProcessingThread(QThread):
    """处理线程类"""
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    processing_finished = pyqtSignal(bool, str, list)  # 添加文件列表参数

    def __init__(self, input_file, output_dir, min_silence, silence_threshold):
        super().__init__()
        self.input_file = input_file
        self.output_dir = output_dir
        self.min_silence = min_silence
        self.silence_threshold = silence_threshold
        self.cancel_flag = False

    def run(self):
        try:
            # 检查输入文件
            if not os.path.exists(self.input_file):
                self.status_updated.emit(f"错误: 文件不存在: {self.input_file}")
                self.processing_finished.emit(False, "文件不存在")
                return

            # 创建输出目录
            os.makedirs(self.output_dir, exist_ok=True)

            # 加载音频文件
            self.status_updated.emit(f"正在加载音频文件: {self.input_file}")
            audio = AudioSegment.from_mp3(self.input_file)
            audio_length = len(audio)
            self.status_updated.emit(f"音频加载完成，长度: {audio_length/1000:.2f}秒")

            # 分割音频
            self.status_updated.emit(f"开始分割音频，最小静默长度: {self.min_silence}ms，静默阈值: {self.silence_threshold}dB")
            self.progress_updated.emit(10)

            # 为split_on_silence添加进度更新和取消检查
            self.status_updated.emit("正在分析音频波形...")
            
            # 分割音频时更新进度的替代方案
            # 先获取总长度
            audio_length = len(audio)
            
            # 创建一个临时的进度更新函数
            def progress_callback(progress):
                # 将0-1的进度映射到10-30%的UI进度
                ui_progress = 10 + int(progress * 20)
                self.progress_updated.emit(ui_progress)
                
                # 检查是否取消
                if self.cancel_flag:
                    raise Exception("处理已取消")
            
            try:
                # 使用带进度的分割函数
                segments = ProcessingThread.split_on_silence_with_progress(
                    audio,
                    min_silence_len=self.min_silence,
                    silence_thresh=self.silence_threshold,
                    keep_silence=200,
                    progress_callback=progress_callback
                )
            except Exception as e:
                if str(e) == "处理已取消":
                    self.status_updated.emit("处理已取消")
                    self.progress_updated.emit(0)
                    self.processing_finished.emit(False, "处理已取消")
                    return
                else:
                    raise e
            
            self.status_updated.emit(f"音频分割完成，共 {len(segments)} 个片段")
            self.progress_updated.emit(30)

            # 保存分段后的音频
            file_name = os.path.splitext(os.path.basename(self.input_file))[0]
            output_files = []
            skipped_count = 0

            for i, segment in enumerate(segments):
                if self.cancel_flag:
                    self.status_updated.emit("处理已取消")
                    self.progress_updated.emit(0)
                    self.processing_finished.emit(False, "处理已取消")
                    return

                # 跳过太短的片段
                if len(segment) < 1000:
                    skipped_count += 1
                    continue

                # 记录片段时长
                segment_duration = len(segment)
                self.status_updated.emit(f"片段 {i+1} 时长: {segment_duration/1000:.2f}秒")

                output_file = os.path.join(self.output_dir, f"{file_name}_segment_{i+1:03d}.mp3")
                segment.export(output_file, format="mp3")
                output_files.append(output_file)

                # 更新进度
                progress = 30 + (i+1) * 70 / len(segments)
                self.progress_updated.emit(int(progress))
                self.status_updated.emit(f"已保存片段 {i+1} 到: {output_file}")

            self.status_updated.emit(f"跳过 {skipped_count} 个太短的片段")
            self.status_updated.emit(f"处理完成，共生成 {len(output_files)} 个音频片段，保存在: {self.output_dir}")
            self.progress_updated.emit(100)
            self.processing_finished.emit(True, "处理完成，共生成 {} 个音频片段！".format(len(output_files)), output_files)

        except Exception as e:
            self.status_updated.emit(f"处理错误: {str(e)}")
            self.progress_updated.emit(0)
            self.processing_finished.emit(False, f"处理时发生错误: {str(e)}", [])
 
    def cancel(self):
        """取消处理"""
        self.cancel_flag = True
        
    @staticmethod
    def split_on_silence_with_progress(audio, min_silence_len, silence_thresh, keep_silence, progress_callback):
        """带进度更新的split_on_silence实现"""
        # 基于pydub的split_on_silence实现，但添加了进度更新
        
        # 转换为dBFS
        silence_thresh = audio.dBFS + silence_thresh
        
        # 找出所有静默部分
        silent_ranges = []
        
        # 音频帧数据
        frame_length = 10
        audio_frame = list(audio[::frame_length])  # 确保转换为列表
        
        # 总帧数
        total_frames = len(audio_frame)
        
        # 当前是否在静默中
        in_silence = False
        silence_start = 0
        
        for i, frame in enumerate(audio_frame):
            # 更新进度
            if i % 100 == 0:  # 每100帧更新一次进度
                progress = i / total_frames
                progress_callback(progress)
                
            # 检查是否在静默中
            if frame.dBFS <= silence_thresh:
                if not in_silence:
                    in_silence = True
                    silence_start = i * frame_length
            else:
                if in_silence:
                    in_silence = False
                    silence_end = i * frame_length
                    
                    # 检查静默长度是否足够
                    if silence_end - silence_start >= min_silence_len:
                        silent_ranges.append((silence_start, silence_end))
        
        # 处理结尾的静默
        if in_silence:
            silence_end = len(audio)
            if silence_end - silence_start >= min_silence_len:
                silent_ranges.append((silence_start, silence_end))
        
        # 根据静默范围分割音频
        segments = []
        last_end = 0
        
        for start, end in silent_ranges:
            # 添加静默前的音频段
            if start - last_end > 0:
                segments.append(audio[last_end:start])
            
            last_end = end
        
        # 添加最后一段
        if last_end < len(audio):
            segments.append(audio[last_end:])
        
        return segments

import json
import os

class AudioSegmenterPyQt(QMainWindow):
    """PyQt版本的音频分段工具"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("英语听力分段工具")
        self.setMinimumSize(650, 500)
        self.setGeometry(100, 100, 700, 550)
        # 移除最大尺寸限制，允许窗口最大化
        # self.setMaximumSize(1200, 800)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)  # 设置大小策略

        # 设置现代化主题颜色
        self.set_theme_colors()

    def set_theme_colors(self):
        self.primary_color = QColor(41, 128, 185)    # 蓝色
        self.secondary_color = QColor(39, 174, 96)   # 绿色
        self.accent_color = QColor(231, 76, 60)      # 红色
        self.background_color = QColor(248, 249, 250) # 浅灰背景
        self.text_color = QColor(44, 62, 80)         # 深蓝灰文字
        self.border_color = QColor(218, 223, 225)    # 边框颜色

        # 配置文件路径
        self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')

        # 初始化输入文件路径
        self.input_file = ""

        # 初始化变量
        self.input_file = ""
        self.output_dir = os.path.join(os.path.expanduser("~"), "Downloads", "segments")
        self.min_silence = 1000
        self.silence_threshold = -40
        self.segment_files = []  # 存储分割后的音频文件列表
        self.current_playing_file = ""  # 当前播放的文件

        # 加载配置（会覆盖上面的默认值）
        self.load_config()
        self.processing_thread = None

        # 创建主布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)
        self.main_layout.setAlignment(Qt.AlignTop)  # 设置顶部对齐
        self.central_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 设置窗口样式
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {self.background_color.name()};
            }}
            QLabel {{
                color: {self.text_color.name()};
                font-size: 10pt;
            }}
            QToolTip {{
                background-color: white;
                color: {self.text_color.name()};
                border: 1px solid {self.border_color.name()};
                border-radius: 4px;
                padding: 5px;
            }}
        """)

        # 创建菜单栏
        self.create_menu_bar()

        # 应用样式
        self.apply_styles()



    def load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # 加载上次输入的文件
                    if 'last_input_file' in config and config['last_input_file']:
                        self.input_file = config['last_input_file']
                        # 在初始化完成后设置输入框的值
                        if hasattr(self, 'input_lineedit'):
                            self.input_lineedit.setText(self.input_file)
                            # 自动设置输出目录（如果没有配置的输出目录）
                            if not hasattr(self, 'output_lineedit') or not self.output_lineedit.text():
                                input_dir = os.path.dirname(self.input_file)
                                self.output_dir = os.path.join(input_dir, "segments")
                                if hasattr(self, 'output_lineedit'):
                                    self.output_lineedit.setText(self.output_dir)
                    # 加载输出目录
                    if 'output_dir' in config and config['output_dir']:
                        self.output_dir = config['output_dir']
                        if hasattr(self, 'output_lineedit'):
                            self.output_lineedit.setText(self.output_dir)
                    # 加载最小静默长度
                    if 'min_silence' in config:
                        self.min_silence = config['min_silence']
                    # 加载静默阈值
                    if 'silence_threshold' in config:
                        self.silence_threshold = config['silence_threshold']
            except Exception as e:
                logger.error(f"加载配置文件失败: {str(e)}")

    def save_config(self):
        """保存配置文件"""
        config = {
            'last_input_file': self.input_file,
            'output_dir': self.output_dir,
            'min_silence': self.min_silence,
            'silence_threshold': self.silence_threshold
        }
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            logger.info(f"配置已保存到 {self.config_file}: {config}")
        except Exception as e:
            logger.error(f"保存配置文件失败: {str(e)}")

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 设置菜单
        settings_menu = menubar.addMenu('设置')

        # 输出设置动作
        output_settings_action = QAction('输出设置', self)
        output_settings_action.triggered.connect(self.open_settings_dialog)
        settings_menu.addAction(output_settings_action)



    def apply_styles(self):
        """应用自定义样式"""
        # 设置窗口背景
        palette = self.palette()
        palette.setColor(QPalette.Window, self.background_color)
        palette.setColor(QPalette.WindowText, self.text_color)
        self.setPalette(palette)

        # 设置字体
        font = QFont()
        font.setFamily("Microsoft YaHei")
        font.setPointSize(10)
        self.setFont(font)

        # 创建输入文件组
        self.create_input_group()

        # 创建输出目录显示
        self.create_output_display()

        # 创建底部设置区域
        self.create_bottom_settings()

    def open_settings_dialog(self):
        """打开设置对话框"""
        dialog = SettingsDialog(self)
        dialog.exec_()

    def create_output_display(self):
        """创建输出目录显示"""
        group = QGroupBox("输出信息")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 11pt;
                color: {self.text_color.name()};
                border: 1px solid {self.border_color.name()};
                border-radius: 8px;
                margin-top: 8px;
                padding: 10px;
                background-color: white;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px 0 5px;
            }}
        """)

        layout = QVBoxLayout()

        dir_layout = QHBoxLayout()
        self.output_label = QLabel("当前输出目录:")
        self.output_label.setFixedWidth(100)
        self.output_lineedit = QLineEdit(self.output_dir)
        self.output_lineedit.setReadOnly(True)
        self.output_lineedit.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {self.border_color.name()};
                border-radius: 6px;
                padding: 8px;
                background-color: #F8F9FA;
                color: {self.text_color.name()};
                font-size: 10pt;
            }}
        """)

        dir_layout.addWidget(self.output_label)
        dir_layout.addWidget(self.output_lineedit)

        layout.addLayout(dir_layout)
        group.setLayout(layout)
        self.main_layout.addWidget(group)

        # 创建进度条
        self.create_progress_bar()

        # 创建状态框
        self.create_status_box()
        
        # 创建音频播放器和文件列表组
        self.create_audio_player_group()

    def create_bottom_settings(self):
        """创建底部设置区域"""
        # 此方法现在为空，设置按钮已移至按钮布局中

        # 创建按钮框
        self.create_buttons()
        
    def create_audio_player_group(self):
        """创建音频播放器和文件列表组"""
        # 创建音频播放器和文件列表的容器
        audio_group = QGroupBox("音频播放器")
        audio_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 11pt;
                color: {self.text_color.name()};
                border: 1px solid {self.border_color.name()};
                border-radius: 8px;
                margin-top: 8px;
                padding: 10px;
                background-color: white;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px 0 5px;
            }}
        """)
        
        # 创建水平布局，左侧是文件列表，右侧是播放器
        audio_layout = QHBoxLayout()
        
        # 创建文件列表
        list_layout = QVBoxLayout()
        list_label = QLabel("分割后的音频文件:")
        list_label.setStyleSheet(f"""
            QLabel {{
                color: {self.text_color.name()};
                font-size: 9pt;
                padding: 2px;
            }}
        """)
        self.file_list = QListWidget()
        self.file_list.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {self.border_color.name()};
                border-radius: 6px;
                padding: 5px;
                background-color: white;
                color: {self.text_color.name()};
                font-size: 9pt;
                selection-background-color: {self.primary_color.name()};
            }}
            QListWidget::item {{
                padding: 4px;
                border-bottom: 1px solid {self.border_color.name()};
            }}
            QListWidget::item:selected {{
                background-color: {self.primary_color.name()};
                color: white;
            }}
        """)
        self.file_list.itemClicked.connect(self.play_selected_file)
        # 添加触屏支持
        self.file_list.setMouseTracking(True)
        
        list_layout.addWidget(list_label)
        list_layout.addWidget(self.file_list)
        
        # 创建音频播放器
        self.audio_player = AudioPlayer(self)
        self.audio_player.setMinimumHeight(100)  # 减小高度
        self.audio_player.setEnabled(False)  # 初始禁用播放器
        
        # 连接音频播放器的信号
        self.audio_player.nextTrackRequested.connect(self.play_next_file)
        self.audio_player.prevTrackRequested.connect(self.play_prev_file)
        
        # 添加到布局
        audio_layout.addLayout(list_layout, 1)  # 列表占1份空间
        audio_layout.addWidget(self.audio_player, 2)  # 播放器占2份空间
        
        audio_group.setLayout(audio_layout)
        self.main_layout.addWidget(audio_group)
        
    def play_selected_file(self, item):
        """播放选中的文件"""
        file_path = item.data(Qt.UserRole)  # 获取存储的文件路径
        if file_path and os.path.exists(file_path):
            self.current_playing_file = file_path
            # 获取当前选中项的索引
            current_index = self.file_list.row(item)
            # 加载文件并传递段落编号
            self.audio_player.load_file(file_path, current_index + 1)  # +1 因为用户习惯从1开始计数
            #self.audio_player.play_pause()  # 自动开始播放
            
    def play_next_file(self):
        """播放下一个文件"""
        # 如果没有文件，直接返回
        if self.file_list.count() == 0:
            return
            
        # 获取当前选中项
        current_item = self.file_list.currentItem()
        if current_item is None:
            # 如果没有选中项，选择第一个
            self.file_list.setCurrentRow(0)
            self.play_selected_file(self.file_list.item(0))
        else:
            # 获取当前索引
            current_index = self.file_list.row(current_item)
            # 计算下一个索引
            next_index = (current_index + 1) % self.file_list.count()
            # 选择并播放下一个
            self.file_list.setCurrentRow(next_index)
            self.play_selected_file(self.file_list.item(next_index))
    
    def play_prev_file(self):
        """播放上一个文件"""
        # 如果没有文件，直接返回
        if self.file_list.count() == 0:
            return
            
        # 获取当前选中项
        current_item = self.file_list.currentItem()
        if current_item is None:
            # 如果没有选中项，选择最后一个
            last_index = self.file_list.count() - 1
            self.file_list.setCurrentRow(last_index)
            self.play_selected_file(self.file_list.item(last_index))
        else:
            # 获取当前索引
            current_index = self.file_list.row(current_item)
            # 计算上一个索引
            prev_index = (current_index - 1) % self.file_list.count()
            # 选择并播放上一个
            self.file_list.setCurrentRow(prev_index)
            self.play_selected_file(self.file_list.item(prev_index))

    def create_input_group(self):
        """创建输入文件选择组"""
        group = QGroupBox("输入设置")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 11pt;
                color: {self.text_color.name()};
                border: 1px solid {self.border_color.name()};
                border-radius: 8px;
                margin-top: 12px;
                padding: 15px;
                background-color: white;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px 0 5px;
            }}
        """)

        layout = QVBoxLayout()

        file_layout = QHBoxLayout()
        self.input_label = QLabel("输入MP3文件:")
        self.input_label.setFixedWidth(100)
        self.input_lineedit = QLineEdit()
        self.input_lineedit.setPlaceholderText("请选择要分割的MP3文件")
        self.input_lineedit.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {self.border_color.name()};
                border-radius: 6px;
                padding: 8px;
                background-color: white;
                color: {self.text_color.name()};
                font-size: 10pt;
                selection-background-color: {self.primary_color.name()};
            }}
            QLineEdit:focus {{
                border: 1px solid {self.primary_color.name()};
            }}
        """)

        self.browse_input_btn = QPushButton("浏览")
        self.browse_input_btn.clicked.connect(self.browse_input_file)
        self.browse_input_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.primary_color.name()};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 15px;
                font-size: 10pt;
                font-weight: bold;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background-color: {QColor(52, 152, 219).name()};
            }}
            QPushButton:pressed {{
                background-color: {QColor(30, 96, 146).name()};

            }}
        """)

        file_layout.addWidget(self.input_label)
        file_layout.addWidget(self.input_lineedit)
        file_layout.addWidget(self.browse_input_btn)

        layout.addLayout(file_layout)
        group.setLayout(layout)
        self.main_layout.addWidget(group)


    def create_params_group(self):
        """创建参数设置组"""
        group = QGroupBox("分段参数设置")
        group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 11pt;
                color: {self.text_color.name()};
                border: 1px solid {self.border_color.name()};
                border-radius: 8px;
                margin-top: 12px;
                padding: 15px;
                background-color: white;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px 0 5px;
            }}
        """)

        layout = QVBoxLayout()

        # 最小静默长度
        silence_layout = QHBoxLayout()
        self.silence_label = QLabel("最小静默长度 (毫秒):")
        self.silence_label.setFixedWidth(140)
        self.silence_slider = QSlider(Qt.Horizontal)
        self.silence_slider.setMinimum(200)
        self.silence_slider.setMaximum(3000)
        self.silence_slider.setValue(1000)
        self.silence_slider.setTickInterval(200)
        self.silence_slider.setTickPosition(QSlider.TicksBelow)
        self.silence_slider.valueChanged.connect(self.update_silence_value)
        self.silence_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: 1px solid {self.border_color.name()};
                height: 10px;
                background: white;
                margin: 2px 0;
                border-radius: 5px;
            }}
            QSlider::handle:horizontal {{
                background: {self.primary_color.name()};
                border: 2px solid white;
                width: 20px;
                height: 20px;
                margin: -6px 0;
                border-radius: 10px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {QColor(52, 152, 219).name()};
            }}
        """)

        self.silence_value_label = QLabel("1000ms")
        self.silence_value_label.setFixedWidth(60)
        self.silence_value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        silence_layout.addWidget(self.silence_label)
        silence_layout.addWidget(self.silence_slider)
        silence_layout.addWidget(self.silence_value_label)

        # 静默阈值
        threshold_layout = QHBoxLayout()
        self.threshold_label = QLabel("静默阈值 (分贝):")
        self.threshold_label.setFixedWidth(140)
        self.threshold_slider = QSlider(Qt.Horizontal)
        self.threshold_slider.setMinimum(-60)
        self.threshold_slider.setMaximum(-10)
        self.threshold_slider.setValue(-40)
        self.threshold_slider.setTickInterval(5)
        self.threshold_slider.setTickPosition(QSlider.TicksBelow)
        self.threshold_slider.valueChanged.connect(self.update_threshold_value)
        self.threshold_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: 1px solid {self.border_color.name()};
                height: 10px;
                background: white;
                margin: 2px 0;
                border-radius: 5px;
            }}
            QSlider::handle:horizontal {{
                background: {self.primary_color.name()};
                border: 2px solid white;
                width: 20px;
                height: 20px;
                margin: -6px 0;
                border-radius: 10px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {QColor(52, 152, 219).name()};
            }}
        """)

        self.threshold_value_label = QLabel("-40dB")
        self.threshold_value_label.setFixedWidth(60)
        self.threshold_value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        threshold_layout.addWidget(self.threshold_label)
        threshold_layout.addWidget(self.threshold_slider)
        threshold_layout.addWidget(self.threshold_value_label)

        layout.addLayout(silence_layout)
        layout.addLayout(threshold_layout)
        group.setLayout(layout)
        self.main_layout.addWidget(group)

    def create_progress_bar(self):
        """创建进度条"""
        progress_layout = QHBoxLayout()
        self.progress_label = QLabel("处理进度:")
        self.progress_label.setFixedWidth(80)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {self.border_color.name()};
                border-radius: 8px;
                background-color: white;
                text-align: center;
                height: 16px;
                margin-top: 5px;
                margin-bottom: 5px;
            }}
            QProgressBar::chunk {{
                background-color: {self.primary_color.name()};
                border-radius: 7px;
            }}
        """)

        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        self.main_layout.addLayout(progress_layout)

    def create_status_box(self):
        """创建状态框"""
        status_group = QGroupBox("处理状态")
        status_group.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 11pt;
                color: {self.text_color.name()};
                border: 1px solid {self.border_color.name()};
                border-radius: 8px;
                margin-top: 12px;
                padding: 15px;
                background-color: white;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px 0 5px;
            }}
        """)

        status_layout = QVBoxLayout()
        self.status_text = QLabel("就绪")
        self.status_text.setStyleSheet(f"""
            QLabel {{
                background-color: white;
                border: 1px solid {self.border_color.name()};
                border-radius: 6px;
                padding: 10px;
                font-size: 10pt;
                color: {self.text_color.name()};
            }}
        """)
        self.status_text.setMinimumHeight(40)
        self.status_text.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.status_text.setWordWrap(False)

        status_layout.addWidget(self.status_text)
        status_group.setLayout(status_layout)
        self.main_layout.addWidget(status_group)

    def create_buttons(self):
        """创建按钮框"""
        button_layout = QHBoxLayout()
 
        # 按钮通用样式
        button_common_style = f"""
            QPushButton {{
                color: white;
                border-radius: 8px;
                padding: 5px 8px;
                font-weight: bold;
                font-size: 9pt;
                min-height: 20px;
            }}
            QPushButton:focus {{
                outline: none;
            }}
        """

        # 开始按钮样式
        self.start_btn = QPushButton("开始处理")
        self.start_btn.clicked.connect(self.start_processing)
        self.start_btn.setStyleSheet(button_common_style + f"""
            QPushButton {{
                background-color: {self.secondary_color.name()};
                min-width: 40px;
                max-width: 48px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {QColor(46, 204, 113).name()};

            }}
            QPushButton:pressed {{
                background-color: {QColor(33, 150, 84).name()};

            }}
        """)

        # 取消按钮样式
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.cancel_processing)
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setStyleSheet(button_common_style + f"""
            QPushButton {{
                background-color: {self.accent_color.name()};
                min-width: 32px;
                max-width: 40px;
                border: none;
            }}
            QPushButton:hover {{
                background-color: {QColor(231, 76, 60).name()};

            }}
            QPushButton:pressed {{
                background-color: {QColor(192, 57, 43).name()};

            }}
            QPushButton:disabled {{
                background-color: #AAAAAA;
                color: #EEEEEE;
            }}
        """)

        # 设置按钮样式
        self.settings_btn = QPushButton("设置")
        self.settings_btn.clicked.connect(self.open_settings_dialog)
        self.settings_btn.setStyleSheet(button_common_style + f"""
            QPushButton {{
                background-color: {self.primary_color.name()};
                min-width: 80px;
                max-width: 100px;
                border: none;

            }}
            QPushButton:hover {{
                background-color: {QColor(52, 152, 219).name()};

            }}
            QPushButton:pressed {{
                background-color: {QColor(30, 96, 146).name()};

            }}
        """)

        # 最大化按钮样式
        self.maximize_btn = QPushButton("最大化")
        self.maximize_btn.clicked.connect(self.showMaximized)
        self.maximize_btn.setStyleSheet(button_common_style + f"""
            QPushButton {{
                background-color: {self.primary_color.name()};
                min-width: 80px;
                max-width: 100px;
                border: none;

            }}
            QPushButton:hover {{
                background-color: {QColor(52, 152, 219).name()};

            }}
            QPushButton:pressed {{
                background-color: {QColor(30, 96, 146).name()};

            }}
        """)

        # 退出按钮样式
        self.exit_btn = QPushButton("退出")
        self.exit_btn.clicked.connect(self.close)
        self.exit_btn.setStyleSheet(button_common_style + f"""
            QPushButton {{
                background-color: #95A5A6;
                min-width: 80px;
                max-width: 100px;
                border: none;

            }}
            QPushButton:hover {{
                background-color: #7F8C8D;

            }}
            QPushButton:pressed {{
                background-color: #708090;

            }}
        """)

        # 创建弹性布局，使按钮在窗口调整大小时能更好地适应
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.settings_btn)
        button_layout.addWidget(self.maximize_btn)
        button_layout.addStretch(1)
        button_layout.addWidget(self.exit_btn)
        button_layout.setSpacing(2)
        button_layout.setContentsMargins(2, 2, 2, 2)

        self.main_layout.addLayout(button_layout)

    def browse_input_file(self):
        """浏览输入文件"""
        # 确定初始目录
        initial_dir = ""
        if hasattr(self, 'input_file') and self.input_file and os.path.exists(self.input_file):
            initial_dir = os.path.dirname(self.input_file)
        elif os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    if 'last_input_file' in config and config['last_input_file'] and os.path.exists(config['last_input_file']):
                        initial_dir = os.path.dirname(config['last_input_file'])
            except Exception as e:
                logger.error(f"读取配置文件失败: {str(e)}")

        filename, _ = QFileDialog.getOpenFileName(
            self, "选择MP3文件", initial_dir, "MP3文件 (*.mp3);;所有文件 (*.*)"
        )
        if filename:
            self.input_lineedit.setText(filename)
            self.input_file = filename
            # 自动设置输出目录
            input_dir = os.path.dirname(filename)
            self.output_lineedit.setText(os.path.join(input_dir, "segments"))
            # 保存配置
            self.save_config()


    def update_silence_value(self):
        """更新最小静默长度值"""
        value = self.silence_slider.value()
        self.silence_value_label.setText(f"{value}ms")
        self.min_silence = value

    def update_threshold_value(self):
        """更新静默阈值"""
        value = self.threshold_slider.value()
        self.threshold_value_label.setText(f"{value}dB")
        self.silence_threshold = value

    def update_status(self, message):
        """更新状态文本，只显示最新一行"""
        self.status_text.setText(message)
        logger.info(message)

    def update_progress(self, value):
        """更新进度条"""
        self.progress_bar.setValue(value)

    def start_processing(self):
        """开始处理"""
        # 检查是否正在处理
        if self.processing_thread and self.processing_thread.isRunning():
            QMessageBox.warning(self, "警告", "正在处理中，请等待完成或取消当前任务。")
            return

        # 获取输入参数
        self.input_file = self.input_lineedit.text().strip()
        self.output_dir = self.output_lineedit.text().strip()

        # 从设置对话框获取参数
        if not hasattr(self, 'settings_dialog') or self.settings_dialog is None:
            self.settings_dialog = SettingsDialog(self)
        self.min_silence = self.settings_dialog.min_silence
        self.silence_threshold = self.settings_dialog.silence_threshold

        # 验证输入
        if not self.input_file:
            QMessageBox.warning(self, "警告", "请选择输入MP3文件。")
            return

        if not self.output_dir:
            QMessageBox.warning(self, "警告", "请指定输出目录。")
            return

        # 重置UI
        self.status_text.clear()
        self.progress_bar.setValue(0)
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.audio_player.setEnabled(False)  # 禁用音频播放器
        self.file_list.clear()  # 清空文件列表

        # 启动处理线程
        self.processing_thread = ProcessingThread(
            self.input_file, self.output_dir, self.min_silence, self.silence_threshold
        )
        self.processing_thread.progress_updated.connect(self.update_progress)
        self.processing_thread.status_updated.connect(self.update_status)
        self.processing_thread.processing_finished.connect(self.processing_completed)
        self.processing_thread.start()

    def cancel_processing(self):
        """取消处理"""
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.cancel()
            self.update_status("正在取消处理...")
        else:
            QMessageBox.information(self, "提示", "当前没有正在进行的处理。")

    def processing_completed(self, success, message, file_list=None):
        """处理完成后的回调"""
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)

        if success:
            # 不显示完成弹窗
            logger.info(f"处理完成: {message}")
            # 更新文件列表
            if file_list and len(file_list) > 0:
                self.update_file_list(file_list)
            else:
                self.update_file_list()
            # 启用音频播放器
            self.audio_player.setEnabled(True)
            
            # 自动选择并播放第一个音频片段
            if self.file_list.count() > 0:
                self.file_list.setCurrentRow(0)
                first_item = self.file_list.item(0)
                file_path = first_item.data(Qt.UserRole)
                self.current_playing_file = file_path
                self.audio_player.load_file(file_path, 1)  # 1表示第一个段落
                #self.audio_player.play_pause()  # 自动播放第一个片段
        else:
            QMessageBox.critical(self, "错误", message)
            
    def update_file_list(self, file_list=None):
        """更新文件列表"""
        self.file_list.clear()
        self.segment_files = []
        
        # 如果提供了文件列表，直接使用
        if file_list and len(file_list) > 0:
            self.segment_files = file_list
        else:
            # 检查输出目录是否存在
            if not os.path.exists(self.output_dir):
                return
                
            # 获取所有MP3文件
            for file in os.listdir(self.output_dir):
                if file.endswith(".mp3"):
                    file_path = os.path.join(self.output_dir, file)
                    self.segment_files.append(file_path)
                
        # 按文件名排序
        self.segment_files.sort()
        
        # 添加到列表
        for i, file_path in enumerate(self.segment_files):
            file_name = os.path.basename(file_path)
            # 在文件名前添加序号
            display_name = f"{i+1}. {file_name}"
            item = QListWidgetItem(display_name)
            item.setData(Qt.UserRole, file_path)  # 存储完整路径
            self.file_list.addItem(item)

if __name__ == "__main__":
    # 检查PyQt5是否安装
    try:
        import PyQt5
    except ImportError:
        print("错误: 未找到PyQt5库。请先安装: pip install PyQt5")
        sys.exit(1)

    # 检查pydub是否安装
    try:
        import pydub
    except ImportError:
        print("错误: 未找到pydub库。请先安装: pip install pydub")
        sys.exit(1)

    app = QApplication(sys.argv)
    window = AudioSegmenterPyQt()
    window.show()
    sys.exit(app.exec_())

# 使用说明:
# 1. 安装依赖: pip install PyQt5 pydub
# 2. 运行程序: python audio_segmenter_pyqt.py
# 3. 功能:
#    - 选择输入的MP3文件
#    - 选择输出目录
#    - 调整最小静默长度和静默阈值
#    - 查看处理进度和状态
#    - 取消正在进行的处理
# 4. 注意事项:
#    - 需要安装FFmpeg并确保其在系统PATH中以处理MP3文件
#    - 处理大文件时可能需要较长时间
#    - 处理过程中不要关闭窗口



    self.settings_dialog = None  # 强制重新创建设置对话框以应用新样式

    def restore_default_settings(self):
        """恢复默认设置"""
        # 询问用户是否确定要恢复默认设置
        reply = QMessageBox.question(self, "确认", "确定要恢复默认设置吗？", 
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # 默认值
            default_output_dir = os.path.join(os.path.expanduser("~"), "Downloads", "segments")
            default_min_silence = 1000
            default_silence_threshold = -40

            # 恢复默认设置
            self.output_dir = default_output_dir
            self.min_silence = default_min_silence
            self.silence_threshold = default_silence_threshold

            # 更新界面
            self.output_lineedit.setText(self.output_dir)
            self.silence_slider.setValue(self.min_silence)
            self.silence_value_label.setText(f"{self.min_silence}ms")
            self.threshold_slider.setValue(self.silence_threshold)
            self.threshold_value_label.setText(f"{self.silence_threshold}dB")

            # 通知父窗口更新设置，但不自动保存
            if self.parent:
                self.parent.output_dir = self.output_dir
                self.parent.min_silence = self.min_silence
                self.parent.silence_threshold = self.silence_threshold
                logger.info(f"恢复默认设置: output_dir={self.output_dir}, min_silence={self.min_silence}, silence_threshold={self.silence_threshold}")

    def save_settings(self):
        """保存设置"""
        # 获取输出目录
        self.output_dir = self.output_lineedit.text()
        
        # 处理特殊路径语法
        if hasattr(self.parent, 'input_file') and self.parent.input_file and '<文件>' in self.output_dir:
            input_dir = os.path.dirname(self.parent.input_file)
            self.output_dir = self.output_dir.replace('<文件>', input_dir)
            # 更新输入框显示实际路径
            self.output_lineedit.setText(self.output_dir)

        # 确保输出目录存在
        if not os.path.exists(self.output_dir):
            try:
                os.makedirs(self.output_dir)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"创建输出目录失败: {str(e)}")
                return

        # 保存设置到父窗口
        if self.parent:
            self.parent.output_dir = self.output_dir
            self.parent.min_silence = self.min_silence
            self.parent.silence_threshold = self.silence_threshold
            self.parent.output_lineedit.setText(self.output_dir)
            self.parent.save_config()

        self.accept()

class ProcessingThread(QThread):
    """处理线程类"""
    progress_updated = pyqtSignal(int)
    status_updated = pyqtSignal(str)
    processing_finished = pyqtSignal(bool, str, list)  # 添加文件列表参数

    def __init__(self, input_file, output_dir, min_silence, silence_threshold):
        super().__init__()
        self.input_file = input_file
        self.output_dir = output_dir
        self.min_silence = min_silence
        self.silence_threshold = silence_threshold
        self.cancel_flag = False

    def run(self):
        try:
            # 检查输入文件
            if not os.path.exists(self.input_file):
                self.status_updated.emit(f"错误: 文件不存在: {self.input_file}")
                self.processing_finished.emit(False, "文件不存在")
                return

            # 创建输出目录
            os.makedirs(self.output_dir, exist_ok=True)

            # 加载音频文件
            self.status_updated.emit(f"正在加载音频文件: {self.input_file}")
            audio = AudioSegment.from_mp3(self.input_file)
            audio_length = len(audio)
            self.status_updated.emit(f"音频加载完成，长度: {audio_length/1000:.2f}秒")

            # 分割音频
            self.status_updated.emit(f"开始分割音频，最小静默长度: {self.min_silence}ms，静默阈值: {self.silence_threshold}dB")
            self.progress_updated.emit(10)

            # 为split_on_silence添加进度更新和取消检查
            self.status_updated.emit("正在分析音频波形...")
            
            # 分割音频时更新进度的替代方案
            # 先获取总长度
            audio_length = len(audio)
            
            # 创建一个临时的进度更新函数
            def progress_callback(progress):
                # 将0-1的进度映射到10-30%的UI进度
                ui_progress = 10 + int(progress * 20)
                self.progress_updated.emit(ui_progress)
                
                # 检查是否取消
                if self.cancel_flag:
                    raise Exception("处理已取消")
            
            try:
                # 使用带进度的分割函数
                segments = ProcessingThread.split_on_silence_with_progress(
                    audio,
                    min_silence_len=self.min_silence,
                    silence_thresh=self.silence_threshold,
                    keep_silence=200,
                    progress_callback=progress_callback
                )
            except Exception as e:
                if str(e) == "处理已取消":
                    self.status_updated.emit("处理已取消")
                    self.progress_updated.emit(0)
                    self.processing_finished.emit(False, "处理已取消")
                    return
                else:
                    raise e
            
            self.status_updated.emit(f"音频分割完成，共 {len(segments)} 个片段")
            self.progress_updated.emit(30)

            # 保存分段后的音频
            file_name = os.path.splitext(os.path.basename(self.input_file))[0]
            output_files = []
            skipped_count = 0

            for i, segment in enumerate(segments):
                if self.cancel_flag:
                    self.status_updated.emit("处理已取消")
                    self.progress_updated.emit(0)
                    self.processing_finished.emit(False, "处理已取消")
                    return

                # 跳过太短的片段
                if len(segment) < 1000:
                    skipped_count += 1
                    continue

                output_file = os.path.join(self.output_dir, f"{file_name}_segment_{i+1:03d}.mp3")
                segment.export(output_file, format="mp3")
                output_files.append(output_file)

                # 更新进度
                progress = 30 + (i+1) * 70 / len(segments)
                self.progress_updated.emit(int(progress))
                self.status_updated.emit(f"已保存片段 {i+1} 到: {output_file}")

            self.status_updated.emit(f"跳过 {skipped_count} 个太短的片段")
            self.status_updated.emit("处理完成，共生成 {} 个音频片段，保存在: {}".format(len(output_files), self.output_dir))
            self.processing_finished.emit(True, "处理完成", output_files)
        except Exception as e:
            self.status_updated.emit(f"处理出错: {str(e)}")
            self.progress_updated.emit(0)
            self.processing_finished.emit(False, f"处理出错: {str(e)}")