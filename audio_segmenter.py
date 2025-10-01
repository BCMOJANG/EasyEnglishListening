import os
import argparse
from pydub import AudioSegment
from pydub.silence import split_on_silence
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def segment_audio(file_path, output_dir, min_silence_len=1000, silence_thresh=-40):
    """
    将音频文件按照静默部分分段
    
    参数:
    file_path (str): 输入音频文件路径
    output_dir (str): 输出目录
    min_silence_len (int): 最小静默长度(毫秒)
    silence_thresh (int): 静默阈值(分贝)
    
    返回:
    list: 分段后的音频文件路径列表
    """
    # 检查文件是否存在
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return []
    
    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    
    # 加载音频文件
    logger.info(f"正在加载音频文件: {file_path}")
    try:
        audio = AudioSegment.from_mp3(file_path)
        logger.info(f"音频加载完成，长度: {len(audio)/1000:.2f}秒")
    except Exception as e:
        logger.error(f"加载音频失败: {str(e)}")
        return []
    
    # 分割音频
    logger.info(f"开始分割音频，最小静默长度: {min_silence_len}ms，静默阈值: {silence_thresh}dB")
    segments = split_on_silence(
        audio,
        min_silence_len=min_silence_len,
        silence_thresh=silence_thresh,
        keep_silence=200  # 保留每个片段前后200ms的静默
    )
    
    logger.info(f"音频分割完成，共 {len(segments)} 个片段")
    
    # 保存分段后的音频
    file_name = os.path.splitext(os.path.basename(file_path))[0]
    output_files = []
    
    for i, segment in enumerate(segments):
        # 跳过太短的片段(小于1秒)
        if len(segment) < 1000:
            logger.warning(f"跳过太短的片段 {i+1}，长度: {len(segment)/1000:.2f}秒")
            continue
        
        output_file = os.path.join(output_dir, f"{file_name}_segment_{i+1:03d}.mp3")
        segment.export(output_file, format="mp3")
        output_files.append(output_file)
        logger.info(f"已保存片段 {i+1} 到: {output_file}")
    
    return output_files

def main():
    parser = argparse.ArgumentParser(description='英语听力MP3对话分段工具')
    parser.add_argument('input_file', help='输入MP3文件路径')
    parser.add_argument('-o', '--output_dir', default='segments', help='输出目录，默认为segments')
    parser.add_argument('-m', '--min_silence', type=int, default=1000, help='最小静默长度(毫秒)，默认为1000ms')
    parser.add_argument('-t', '--silence_threshold', type=int, default=-40, help='静默阈值(分贝)，默认为-40dB')
    
    args = parser.parse_args()
    
    logger.info(f"开始处理音频文件: {args.input_file}")
    output_files = segment_audio(
        args.input_file,
        args.output_dir,
        args.min_silence,
        args.silence_threshold
    )
    
    if output_files:
        logger.info(f"处理完成，共生成 {len(output_files)} 个音频片段，保存在: {args.output_dir}")
    else:
        logger.error("处理失败，未生成任何音频片段")

if __name__ == '__main__':
    main()

# 使用说明:
# 1. 安装依赖: pip install pydub
# 2. 运行程序: python audio_segmenter.py input.mp3 -o output_directory
# 3. 可选参数:
#    -m 最小静默长度(毫秒)，默认为1000ms
#    -t 静默阈值(分贝)，默认为-40dB
# 示例:
# python audio_segmenter.py english_listening.mp3 -o segments -m 800 -t -35