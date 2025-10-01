import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel, QSlider, 
                            QHBoxLayout, QVBoxLayout, QWidget, QStyle, QSizePolicy, QFileDialog, 
                            QComboBox)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import Qt, QUrl, pyqtSignal, QTime, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QIcon, QColor
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import Qt, QUrl, pyqtSignal, QTime
from PyQt5.QtGui import QIcon, QColor

# 导入pydub用于准确计算音频时长
from pydub import AudioSegment
import logging

class AudioPlayer(QWidget):
    """音频播放器组件"""
    
    # 自定义信号
    playStateChanged = pyqtSignal(bool)  # 播放状态改变信号，True表示正在播放，False表示暂停或停止
    nextTrackRequested = pyqtSignal()  # 请求播放下一个音频的信号
    prevTrackRequested = pyqtSignal()  # 请求播放上一个音频的信号
    trackChanged = pyqtSignal(int)  # 当前播放轨道改变信号
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        # 设置颜色
        if parent and hasattr(parent, 'primary_color'):
            self.primary_color = parent.primary_color
            self.secondary_color = parent.secondary_color
            self.accent_color = parent.accent_color
            self.background_color = parent.background_color
            self.text_color = parent.text_color
            self.border_color = parent.border_color
        else:
            # 默认颜色
            self.primary_color = QColor(41, 128, 185)    # 蓝色
            self.secondary_color = QColor(39, 174, 96)   # 绿色
            self.accent_color = QColor(231, 76, 60)      # 红色
            self.background_color = QColor(248, 249, 250) # 浅灰背景
            self.text_color = QColor(44, 62, 80)         # 深蓝灰文字
            self.border_color = QColor(218, 223, 225)    # 边框颜色
        
        # 创建媒体播放器
        self.mediaPlayer = QMediaPlayer()
        
        # 连接信号
        self.mediaPlayer.positionChanged.connect(self.position_changed)
        self.mediaPlayer.durationChanged.connect(self.duration_changed)
        self.mediaPlayer.stateChanged.connect(self.media_state_changed)
        self.mediaPlayer.volumeChanged.connect(self.volume_changed)
        self.mediaPlayer.mediaStatusChanged.connect(self.media_status_changed)

        # 设置位置更新间隔为50毫秒(0.05秒)
        self.mediaPlayer.setNotifyInterval(50)

        # 初始化音量
        self.mediaPlayer.setVolume(100)  # 默认音量为100

        # 初始化播放速率
        self.playback_rates = [0.5, 0.75, 0.9, 1.0, 1.1, 1.2, 1.25, 1.5, 2.0, 3.0]  # 支持的播放速率
        self.current_rate_index = 3  # 默认1.0倍速

        # 音频片段列表管理
        self.track_list = []  # 存储音频片段文件路径
        self.current_track_index = -1  # 当前播放的轨道索引
        self.accurate_duration = None  # 初始化准确时长属性
        
        # 创建UI
        self.setup_ui()

        # 创建进度条动画对象
        self.position_animation = QPropertyAnimation(self.positionSlider, b'value')
        self.position_animation.setDuration(50)  # 动画持续时间（毫秒）
        self.position_animation.setEasingCurve(QEasingCurve.Linear)

    def setup_ui(self):
        """设置UI"""
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 创建播放控制布局
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(0, 0, 0, 0)
        control_layout.setSpacing(10)

        # 播放/暂停按钮
        self.playButton = QPushButton()
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playButton.setFixedSize(32, 32)  # 缩小按钮尺寸
        self.playButton.clicked.connect(self.play_pause)
        self.playButton.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.primary_color.name()};
                color: white;
                border: none;
                border-radius: 16px;
                padding: 3px;
            }}
            QPushButton:hover {{
                background-color: {QColor(52, 152, 219).name()};
            }}
            QPushButton:pressed {{
                background-color: {QColor(30, 96, 146).name()};
            }}
        """)

        # 停止按钮
        self.stopButton = QPushButton()
        self.stopButton.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stopButton.setFixedSize(32, 32)  # 缩小按钮尺寸
        self.stopButton.clicked.connect(self.stop)
        self.stopButton.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.accent_color.name()};
                color: white;
                border: none;
                border-radius: 16px;
                padding: 3px;
            }}
            QPushButton:hover {{
                background-color: {QColor(231, 76, 60).name()};
            }}
            QPushButton:pressed {{
                background-color: {QColor(192, 57, 43).name()};
            }}
        """)

        # 后退5秒按钮
        self.rewindButton = QPushButton()
        self.rewindButton.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekBackward))
        self.rewindButton.setFixedSize(32, 32)  # 缩小按钮尺寸
        self.rewindButton.clicked.connect(lambda: self.seek_relative(-5000))  # 后退5秒
        self.rewindButton.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.primary_color.name()};
                color: white;
                border: none;
                border-radius: 16px;
                padding: 3px;
            }}
            QPushButton:hover {{
                background-color: {QColor(52, 152, 219).name()};
            }}
            QPushButton:pressed {{
                background-color: {QColor(30, 96, 146).name()};
            }}
        """)

        # 前进5秒按钮
        self.forwardButton = QPushButton()
        self.forwardButton.setIcon(self.style().standardIcon(QStyle.SP_MediaSeekForward))
        self.forwardButton.setFixedSize(32, 32)  # 缩小按钮尺寸
        self.forwardButton.clicked.connect(lambda: self.seek_relative(5000))  # 前进5秒
        self.forwardButton.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.primary_color.name()};
                color: white;
                border: none;
                border-radius: 16px;
                padding: 3px;
            }}
            QPushButton:hover {{
                background-color: {QColor(52, 152, 219).name()};
            }}
            QPushButton:pressed {{
                background-color: {QColor(30, 96, 146).name()};
            }}
        """)

        # 时间标签
        self.timeLabel = QLabel("00:00 / 00:00")
        self.timeLabel.setStyleSheet(f"""
            QLabel {{
                color: {self.text_color.name()};
                font-size: 9pt;
                padding: 3px;
                min-width: 100px;
            }}
        """)

        # 创建上一个/下一个音频按钮
        self.prevButton = QPushButton()
        self.prevButton.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipBackward))
        self.prevButton.setFixedSize(32, 32)  # 缩小按钮尺寸
        self.prevButton.clicked.connect(self.request_prev_track)
        self.prevButton.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.secondary_color.name()};
                color: white;
                border: none;
                border-radius: 16px;
                padding: 3px;
            }}
            QPushButton:hover {{
                background-color: {QColor(46, 204, 113).name()};
            }}
            QPushButton:pressed {{
                background-color: {QColor(39, 174, 96).name()};
            }}
        """)

        self.nextButton = QPushButton()
        self.nextButton.setIcon(self.style().standardIcon(QStyle.SP_MediaSkipForward))
        self.nextButton.setFixedSize(32, 32)  # 缩小按钮尺寸
        self.nextButton.clicked.connect(self.request_next_track)
        self.nextButton.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.secondary_color.name()};
                color: white;
                border: none;
                border-radius: 16px;
                padding: 3px;
            }}
            QPushButton:hover {{
                background-color: {QColor(46, 204, 113).name()};
            }}
            QPushButton:pressed {{
                background-color: {QColor(39, 174, 96).name()};
            }}
        """)

        # 当前播放段落标签
        self.trackLabel = QLabel("未播放")
        self.trackLabel.setStyleSheet(f"""
            QLabel {{
                color: {self.text_color.name()};
                font-size: 9pt;
                padding: 3px;
                min-width: 80px;
            }}
        """)

        # 音量标签和滑块
        self.volumeLabel = QLabel("音量:")
        self.volumeLabel.setStyleSheet(f"""
            QLabel {{
                color: {self.text_color.name()};
                font-size: 9pt;
                padding: 3px;
            }}
        """)

        self.volumeSlider = QSlider(Qt.Horizontal)
        self.volumeSlider.setRange(0, 250)  # 设置音量范围0-250
        self.volumeSlider.setValue(100)  # 默认音量为100
        self.volumeSlider.setToolTip("调整音量")
        self.volumeSlider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: 1px solid {self.border_color.name()};
                height: 8px;
                background: white;
                margin: 2px 0;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {self.primary_color.name()};
                border: 2px solid white;
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }}
            QSlider::handle:horizontal:hover {{
                background-color: {QColor(52, 152, 219).name()};
            }}
        """)
        self.volumeSlider.valueChanged.connect(self.set_volume)

        self.volumeValueLabel = QLabel("100%")
        self.volumeValueLabel.setStyleSheet(f"""
            QLabel {{
                color: {self.text_color.name()};
                font-size: 9pt;
                padding: 3px;
                min-width: 40px;
            }}
        """)

        # 播放速率选择
        self.rateLabel = QLabel("倍速:")
        self.rateLabel.setStyleSheet(f"""
            QLabel {{
                color: {self.text_color.name()};
                font-size: 9pt;
                padding: 3px;
            }}
        """)

        self.rateComboBox = QComboBox()
        for rate in self.playback_rates:
            self.rateComboBox.addItem(f"{rate}x")
        self.rateComboBox.setCurrentIndex(self.current_rate_index)
        self.rateComboBox.setStyleSheet(f"""
            QComboBox {{
                background-color: white;
                border: 1px solid {self.border_color.name()};
                border-radius: 4px;
                padding: 3px;
                font-size: 9pt;
                color: {self.text_color.name()};
            }}
            QComboBox QAbstractItemView {{
                border: 1px solid {self.border_color.name()};
                selection-background-color: {self.primary_color.name()};
                selection-color: white;
            }}
        """)
        self.rateComboBox.currentIndexChanged.connect(self.change_playback_rate)

        # 添加控件到控制布局
        control_layout.addWidget(self.prevButton)
        control_layout.addWidget(self.rewindButton)
        control_layout.addWidget(self.playButton)
        control_layout.addWidget(self.stopButton)
        control_layout.addWidget(self.forwardButton)
        control_layout.addWidget(self.nextButton)
        control_layout.addWidget(self.trackLabel)
        control_layout.addWidget(self.timeLabel)
        control_layout.addStretch(1)  # 添加弹性空间
        control_layout.addWidget(self.volumeLabel)
        control_layout.addWidget(self.volumeSlider)
        control_layout.addWidget(self.volumeValueLabel)
        control_layout.addWidget(self.rateLabel)
        control_layout.addWidget(self.rateComboBox)

        # 创建进度条
        self.positionSlider = QSlider(Qt.Horizontal)
        self.positionSlider.setRange(0, 0)
        self.positionSlider.sliderMoved.connect(self.set_position)
        self.positionSlider.sliderPressed.connect(self.slider_pressed)
        self.positionSlider.sliderReleased.connect(self.slider_released)
        # 添加触屏支持
        self.positionSlider.setMouseTracking(True)
        self.is_dragging = False
        self.positionSlider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                border: 1px solid {self.border_color.name()};
                height: 8px;
                background: white;
                margin: 2px 0;
                border-radius: 4px;
            }}
            QSlider::handle:horizontal {{
                background: {self.primary_color.name()};
                border: 2px solid white;
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }}
            QSlider::handle:horizontal:hover {{
                background-color: {QColor(52, 152, 219).name()};
            }}
        """)

        # 添加布局到主布局
        main_layout.addWidget(self.positionSlider)
        main_layout.addLayout(control_layout)

        # 设置布局
        self.setLayout(main_layout)
    

    
    def get_accurate_duration(self, file_path):
        """使用pydub获取音频文件的准确时长(毫秒)"""
        try:
            audio = AudioSegment.from_file(file_path)
            duration_ms = len(audio)
            logging.info(f"pydub获取的音频时长: {duration_ms}毫秒 ({duration_ms/1000:.2f}秒)")
            return duration_ms
        except Exception as e:
            logging.error(f"pydub获取音频时长失败: {str(e)}")
            return None

    def load_file(self, file_path, track_number=None):
        """加载单个音频文件"""
        if not file_path or not os.path.exists(file_path):
            logging.error(f"文件不存在: {file_path}")
            return False
        
        # 使用pydub获取准确时长
        accurate_duration = self.get_accurate_duration(file_path)
        
        # 创建媒体内容
        url = QUrl.fromLocalFile(file_path)
        content = QMediaContent(url)
        
        # 设置媒体内容
        self.mediaPlayer.setMedia(content)
        
        # 更新UI
        self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        
        # 更新当前播放段落标签
        if track_number is not None:
            self.trackLabel.setText(f"第 {track_number} 段")
        else:
            # 尝试从文件名中提取段号
            file_name = os.path.basename(file_path)
            try:
                # 假设文件名格式为 "segment_X.mp3" 或类似格式
                import re
                match = re.search(r'\d+', file_name)
                if match:
                    self.trackLabel.setText(f"第 {match.group()} 段")
                else:
                    self.trackLabel.setText(file_name)
            except:
                self.trackLabel.setText(file_name)
        
        # 添加日志记录文件路径和基本信息
        logging.info(f"加载音频文件: {file_path}")
        
        # 如果获取到准确时长，使用它更新UI
        if accurate_duration is not None:
            self.accurate_duration = accurate_duration
            # 手动更新时间标签
            current_time = QTime(0, 0)
            current_time = current_time.addMSecs(0)
            total_time = QTime(0, 0)
            total_time = total_time.addMSecs(accurate_duration)
            
            time_format = "mm:ss"
            if accurate_duration > 3600000:  # 如果时长超过1小时，显示小时
                time_format = "hh:mm:ss"
            
            time_text = f"{current_time.toString(time_format)} / {total_time.toString(time_format)}"
            self.timeLabel.setText(time_text)
        
        return True
    
    def set_track_list(self, track_list):
        """设置音频片段列表"""
        self.track_list = track_list
        self.current_track_index = -1
        
    def set_current_track(self, index):
        """设置当前播放的音频片段索引"""
        if 0 <= index < len(self.track_list):
            self.current_track_index = index
            self.load_file(self.track_list[index], index + 1)
            self.trackChanged.emit(index)
            return True
        return False
    
    def get_current_track_index(self):
        """获取当前播放的音频片段索引"""
        return self.current_track_index
    
    def media_status_changed(self, status):
        """媒体状态改变时的处理"""
        # 当媒体加载完成时，确保更新时长
        if status == QMediaPlayer.LoadedMedia:
            self.duration_changed(self.mediaPlayer.duration())
        
        # 当当前媒体播放结束时
        if status == QMediaPlayer.EndOfMedia and len(self.track_list) > 0:
            # 如果不是最后一个轨道，则播放下一个
            if self.current_track_index < len(self.track_list) - 1:
                self.set_current_track(self.current_track_index + 1)
                self.mediaPlayer.play()
    
    def play_pause(self):
        """播放或暂停"""
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()
    
    def stop(self):
        """停止播放"""
        self.mediaPlayer.stop()
    
    def seek_relative(self, msecs):
        """相对跳转"""
        current_position = self.mediaPlayer.position()
        new_position = max(0, current_position + msecs)
        self.mediaPlayer.setPosition(new_position)
    
    def slider_pressed(self):
        """进度条按下时的处理"""
        self.is_dragging = True

    def slider_released(self):
        """进度条释放时的处理"""
        self.is_dragging = False
        # 确保释放时设置一次位置
        self.set_position(self.positionSlider.value())

    def set_position(self, position):
        """设置播放位置"""
        self.mediaPlayer.setPosition(position)
        # 确保设置位置后如果是播放状态则继续播放
        if self.mediaPlayer.state() == QMediaPlayer.PausedState:
            self.mediaPlayer.play()
    
    def position_changed(self, position):
        """播放位置改变时更新UI"""
        # 直接更新进度条位置以确保精确性
        if not self.is_dragging:
            # 使用准确时长来限制进度条位置
            max_position = self.accurate_duration if self.accurate_duration is not None else self.mediaPlayer.duration()
            self.positionSlider.setValue(min(position, max_position))
        
        # 更新时间标签
        actual_duration = self.accurate_duration if self.accurate_duration is not None else self.mediaPlayer.duration()
        
        # 转换为时分秒格式
        current_time = QTime(0, 0)
        current_time = current_time.addMSecs(position)
        total_time = QTime(0, 0)
        total_time = total_time.addMSecs(actual_duration)
        
        time_format = "mm:ss"
        if actual_duration > 3600000:  # 如果时长超过1小时，显示小时
            time_format = "hh:mm:ss"
        
        time_text = f"{current_time.toString(time_format)} / {total_time.toString(time_format)}"
        self.timeLabel.setText(time_text)

    def change_playback_rate(self, index):
        """更改播放速率"""
        if 0 <= index < len(self.playback_rates):
            # 记录当前播放位置和状态
            current_position = self.mediaPlayer.position()
            was_playing = self.mediaPlayer.state() == QMediaPlayer.PlayingState
            
            self.current_rate_index = index
            rate = self.playback_rates[index]
            
            # 先暂停播放再更改速率
            if was_playing:
                self.mediaPlayer.pause()
            
            # 设置新的播放速率
            self.mediaPlayer.setPlaybackRate(rate)
            
            # 根据播放速率调整位置更新间隔
            # 播放速度越快，更新间隔应该越小，以保持进度条的准确性
            base_interval = 50  # 基础间隔50ms
            new_interval = max(10, int(base_interval / rate))  # 最小10ms
            self.mediaPlayer.setNotifyInterval(new_interval)
            
            # 延迟一小段时间后再设置播放位置，确保速率变更生效
            import time
            time.sleep(0.1)  # 延迟100ms
            
            # 重新设置播放位置，确保同步
            self.mediaPlayer.setPosition(current_position)
            
            # 强制更新一次进度条
            self.position_changed(current_position)
            
            # 如果之前是播放状态，恢复播放
            if was_playing:
                self.mediaPlayer.play()
    
    def duration_changed(self, duration):
        """媒体时长改变时更新UI"""
        # 确定使用哪个时长值
        actual_duration = self.accurate_duration if self.accurate_duration is not None else duration
        
        self.positionSlider.setRange(0, actual_duration)
        
        # 添加日志记录时长信息
        import logging
        logging.info(f"QMediaPlayer提供的时长: {duration}毫秒 ({duration/1000:.2f}秒)")
        if self.accurate_duration is not None:
            logging.info(f"使用pydub获取的准确时长: {self.accurate_duration}毫秒 ({self.accurate_duration/1000:.2f}秒)")
        
        # 更新时间标签
        if actual_duration > 0:
            current_time = QTime(0, 0)
            current_time = current_time.addMSecs(0)
            total_time = QTime(0, 0)
            total_time = total_time.addMSecs(actual_duration)
            
            time_format = "mm:ss"
            if actual_duration > 3600000:  # 如果时长超过1小时，显示小时
                time_format = "hh:mm:ss"
            
            time_text = f"{current_time.toString(time_format)} / {total_time.toString(time_format)}"
            self.timeLabel.setText(time_text)
    
    def media_state_changed(self, state):
        """媒体状态改变时更新UI"""
        if state == QMediaPlayer.PlayingState:
            self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
            self.playStateChanged.emit(True)
        else:
            self.playButton.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            self.playStateChanged.emit(False)
            
    def request_next_track(self):
        """请求播放下一个音频"""
        if len(self.track_list) > 0:
            if self.current_track_index < len(self.track_list) - 1:
                self.set_current_track(self.current_track_index + 1)
                self.mediaPlayer.play()
        else:
            self.nextTrackRequested.emit()
        
    def request_prev_track(self):
        """请求播放上一个音频"""
        if len(self.track_list) > 0:
            if self.current_track_index > 0:
                self.set_current_track(self.current_track_index - 1)
                self.mediaPlayer.play()
        else:
            self.prevTrackRequested.emit()

    def set_volume(self, value):
        """设置音量"""
        # 将0-250的滑块值直接设置为音量
        self.mediaPlayer.setVolume(value)
        self.volumeValueLabel.setText(f"{value}%")

    def volume_changed(self, value):
        """音量改变时更新UI"""
        self.volumeSlider.setValue(value)
        self.volumeValueLabel.setText(f"{value}%")

    def change_playback_rate(self, index):
        """更改播放速率"""
        if 0 <= index < len(self.playback_rates):
            self.current_rate_index = index
            rate = self.playback_rates[index]
            self.mediaPlayer.setPlaybackRate(rate)


# 测试代码
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 创建主窗口
    window = QMainWindow()
    window.setWindowTitle("音频播放器测试")
    window.setGeometry(100, 100, 600, 150)
    
    # 创建音频播放器
    player = AudioPlayer()
    window.setCentralWidget(player)
    
    # 添加打开文件按钮
    menubar = window.menuBar()
    file_menu = menubar.addMenu("文件")
    open_action = file_menu.addAction("打开")
    
    def open_file():
        file_path, _ = QFileDialog.getOpenFileName(
            window, "打开音频文件", "", "音频文件 (*.mp3 *.wav *.ogg *.flac);;所有文件 (*.*)"
        )
        if file_path:
            player.load_file(file_path)
    
    open_action.triggered.connect(open_file)
    
    window.show()
    sys.exit(app.exec_())