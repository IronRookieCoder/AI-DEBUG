"""API服务模块，负责提供HTTP API接口"""

from flask import Flask, request, jsonify, render_template, Response
import json
import logging
import os
from typing import Dict, Any, Optional

from ..config import get_config
from ..input_layer import process_combined_input
from ..llm_engine import analyze
from ..output_layer import format_result


# 配置日志
logging_config = get_config("logging")
log_level = getattr(logging, logging_config.get("level", "INFO"))
log_format = logging_config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
log_file = logging_config.get("file", "logs/debug_system.log")

# 确保日志目录存在
os.makedirs(os.path.dirname(log_file), exist_ok=True)

logging.basicConfig(
    level=log_level,
    format=log_format,
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("api_service")


class AIDebugAPI:
    """AI DEBUG系统API服务类"""
    
    def __init__(self):
        """初始化API服务"""
        self.app = Flask(__name__)
        self.config = get_config("api")
        
        # 注册路由
        self.register_routes()
    
    def register_routes(self):
        """注册API路由"""
        
        @self.app.route("/", methods=["GET"])
        def index():
            """首页路由"""
            return render_template("index.html")
        
        @self.app.route("/api/v1/analyze", methods=["POST"])
        def analyze_api():
            """分析API路由"""
            try:
                # 获取请求数据
                request_data = request.json
                if not request_data:
                    return jsonify({"error": "请求数据为空"}), 400
                
                # 记录请求
                logger.info(f"收到分析请求: {json.dumps(request_data, ensure_ascii=False)[:200]}...")
                
                # 从请求中提取输入数据
                input_data = self._extract_input_data(request_data)
                if not input_data:
                    return jsonify({"error": "输入数据无效"}), 400
                
                # 处理输入数据
                processed_input = process_combined_input(input_data)
                
                # 进行分析
                analysis_result = analyze(processed_input)
                
                # 获取期望的输出格式
                output_format = request_data.get("output_format", "json")
                
                # 如果客户端请求JSON格式，直接返回结果
                if output_format == "json":
                    return jsonify(analysis_result)
                
                # 否则，格式化结果并返回
                formatted_result = format_result(analysis_result, output_format)
                
                # 根据输出格式设置响应类型
                content_type = "text/plain"
                if output_format == "html":
                    content_type = "text/html"
                elif output_format == "markdown":
                    content_type = "text/markdown"
                
                return Response(formatted_result, mimetype=content_type)
                
            except Exception as e:
                logger.error(f"处理请求时出错: {str(e)}", exc_info=True)
                return jsonify({"error": f"内部服务错误: {str(e)}"}), 500
        
        @self.app.route("/api/v1/health", methods=["GET"])
        def health_check():
            """健康检查路由"""
            return jsonify({"status": "ok", "service": "ai-debug-api"})
        
        @self.app.route("/api/v1/feedback", methods=["POST"])
        def submit_feedback():
            """提交反馈路由"""
            try:
                feedback_data = request.json
                if not feedback_data:
                    return jsonify({"error": "反馈数据为空"}), 400
                
                # 记录反馈
                logger.info(f"收到用户反馈: {json.dumps(feedback_data, ensure_ascii=False)}")
                
                # 实际项目中可以将反馈存储到数据库或其他系统
                
                return jsonify({"status": "success", "message": "感谢您的反馈"})
                
            except Exception as e:
                logger.error(f"处理反馈时出错: {str(e)}", exc_info=True)
                return jsonify({"error": f"处理反馈时出错: {str(e)}"}), 500
    
    def _extract_input_data(self, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        从请求数据中提取输入数据
        
        Args:
            request_data: 请求数据
            
        Returns:
            输入数据字典，提取失败时返回None
        """
        input_data = {}
        
        # 提取各种输入类型的数据
        if "error_message" in request_data:
            input_data["error_message"] = request_data["error_message"]
        
        if "code_snippet" in request_data:
            input_data["code_snippet"] = request_data["code_snippet"]
        
        if "problem_description" in request_data:
            input_data["problem_description"] = request_data["problem_description"]
        
        if "log_info" in request_data:
            input_data["log_info"] = request_data["log_info"]
        
        # 至少需要一种输入
        if not input_data:
            logger.warning("请求中未包含任何有效输入数据")
            return None
        
        return input_data
    
    def run(self, host: str = None, port: int = None, debug: bool = None):
        """
        运行API服务
        
        Args:
            host: 主机地址，默认使用配置
            port: 端口，默认使用配置
            debug: 是否开启调试模式，默认使用配置
        """
        host = host or self.config.get("host", "0.0.0.0")
        port = port or self.config.get("port", 5000)
        debug = debug if debug is not None else self.config.get("debug", False)
        
        logger.info(f"启动AI DEBUG API服务，监听 {host}:{port}，调试模式: {debug}")
        self.app.run(host=host, port=port, debug=debug)


# 创建API服务实例
api_service = AIDebugAPI()


def run_api_service(host: str = None, port: int = None, debug: bool = None):
    """
    运行API服务的便捷函数
    
    Args:
        host: 主机地址
        port: 端口
        debug: 是否开启调试模式
    """
    api_service.run(host, port, debug)
