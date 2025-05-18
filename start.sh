#!/bin/bash

# AI DEBUG系统启动脚本

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "错误: 未找到Python。请安装Python 3.6以上版本。"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python -m venv venv
    if [ $? -ne 0 ]; then
        echo "错误: 创建虚拟环境失败。请检查Python venv模块是否可用。"
        exit 1
    fi
fi

# 激活虚拟环境
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # Linux/Mac
    source venv/bin/activate
fi

# 安装依赖
if [ ! -f ".deps_installed" ]; then
    echo "安装依赖..."
    pip install -r requirements.txt
    if [ $? -eq 0 ]; then
        touch .deps_installed
    else
        echo "警告: 依赖安装可能不完整。"
    fi
fi

# 解析命令行参数
MODE="api"
HOST="0.0.0.0"
PORT="5000"
DEBUG="false"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --analyze)
            MODE="analyze"
            shift
            ;;
        --error)
            ERROR_FILE="$2"
            shift 2
            ;;
        --code)
            CODE_FILE="$2"
            shift 2
            ;;
        --description)
            DESC_FILE="$2"
            shift 2
            ;;
        --log)
            LOG_FILE="$2"
            shift 2
            ;;
        --output)
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        --output-file)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --debug)
            DEBUG="true"
            shift
            ;;
        --help)
            echo "AI DEBUG系统启动脚本"
            echo ""
            echo "用法: $0 [选项]"
            echo ""
            echo "选项:"
            echo "  --analyze             运行单次分析而不是启动API服务"
            echo "  --error <文件>        错误信息文件路径"
            echo "  --code <文件>         代码片段文件路径"
            echo "  --description <文件>  问题描述文件路径"
            echo "  --log <文件>          日志信息文件路径"
            echo "  --output <格式>       输出格式 (markdown/html/json)"
            echo "  --output-file <文件>  输出文件路径"
            echo "  --host <主机>         API服务主机地址"
            echo "  --port <端口>         API服务端口"
            echo "  --debug               开启调试模式"
            echo "  --help                显示此帮助信息"
            echo ""
            echo "示例:"
            echo "  $0                                  # 启动API服务"
            echo "  $0 --host localhost --port 8080     # 在localhost:8080启动API服务"
            echo "  $0 --analyze --error examples/error_messages/python_zero_division.txt --code examples/code_snippets/python_division.py"
            exit 0
            ;;
        *)
            echo "未知选项: $1"
            echo "使用 --help 查看帮助信息"
            exit 1
            ;;
    esac
done

# 运行程序
if [ "$MODE" = "api" ]; then
    echo "启动API服务，监听 $HOST:$PORT..."
    if [ "$DEBUG" = "true" ]; then
        python main.py api --host "$HOST" --port "$PORT" --debug
    else
        python main.py api --host "$HOST" --port "$PORT"
    fi
else
    # 构建命令行
    CMD="python main.py analyze"
    
    if [ -n "$ERROR_FILE" ]; then
        CMD="$CMD --error \"$ERROR_FILE\""
    fi
    
    if [ -n "$CODE_FILE" ]; then
        CMD="$CMD --code \"$CODE_FILE\""
    fi
    
    if [ -n "$DESC_FILE" ]; then
        CMD="$CMD --description \"$DESC_FILE\""
    fi
    
    if [ -n "$LOG_FILE" ]; then
        CMD="$CMD --log \"$LOG_FILE\""
    fi
    
    if [ -n "$OUTPUT_FORMAT" ]; then
        CMD="$CMD --output \"$OUTPUT_FORMAT\""
    fi
    
    if [ -n "$OUTPUT_FILE" ]; then
        CMD="$CMD --output-file \"$OUTPUT_FILE\""
    fi
    
    echo "运行分析..."
    eval $CMD
fi

# 停用虚拟环境
deactivate
