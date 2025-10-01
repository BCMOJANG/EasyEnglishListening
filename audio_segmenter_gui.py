import os
import sys
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading
from pydub import AudioSegment
from pydub.silence import split_on_silence
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AudioSegmenterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("英语听力MP3对话分段工具")
        self.root.geometry("500x500")
        self.root.resizable(True, True)

        # 设置中文字体
        self.style = ttk.Style()
        self.style.configure("TLabel", font=('SimHei', 10))
        self.style.configure("TButton", font=('SimHei', 10))
        self.style.configure("TScale", font=('SimHei', 10))

        # 创建主框架
        self.main_frame = ttk.Frame(root, padding=20)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # 输入文件选择
        self.input_file = tk.StringVar()
        ttk.Label(self.main_frame, text="输入MP3文件:", anchor='w').pack(fill=tk.X, pady=(0, 5))
        input_frame = ttk.Frame(self.main_frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Entry(input_frame, textvariable=self.input_file).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(input_frame, text="浏览", command=self.browse_input_file).pack(side=tk.RIGHT)

        # 输出目录选择
        self.output_dir = tk.StringVar(value="segments")
        ttk.Label(self.main_frame, text="输出目录:", anchor='w').pack(fill=tk.X, pady=(0, 5))
        output_frame = ttk.Frame(self.main_frame)
        output_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Entry(output_frame, textvariable=self.output_dir).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(output_frame, text="浏览", command=self.browse_output_dir).pack(side=tk.RIGHT)

        # 最小静默长度设置
        self.min_silence = tk.IntVar(value=100)
        ttk.Label(self.main_frame, text="最小静默长度 (毫秒):", anchor='w').pack(fill=tk.X, pady=(0, 5))
        silence_frame = ttk.Frame(self.main_frame)
        silence_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Scale(silence_frame, from_=200, to=3000, variable=self.min_silence, orient=tk.HORIZONTAL,
                  command=lambda v: self.min_silence_label.config(text=f"{int(float(v))}ms")).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.min_silence_label = ttk.Label(silence_frame, text=f"{self.min_silence.get()}ms")
        self.min_silence_label.pack(side=tk.RIGHT, width=60)

        # 静默阈值设置
        self.silence_threshold = tk.IntVar(value=-40)
        ttk.Label(self.main_frame, text="静默阈值 (分贝):", anchor='w').pack(fill=tk.X, pady=(0, 5))
        threshold_frame = ttk.Frame(self.main_frame)
        threshold_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Scale(threshold_frame, from_=-60, to=-10, variable=self.silence_threshold, orient=tk.HORIZONTAL,
                  command=lambda v: self.threshold_label.config(text=f"{int(float(v))}dB")).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.threshold_label = ttk.Label(threshold_frame, text=f"{self.silence_threshold.get()}dB")
        self.threshold_label.pack(side=tk.RIGHT, width=60)

        # 进度条
        ttk.Label(self.main_frame, text="处理进度:", anchor='w').pack(fill=tk.X, pady=(0, 5))
        self.progress = ttk.Progressbar(self.main_frame, orient=tk.HORIZONTAL, length=100, mode='determinate')
        self.progress.pack(fill=tk.X, pady=(0, 10))

        # 状态框
        ttk.Label(self.main_frame, text="状态:", anchor='w').pack(fill=tk.X, pady=(0, 5))
        self.status_text = tk.Text(self.main_frame, height=8, wrap=tk.WORD)
        self.status_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        scroll = ttk.Scrollbar(self.status_text, command=self.status_text.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.status_text.config(yscrollcommand=scroll.set)

        # 按钮框
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(button_frame, text="开始处理", command=self.start_processing).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="取消", command=self.cancel_processing).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="退出", command=root.quit).pack(side=tk.RIGHT)

        # 处理线程和标志
        self.processing_thread = None
        self.cancel_flag = False

    def browse_input_file(self):
        filename = filedialog.askopenfilename(
            title="选择MP3文件",
            filetypes=[("MP3文件", "*.mp3"), ("所有文件", "*.*")]
        )
        if filename:
            self.input_file.set(filename)
            # 自动设置输出目录为输入文件所在目录下的segments文件夹
            input_dir = os.path.dirname(filename)
            self.output_dir.set(os.path.join(input_dir, "segments"))

    def browse_output_dir(self):
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.output_dir.set(directory)

    def update_status(self, message):
        """更新状态文本框"""
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        logger.info(message)

    def update_progress(self, value):
        """更新进度条"""
        self.progress['value'] = value
        self.root.update_idletasks()

    def segment_audio(self):
        """音频分段处理函数"""
        input_file = self.input_file.get()
        output_dir = self.output_dir.get()
        min_silence = self.min_silence.get()
        silence_threshold = self.silence_threshold.get()

        # 检查输入文件
        if not os.path.exists(input_file):
            self.root.after(0, lambda: messagebox.showerror("错误", f"文件不存在: {input_file}"))
            self.root.after(0, lambda: self.update_progress(0))
            return

        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        try:
            # 加载音频文件
            self.root.after(0, lambda: self.update_status(f"正在加载音频文件: {input_file}"))
            audio = AudioSegment.from_mp3(input_file)
            audio_length = len(audio)
            self.root.after(0, lambda: self.update_status(f"音频加载完成，长度: {audio_length/1000:.2f}秒"))

            # 分割音频
            self.root.after(0, lambda: self.update_status(f"开始分割音频，最小静默长度: {min_silence}ms，静默阈值: {silence_threshold}dB"))
            self.root.after(0, lambda: self.update_progress(10))

            segments = split_on_silence(
                audio,
                min_silence_len=min_silence,
                silence_thresh=silence_threshold,
                keep_silence=200
            )

            self.root.after(0, lambda: self.update_status(f"音频分割完成，共 {len(segments)} 个片段"))
            self.root.after(0, lambda: self.update_progress(30))

            # 保存分段后的音频
            file_name = os.path.splitext(os.path.basename(input_file))[0]
            output_files = []
            skipped_count = 0

            for i, segment in enumerate(segments):
                if self.cancel_flag:
                    self.root.after(0, lambda: self.update_status("处理已取消"))
                    self.root.after(0, lambda: self.update_progress(0))
                    return

                # 跳过太短的片段
                if len(segment) < 1000:
                    skipped_count += 1
                    continue

                output_file = os.path.join(output_dir, f"{file_name}_segment_{i+1:03d}.mp3")
                segment.export(output_file, format="mp3")
                output_files.append(output_file)

                # 更新进度
                progress = 30 + (i+1) * 70 / len(segments)
                self.root.after(0, lambda p=progress: self.update_progress(p))
                self.root.after(0, lambda i=i+1, f=output_file: self.update_status(f"已保存片段 {i} 到: {f}"))

            self.root.after(0, lambda: self.update_status(f"跳过 {skipped_count} 个太短的片段"))
            self.root.after(0, lambda: self.update_status(f"处理完成，共生成 {len(output_files)} 个音频片段，保存在: {output_dir}"))
            self.root.after(0, lambda: self.update_progress(100))
            self.root.after(0, lambda: messagebox.showinfo("完成", f"处理完成，共生成 {len(output_files)} 个音频片段！"))

        except Exception as e:
            self.root.after(0, lambda: self.update_status(f"处理错误: {str(e)}"))
            self.root.after(0, lambda: self.update_progress(0))
            self.root.after(0, lambda: messagebox.showerror("错误", f"处理时发生错误: {str(e)}"))

    def start_processing(self):
        """开始处理音频"""
        # 检查是否正在处理
        if self.processing_thread and self.processing_thread.is_alive():
            messagebox.showwarning("警告", "正在处理中，请等待完成或取消当前任务。")
            return

        # 重置取消标志和进度条
        self.cancel_flag = False
        self.update_progress(0)
        self.status_text.delete(1.0, tk.END)

        # 启动处理线程
        self.processing_thread = threading.Thread(target=self.segment_audio)
        self.processing_thread.daemon = True
        self.processing_thread.start()

    def cancel_processing(self):
        """取消处理"""
        if self.processing_thread and self.processing_thread.is_alive():
            self.cancel_flag = True
            self.update_status("正在取消处理...")
        else:
            messagebox.showinfo("提示", "当前没有正在进行的处理。")

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioSegmenterGUI(root)
    root.mainloop()

# 使用说明:
# 1. 安装依赖: pip install pydub
# 2. 运行程序: python audio_segmenter_gui.py
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