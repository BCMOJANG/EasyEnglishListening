@echo off
chcp 65001 >nul
setlocal

set APP_NAME=EasyEnglishListening
set ENTRY=audio_segmenter_pyqt.py

echo [1/5] 检查 Python...
where py >nul 2>nul
if %errorlevel% equ 0 (
    set PY_CMD=py -3
) else (
    where python >nul 2>nul
    if %errorlevel% neq 0 (
        echo 未检测到 Python，请先安装 Python 3.8+。
        pause
        exit /b 1
    )
    set PY_CMD=python
)

echo [2/5] 安装/更新打包依赖（PyInstaller）...
%PY_CMD% -m pip install --upgrade pyinstaller
if %errorlevel% neq 0 (
    echo PyInstaller 安装失败，请检查网络后重试。
    pause
    exit /b 1
)

echo [3/5] 清理旧的构建目录...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo [4/5] 开始打包整个项目为单文件 EXE...
%PY_CMD% -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --name %APP_NAME% ^
  --collect-submodules pydub ^
  --collect-submodules PyQt5 ^
  --add-data "config.json;." ^
  --add-data "README.md;." ^
  --add-data "LICENSE;." ^
  %ENTRY%

if %errorlevel% neq 0 (
    echo 打包失败。
    pause
    exit /b 1
)

echo [5/5] 打包完成！
echo 可执行文件：dist\%APP_NAME%.exe
echo.
echo 注意：程序运行仍依赖 FFmpeg，请确保 ffmpeg.exe 已加入系统 PATH。
pause
endlocal
