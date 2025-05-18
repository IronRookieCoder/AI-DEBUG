"""AI DEBUG系统主入口模块"""

import argparse
import logging
import os
import sys

# 将项目根目录添加到Python路径
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, root_dir)

# 加载环境变量文件
try:
    from dotenv import load_dotenv
    # 优先加载项目根目录下的.env文件
    env_path = os.path.join(root_dir, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        print(f"已加载环境变量文件: {env_path}")
except ImportError:
    print("警告: python-dotenv未安装，无法从.env文件加载环境变量")

from src.config import get_config
from src.api_service import run_api_service
from src.utils import get_env


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="AI DEBUG系统")
    
    # 添加子命令
    subparsers = parser.add_subparsers(dest="command", help="命令")
    
    # API服务子命令
    api_parser = subparsers.add_parser("api", help="启动API服务")
    api_parser.add_argument("--host", type=str, help="API服务主机地址")
    api_parser.add_argument("--port", type=int, help="API服务端口")
    api_parser.add_argument("--debug", action="store_true", help="开启调试模式")
    
    # 单次分析子命令
    analyze_parser = subparsers.add_parser("analyze", help="进行单次分析")
    analyze_parser.add_argument("--error", type=str, help="错误信息文件路径")
    analyze_parser.add_argument("--code", type=str, help="代码片段文件路径")
    analyze_parser.add_argument("--description", type=str, help="问题描述文件路径")
    analyze_parser.add_argument("--log", type=str, help="日志信息文件路径")
    analyze_parser.add_argument("--output", type=str, choices=["markdown", "html", "json"], 
                               default="markdown", help="输出格式")
    analyze_parser.add_argument("--output-file", type=str, help="输出文件路径，默认输出到控制台")
    
    return parser.parse_args()


def run_analysis(args):
    """运行单次分析"""
    from src.input_layer import process_combined_input
    from src.llm_engine import analyze
    from src.output_layer import format_result
    
    # 收集输入数据
    input_data = {}
    
    # 读取错误信息
    if args.error:
        try:
            with open(args.error, "r", encoding="utf-8") as f:
                input_data["error_message"] = f.read()
        except Exception as e:
            print(f"读取错误信息文件失败: {e}")
            return
    
    # 读取代码片段
    if args.code:
        try:
            with open(args.code, "r", encoding="utf-8") as f:
                input_data["code_snippet"] = f.read()
        except Exception as e:
            print(f"读取代码片段文件失败: {e}")
            return
    
    # 读取问题描述
    if args.description:
        try:
            with open(args.description, "r", encoding="utf-8") as f:
                input_data["problem_description"] = f.read()
        except Exception as e:
            print(f"读取问题描述文件失败: {e}")
            return
    
    # 读取日志信息
    if args.log:
        try:
            with open(args.log, "r", encoding="utf-8") as f:
                input_data["log_info"] = f.read()
        except Exception as e:
            print(f"读取日志信息文件失败: {e}")
            return
    
    # 验证是否有输入
    if not input_data:
        print("错误: 请至少提供一种输入数据")
        return
    
    # 处理输入
    processed_input = process_combined_input(input_data)
    
    # 分析
    analysis_result = analyze(processed_input)
    
    # 格式化输出
    formatted_result = format_result(analysis_result, args.output)
    
    # 输出结果
    if args.output_file:
        try:
            with open(args.output_file, "w", encoding="utf-8") as f:
                f.write(formatted_result)
            print(f"分析结果已保存到 {args.output_file}")
        except Exception as e:
            print(f"保存输出文件失败: {e}")
            print(formatted_result)
    else:
        print(formatted_result)


def main():
    """主函数"""
    args = parse_args()
    
    # 打印环境变量状态
    api_key = get_env('OPENAI_API_KEY')
    if api_key:
        masked_key = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:] if len(api_key) > 8 else '****'
        print(f"已检测到OPENAI_API_KEY环境变量 ({masked_key})")
    else:
        print("警告: 未检测到OPENAI_API_KEY环境变量，请确保在配置文件或.env文件中设置")
    
    if args.command == "api":
        # 启动API服务
        run_api_service(args.host, args.port, args.debug)
    elif args.command == "analyze":
        # 运行单次分析
        run_analysis(args)
    else:
        # 默认显示帮助信息
        print("请指定命令，使用 --help 查看帮助")


if __name__ == "__main__":
    main()
