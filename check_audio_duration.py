import os
import logging
from pydub import AudioSegment

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_audio_duration(file_path):
    """检查音频文件的实际时长"""
    if not os.path.exists(file_path):
        logging.error(f"文件不存在: {file_path}")
        return None
    
    try:
        # 使用pydub加载音频文件
        audio = AudioSegment.from_mp3(file_path)
        duration_ms = len(audio)
        duration_sec = duration_ms / 1000
        logging.info(f"文件 {os.path.basename(file_path)} 的实际时长: {duration_ms}毫秒 ({duration_sec:.2f}秒)")
        return duration_ms
    except Exception as e:
        logging.error(f"检查文件时长时出错: {str(e)}")
        return None

if __name__ == "__main__":
    # 示例用法
    import sys
    if len(sys.argv) > 1:
        check_audio_duration(sys.argv[1])
    else:
        logging.info("请提供音频文件路径作为参数")