@echo off
REM AI DEBUG系统启动脚本(Windows版)

setlocal enabledelayedexpansion

REM 获取脚本所在目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM 检查Python环境
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo 错误: 未找到Python。请安装Python 3.6以上版本。
    exit /b 1
)

REM 检查虚拟环境
if not exist "venv" (
    echo 创建虚拟环境...
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo 错误: 创建虚拟环境失败。请检查Python venv模块是否可用。
        exit /b 1
    )
)

REM 激活虚拟环境
call venv\Scripts\activate

REM 安装依赖
if not exist ".deps_installed" (
    echo 安装依赖...
    pip install -r requirements.txt
    if %ERRORLEVEL% equ 0 (
        echo. > .deps_installed
    ) else (
        echo 警告: 依赖安装可能不完整。
    )
)

REM 检查环境变量文件
if exist ".env" (
    echo 检测到.env环境变量文件
) else (
    echo 未检测到.env文件
    echo 创建示例.env文件...
    if exist ".env.example" (
        copy .env.example .env
        echo 已创建.env文件，请编辑此文件设置您的API密钥
    ) else (
        echo 创建默认.env文件...
        echo # OpenAI API配置 > .env
        echo OPENAI_API_KEY=your_api_key_here >> .env
        echo 已创建默认.env文件，请编辑此文件设置您的API密钥
    )
)

REM 检查环境变量
if "%OPENAI_API_KEY%"=="" (
    echo 注意: 未检测到OPENAI_API_KEY环境变量，将从.env文件加载
)

REM 解析命令行参数
set "MODE=api"
set "HOST=0.0.0.0"
set "PORT=5000"
set "DEBUG="

:parse_args
if "%~1"=="" goto :end_parse_args

if "%~1"=="--analyze" (
    set "MODE=analyze"
    shift
    goto :parse_args
)

if "%~1"=="--error" (
    set "ERROR_FILE=%~2"
    shift & shift
    goto :parse_args
)

if "%~1"=="--code" (
    set "CODE_FILE=%~2"
    shift & shift
    goto :parse_args
)

if "%~1"=="--description" (
    set "DESC_FILE=%~2"
    shift & shift
    goto :parse_args
)

if "%~1"=="--log" (
    set "LOG_FILE=%~2"
    shift & shift
    goto :parse_args
)

if "%~1"=="--output" (
    set "OUTPUT_FORMAT=%~2"
    shift & shift
    goto :parse_args
)

if "%~1"=="--output-file" (
    set "OUTPUT_FILE=%~2"
    shift & shift
    goto :parse_args
)

if "%~1"=="--host" (
    set "HOST=%~2"
    shift & shift
    goto :parse_args
)

if "%~1"=="--port" (
    set "PORT=%~2"
    shift & shift
    goto :parse_args
)

if "%~1"=="--debug" (
    set "DEBUG=--debug"
    shift
    goto :parse_args
)

if "%~1"=="--help" (
    echo AI DEBUG系统启动脚本
    echo.
    echo 用法: %0 [选项]
    echo.
    echo 选项:
    echo   --analyze             运行单次分析而不是启动API服务
    echo   --error ^<文件^>        错误信息文件路径
    echo   --code ^<文件^>         代码片段文件路径
    echo   --description ^<文件^>  问题描述文件路径
    echo   --log ^<文件^>          日志信息文件路径
    echo   --output ^<格式^>       输出格式 (markdown/html/json)
    echo   --output-file ^<文件^>  输出文件路径
    echo   --host ^<主机^>         API服务主机地址
    echo   --port ^<端口^>         API服务端口
    echo   --debug               开启调试模式
    echo   --help                显示此帮助信息
    echo.
    echo 示例:
    echo   %0                                     # 启动API服务
    echo   %0 --host localhost --port 8080        # 在localhost:8080启动API服务
    echo   %0 --analyze --error examples/error_messages/python_zero_division.txt --code examples/code_snippets/python_division.py
    exit /b 0
)

echo 未知选项: %1
echo 使用 --help 查看帮助信息
exit /b 1

:end_parse_args

REM 运行程序
if "%MODE%"=="api" (
    echo 启动API服务，监听 %HOST%:%PORT%...
    python main.py api --host "%HOST%" --port "%PORT%" %DEBUG%
) else (
    REM 构建命令行
    set "CMD=python main.py analyze"
    
    if defined ERROR_FILE (
        set "CMD=!CMD! --error "!ERROR_FILE!""
    )
    
    if defined CODE_FILE (
        set "CMD=!CMD! --code "!CODE_FILE!""
    )
    
    if defined DESC_FILE (
        set "CMD=!CMD! --description "!DESC_FILE!""
    )
    
    if defined LOG_FILE (
        set "CMD=!CMD! --log "!LOG_FILE!""
    )
    
    if defined OUTPUT_FORMAT (
        set "CMD=!CMD! --output "!OUTPUT_FORMAT!""
    )
    
    if defined OUTPUT_FILE (
        set "CMD=!CMD! --output-file "!OUTPUT_FILE!""
    )
    
    echo 运行分析...
    !CMD!
)

REM 停用虚拟环境
call deactivate

endlocal
