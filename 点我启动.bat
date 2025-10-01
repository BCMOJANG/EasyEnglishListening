@echo off
chcp 65001 >nul
echo 正在启动Trae音频处理程序...

:: 尝试使用py启动器（Python标准安装方式）
py -3 start_pyqt_app.py 2>nul
if %errorlevel% equ 0 goto :eof

:: 尝试使用python命令
python start_pyqt_app.py 2>nul
if %errorlevel% equ 0 goto :eof

:: 尝试使用python3命令
python3 start_pyqt_app.py 2>nul
if %errorlevel% equ 0 goto :eof

:: 如果以上都失败，检查常见的Python安装路径
if exist "C:\Python39\python.exe" (
    "C:\Python39\python.exe" start_pyqt_app.py
    goto :eof
)

if exist "C:\Python310\python.exe" (
    "C:\Python310\python.exe" start_pyqt_app.py
    goto :eof
)

if exist "C:\Python311\python.exe" (
    "C:\Python311\python.exe" start_pyqt_app.py
    goto :eof
)

if exist "C:\Program Files\Python39\python.exe" (
    "C:\Program Files\Python39\python.exe" start_pyqt_app.py
    goto :eof
)

if exist "C:\Program Files\Python310\python.exe" (
    "C:\Program Files\Python310\python.exe" start_pyqt_app.py
    goto :eof
)

if exist "C:\Program Files\Python311\python.exe" (
    "C:\Program Files\Python311\python.exe" start_pyqt_app.py
    goto :eof
)

:: 如果所有尝试都失败，询问用户是否要自动安装Python
echo.
echo 错误：无法找到Python。请确保已安装Python 3.9或更高版本。
echo.
set /p INSTALL_PYTHON=是否要自动下载并安装Python 3.11？(Y/N): 

if /i "%INSTALL_PYTHON%"=="Y" (
    echo.
    echo 正在下载Python 3.11安装程序...
    echo 这可能需要几分钟时间，请耐心等待...
    echo.
    
    :: 创建临时目录
    mkdir "%TEMP%\TrAE_Python_Install" 2>nul
    
    :: 使用PowerShell下载Python安装程序
    powershell -Command "$ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.4/python-3.11.4-amd64.exe' -OutFile '%TEMP%\TrAE_Python_Install\python-3.11.4-amd64.exe'"
    
    if not exist "%TEMP%\TrAE_Python_Install\python-3.11.4-amd64.exe" (
        echo 下载Python安装程序失败。请手动下载并安装Python。
        echo 您可以从 https://www.python.org/downloads/ 下载Python。
        pause
        goto :eof
    )
    
    echo 正在安装Python 3.11...
    echo 这可能需要几分钟时间，请耐心等待...
    echo.
    
    :: 静默安装Python，添加到PATH
    "%TEMP%\TrAE_Python_Install\python-3.11.4-amd64.exe" /quiet InstallAllUsers=1 PrependPath=1
    
    echo Python安装完成！正在清理临时文件...
    rmdir /s /q "%TEMP%\TrAE_Python_Install" 2>nul
    
    echo.
    echo 正在重新启动应用程序...
    echo.
    
    :: 刷新环境变量
    call RefreshEnv.cmd 2>nul
    
    :: 重新尝试启动应用
    python start_pyqt_app.py
    if %errorlevel% equ 0 goto :eof
    
    echo.
    echo 安装完成，但需要重启计算机以完成设置。
    echo 请重启计算机后再次运行此程序。
    pause
    goto :eof
) else (
    echo.
    echo 您选择不安装Python。
    echo 您可以从 https://www.python.org/downloads/ 手动下载并安装Python。
    echo 安装时请确保勾选"Add Python to PATH"选项。
    echo.
    pause
)