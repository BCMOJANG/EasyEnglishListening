@echo off
:: 刷新环境变量的简单脚本

:: 通知用户
echo 正在刷新环境变量...

:: 使用PowerShell刷新环境变量
powershell -Command "$env:Path = [System.Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [System.Environment]::GetEnvironmentVariable('Path','User'); Write-Host '环境变量已刷新！'"

:: 返回到调用脚本
exit /b 0