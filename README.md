# 英语听力MP3对话分段工具使用说明

## 功能介绍
这是一个用于分割英语听力MP3对话的工具，可以根据静音部分自动分割音频文件。

### 新增功能
- **音频播放器**：现在可以直接在应用内播放分割后的音频片段
- **播放控制**：支持播放/暂停、停止、快进5秒、快退5秒等功能
- **进度显示**：显示音频播放进度和时间
- **文件列表**：分割后的音频文件会显示在列表中，点击即可播放

## 安装指南
1. 确保已安装Python 3.8或更高版本
2. 双击 `点我启动.bat` 启动程序，程序会自动检查必要的依赖
3. 如果遇到依赖问题，可以双击 `自动安装依赖并启动.bat` 自动安装所有缺失的依赖
4. 如果仍然遇到问题，可以尝试以下解决方案：

### 常见依赖问题解决方案

#### PyQt5 DLL加载失败
如果遇到PyQt5的DLL加载失败错误，可能是由于缺少Visual C++运行时库：
1. 下载并安装Microsoft Visual C++ Redistributable for Visual Studio 2015-2022
2. 下载链接: https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist?view=msvc-170
3. 安装后重启电脑
4. 尝试重新安装特定版本的PyQt5: `pip install PyQt5==5.15.4`

#### 自动安装依赖
程序提供了自动安装缺失依赖的功能：

1. 使用 `自动安装依赖并启动.bat` 脚本直接启动自动安装模式
2. 或者使用命令行参数启用自动安装：
```
python start_pyqt_app.py --auto-install
```

#### 跳过特定依赖项检查
如果您无法解决某个依赖项问题，可以使用命令行参数跳过该依赖项检查：
```
python start_pyqt_app.py --skip-dependency 依赖项名称
```
例如，跳过PyQt5依赖检查：
```
python start_pyqt_app.py --skip-dependency PyQt5
```
多个依赖项用逗号分隔：
```
python start_pyqt_app.py --skip-dependency PyQt5,pydub
```

也可以同时使用自动安装和跳过依赖检查：
```
python start_pyqt_app.py --auto-install --skip-dependency ffmpeg
```

#### FFmpeg安装
FFmpeg需要手动安装并添加到系统PATH中：
1. 访问 https://ffmpeg.org/download.html 下载适合您系统的版本
2. 解压并将ffmpeg.exe所在目录添加到系统PATH环境变量
3. 重启电脑使更改生效

## 使用方法
1. 启动程序后，点击"打开文件"按钮选择要分割的MP3文件
2. 设置分割参数（最小静音时长和静音阈值）
3. 点击"开始分割"按钮进行分割
4. 分割完成后，音频片段会保存到指定目录

## 注意事项
- 跳过依赖项检查可能导致程序功能不完整或无法正常工作
- 如果程序无法启动，请尝试以管理员身份运行或检查系统环境变量设置