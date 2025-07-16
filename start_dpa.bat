@echo off
setlocal enabledelayedexpansion

REM DPA Windows启动脚本
echo.
echo 🚀 DPA Windows 启动脚本
echo ====================

REM 切换到项目目录
cd /d "%~dp0"

REM 检查conda
where conda >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Conda未安装或未配置
    pause
    exit /b 1
)

REM 检查node
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js未安装
    pause
    exit /b 1
)

REM 激活conda环境
echo 🐍 激活conda环境...
call conda activate dpa_gen
if %errorlevel% neq 0 (
    echo ❌ 无法激活conda环境dpa_gen
    pause
    exit /b 1
)
echo ✅ Conda环境已激活

REM 检查端口占用
echo 🔍 检查端口占用...
netstat -ano | findstr :8200 >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️ 端口8200已被占用
    echo 请手动停止占用进程或重启计算机
)

netstat -ano | findstr :8230 >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️ 端口8230已被占用
    echo 请手动停止占用进程或重启计算机
)

REM 启动后端服务
echo 🔧 启动后端服务...
if not exist "src\api\main.py" (
    echo ❌ 未找到后端主文件src\api\main.py
    pause
    exit /b 1
)

start "DPA Backend" /min cmd /c "uvicorn src.api.main:app --host 0.0.0.0 --port 8200 --reload > backend.log 2>&1"
echo ✅ 后端服务已启动

REM 等待后端服务启动
echo ⏳ 等待后端服务启动...
timeout /t 5 /nobreak >nul
for /l %%i in (1,1,30) do (
    curl -s http://localhost:8200/api/v1/health >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✅ 后端服务已就绪
        goto backend_ready
    )
    timeout /t 1 /nobreak >nul
    echo|set /p="."
)

echo.
echo ❌ 后端服务启动超时
echo 查看日志: type backend.log
pause
exit /b 1

:backend_ready

REM 启动前端服务
echo 🎨 启动前端服务...
if not exist "frontend\package.json" (
    echo ❌ 未找到前端配置文件frontend\package.json
    pause
    exit /b 1
)

cd frontend

REM 检查依赖
if not exist "node_modules" (
    echo 📦 安装前端依赖...
    call npm install
)

start "DPA Frontend" /min cmd /c "npm run dev > ..\frontend.log 2>&1"
echo ✅ 前端服务已启动

REM 等待前端服务启动
echo ⏳ 等待前端服务启动...
timeout /t 5 /nobreak >nul
for /l %%i in (1,1,60) do (
    curl -s http://localhost:8230 >nul 2>&1
    if !errorlevel! equ 0 (
        echo ✅ 前端服务已就绪
        goto frontend_ready
    )
    timeout /t 1 /nobreak >nul
    echo|set /p="."
)

echo.
echo ❌ 前端服务启动超时
echo 查看日志: type ..\frontend.log
pause
exit /b 1

:frontend_ready

cd ..

REM 验证服务
echo 🔍 验证服务状态...
curl -s http://localhost:8200/api/v1/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 后端服务: 正常
) else (
    echo ❌ 后端服务: 异常
)

curl -s http://localhost:8230 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ 前端服务: 正常
) else (
    echo ❌ 前端服务: 异常
)

REM 创建停止脚本
echo @echo off > stop_dpa.bat
echo echo 🛑 停止DPA服务... >> stop_dpa.bat
echo taskkill /f /im "uvicorn.exe" 2^>nul >> stop_dpa.bat
echo taskkill /f /im "node.exe" 2^>nul >> stop_dpa.bat
echo echo ✅ DPA服务已停止 >> stop_dpa.bat
echo pause >> stop_dpa.bat

echo.
echo 🎉 DPA服务启动成功！
echo ====================
echo.
echo 📊 服务信息:
echo    后端服务: http://localhost:8200
echo    API文档:  http://localhost:8200/docs
echo    前端服务: http://localhost:8230
echo    AAG页面:  http://localhost:8230/aag
echo.
echo 🔍 测试工具:
echo    浏览器测试: start test_browser_simple.html
echo    WebSocket诊断: start websocket_diagnostic.html
echo    Python测试: python test_services.py
echo.
echo 📋 日志文件:
echo    后端日志: type backend.log
echo    前端日志: type frontend.log
echo.
echo 🛑 停止服务:
echo    stop_dpa.bat
echo.
echo 🎯 现在可以开始使用DPA了！
echo 按任意键继续...
pause >nul