@echo off
chcp 65001 >nul
setlocal

echo [1/4] 检查 Python...
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

echo [2/4] 安装/更新打包依赖（PyInstaller）...
%PY_CMD% -m pip install --upgrade pyinstaller
if %errorlevel% neq 0 (
    echo PyInstaller 安装失败，请检查网络后重试。
    pause
    exit /b 1
)

echo [3/4] 开始打包...
%PY_CMD% -m PyInstaller --noconfirm EasyEnglishListening.spec
if %errorlevel% neq 0 (
    echo 打包失败。
    pause
    exit /b 1
)

echo [4/4] 打包完成！
echo 生成目录：dist\EasyEnglishListening\
echo 可执行文件：dist\EasyEnglishListening\EasyEnglishListening.exe

echo.
echo 注意：本程序依赖 FFmpeg，请确保 ffmpeg.exe 已加入系统 PATH。
pause
endlocal
