"""输出层模块，负责处理和展示分析结果"""

import json
from typing import Dict, Any, List, Optional


class ResultFormatter:
    """结果格式化器，负责将分析结果格式化为可读形式"""
    
    @staticmethod
    def format_error_analysis(error_analysis: Dict[str, Any]) -> str:
        """
        格式化错误分析结果
        
        Args:
            error_analysis: 错误分析结果
            
        Returns:
            格式化后的文本
        """
        if not error_analysis:
            return "无错误分析结果"
        
        formatted = []
        formatted.append(f"## 错误分析\n")
        
        # 错误类型和描述
        formatted.append(f"### 错误类型\n{error_analysis.get('error_type', '未知错误类型')}\n")
        formatted.append(f"### 错误描述\n{error_analysis.get('description', '无描述')}\n")
        
        # 可能的原因
        formatted.append("### 可能的原因\n")
        causes = error_analysis.get("possible_causes", [])
        if causes:
            for i, cause in enumerate(causes, 1):
                formatted.append(f"{i}. {cause}\n")
        else:
            formatted.append("- 无法确定具体原因\n")
        
        # 解决步骤
        formatted.append("### 解决步骤\n")
        steps = error_analysis.get("solution_steps", [])
        if steps:
            for i, step in enumerate(steps, 1):
                formatted.append(f"{i}. {step}\n")
        else:
            formatted.append("- 无解决步骤\n")
        
        return "\n".join(formatted)
    
    @staticmethod
    def format_code_analysis(code_analysis: Dict[str, Any]) -> str:
        """
        格式化代码分析结果
        
        Args:
            code_analysis: 代码分析结果
            
        Returns:
            格式化后的文本
        """
        if not code_analysis:
            return "无代码分析结果"
        
        formatted = []
        formatted.append(f"## 代码分析\n")
        
        # 代码质量
        formatted.append(f"### 代码质量评估\n{code_analysis.get('code_quality', '未评估')}\n")
        
        # 潜在bugs
        formatted.append("### 潜在问题\n")
        bugs = code_analysis.get("potential_bugs", [])
        if bugs:
            for i, bug in enumerate(bugs, 1):
                formatted.append(f"{i}. {bug}\n")
        else:
            formatted.append("- 未发现明显问题\n")
        
        # 性能问题
        formatted.append("### 性能问题\n")
        perf_issues = code_analysis.get("performance_issues", [])
        if perf_issues:
            for i, issue in enumerate(perf_issues, 1):
                formatted.append(f"{i}. {issue}\n")
        else:
            formatted.append("- 未发现性能问题\n")
        
        # 安全问题
        formatted.append("### 安全问题\n")
        security = code_analysis.get("security_concerns", [])
        if security:
            for i, concern in enumerate(security, 1):
                formatted.append(f"{i}. {concern}\n")
        else:
            formatted.append("- 未发现安全问题\n")
        
        # 改进建议
        formatted.append("### 改进建议\n")
        suggestions = code_analysis.get("improvement_suggestions", [])
        if suggestions:
            for i, suggestion in enumerate(suggestions, 1):
                formatted.append(f"{i}. {suggestion}\n")
        else:
            formatted.append("- 无改进建议\n")
        
        return "\n".join(formatted)
    
    @staticmethod
    def format_root_cause(root_cause: Dict[str, Any]) -> str:
        """
        格式化根因分析结果
        
        Args:
            root_cause: 根因分析结果
            
        Returns:
            格式化后的文本
        """
        if not root_cause:
            return "无根因分析结果"
        
        formatted = []
        formatted.append(f"## 根因分析\n")
        
        # 根本原因
        formatted.append(f"### 根本原因\n{root_cause.get('root_cause', '未能确定')}\n")
        
        # 解释
        formatted.append(f"### 详细解释\n{root_cause.get('explanation', '无解释')}\n")
        
        # 置信度
        confidence = root_cause.get('confidence_level', 0)
        formatted.append(f"### 置信度\n{confidence}/10\n")
        
        # 相关因素
        formatted.append("### 相关因素\n")
        factors = root_cause.get("related_factors", [])
        if factors:
            for i, factor in enumerate(factors, 1):
                formatted.append(f"{i}. {factor}\n")
        else:
            formatted.append("- 无相关因素\n")
        
        return "\n".join(formatted)
    
    @staticmethod
    def format_solution(solution: Dict[str, Any]) -> str:
        """
        格式化解决方案
        
        Args:
            solution: 解决方案
            
        Returns:
            格式化后的文本
        """
        if not solution:
            return "无解决方案"
        
        formatted = []
        formatted.append(f"## 解决方案\n")
        
        # 解决方案摘要
        formatted.append(f"### 摘要\n{solution.get('solution_summary', '无摘要')}\n")
        
        # 修复步骤
        formatted.append("### 修复步骤\n")
        steps = solution.get("fix_steps", [])
        if steps:
            for i, step in enumerate(steps, 1):
                formatted.append(f"{i}. {step}\n")
        else:
            formatted.append("- 无修复步骤\n")
        
        # 代码修改
        formatted.append("### 代码修改\n")
        code_changes = solution.get("code_changes", [])
        if code_changes:
            for i, change in enumerate(code_changes, 1):
                formatted.append(f"#### 修改 {i}\n")
                
                # 原始代码
                original = change.get("original_code", "")
                if original:
                    formatted.append("**原始代码:**\n```\n" + original + "\n```\n")
                
                # 修改后代码
                fixed = change.get("fixed_code", "")
                if fixed:
                    formatted.append("**修改后代码:**\n```\n" + fixed + "\n```\n")
        else:
            formatted.append("- 无代码修改\n")
        
        # 详细解释
        explanation = solution.get("explanation", "")
        if explanation:
            formatted.append(f"### 详细解释\n{explanation}\n")
        
        # 预防措施
        formatted.append("### 预防措施\n")
        tips = solution.get("prevention_tips", [])
        if tips:
            for i, tip in enumerate(tips, 1):
                formatted.append(f"{i}. {tip}\n")
        else:
            formatted.append("- 无预防措施建议\n")
        
        return "\n".join(formatted)
    
    @staticmethod
    def format_similar_bugs(similar_bugs: List[Dict[str, Any]], max_bugs: int = 3) -> str:
        """
        格式化相似bug信息
        
        Args:
            similar_bugs: 相似bug列表
            max_bugs: 最多显示的bug数量
            
        Returns:
            格式化后的文本
        """
        if not similar_bugs:
            return "未找到相似的Bug记录"
        
        formatted = []
        formatted.append(f"## 相似Bug记录\n")
        
        for i, bug in enumerate(similar_bugs[:max_bugs], 1):
            formatted.append(f"### Bug {i}: {bug.get('title', '未知标题')}\n")
            
            # 描述
            desc = bug.get("description", "")
            if desc:
                # 如果描述太长，截断它
                if len(desc) > 300:
                    desc = desc[:297] + "..."
                formatted.append(f"**描述:** {desc}\n")
            
            # 解决方案
            solution = bug.get("solution", "")
            if solution:
                # 如果解决方案太长，截断它
                if len(solution) > 300:
                    solution = solution[:297] + "..."
                formatted.append(f"**解决方案:** {solution}\n")
            
            # 相似度
            similarity = bug.get("similarity", 0)
            formatted.append(f"**相似度:** {similarity:.2f}\n")
            
            # 分隔线
            if i < len(similar_bugs[:max_bugs]):
                formatted.append("---\n")
        
        return "\n".join(formatted)
    
    @staticmethod
    def format_full_result(analysis_result: Dict[str, Any]) -> str:
        """
        格式化完整分析结果
        
        Args:
            analysis_result: 完整分析结果
            
        Returns:
            格式化后的文本
        """
        formatted = []
        formatted.append("# AI DEBUG 分析报告\n")
        
        # 获取各个分析结果
        analyses = analysis_result.get("analyses", {})
        
        # 根因分析（优先显示）
        if "root_cause" in analyses:
            root_cause = analyses["root_cause"].get("root_cause_analysis", {})
            formatted.append(ResultFormatter.format_root_cause(root_cause))
        
        # 解决方案（次优先）
        if "solution" in analyses:
            solution = analyses["solution"].get("solution", {})
            formatted.append(ResultFormatter.format_solution(solution))
        
        # 错误分析
        if "error_analysis" in analyses:
            error_analysis = analyses["error_analysis"].get("error_analysis", {})
            formatted.append(ResultFormatter.format_error_analysis(error_analysis))
        
        # 代码分析
        if "code_analysis" in analyses:
            code_analysis = analyses["code_analysis"].get("code_analysis", {})
            formatted.append(ResultFormatter.format_code_analysis(code_analysis))
        
        # 相似bug
        similar_bugs = analysis_result.get("similar_bugs", [])
        if similar_bugs:
            formatted.append(ResultFormatter.format_similar_bugs(similar_bugs))
        
        return "\n".join(formatted)


class HTMLFormatter:
    """HTML格式化器，负责将分析结果格式化为HTML"""
    
    @staticmethod
    def format_to_html(analysis_result: Dict[str, Any]) -> str:
        """
        将分析结果格式化为HTML
        
        Args:
            analysis_result: 分析结果
            
        Returns:
            HTML格式的结果
        """
        # 获取Markdown格式的结果
        markdown_result = ResultFormatter.format_full_result(analysis_result)
        
        # 转换为HTML (简化版，实际应使用markdown库)
        html_parts = ["<!DOCTYPE html>", "<html>", "<head>", 
                     "<meta charset='utf-8'>",
                     "<title>AI DEBUG 分析报告</title>",
                     "<style>",
                     "body { font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }",
                     "h1 { color: #2c3e50; border-bottom: 2px solid #3498db; }",
                     "h2 { color: #2980b9; margin-top: 30px; }",
                     "h3 { color: #3498db; }",
                     "pre { background-color: #f8f8f8; padding: 10px; border-radius: 5px; overflow-x: auto; }",
                     "code { font-family: Consolas, monospace; }",
                     ".solution { background-color: #e8f8f5; padding: 15px; border-left: 5px solid #2ecc71; margin: 20px 0; }",
                     ".error { background-color: #fdedec; padding: 15px; border-left: 5px solid #e74c3c; margin: 20px 0; }",
                     ".root-cause { background-color: #f5eef8; padding: 15px; border-left: 5px solid #9b59b6; margin: 20px 0; }",
                     "</style>",
                     "</head>",
                     "<body>"]
        
        # 简单的Markdown转HTML转换
        # 实际应用中应使用专业的Markdown到HTML转换库
        content = markdown_result
        # 替换标题
        for i in range(6, 0, -1):
            hashes = '#' * i
            content = content.replace(f"\n{hashes} ", f"\n<h{i}>") \
                           .replace(f"{hashes} ", f"<h{i}>")
            content = content.replace(f"\n<h{i}>", f"\n<h{i}>")
            content = content.replace("\n", "<br>\n")
            
            # 闭合标签
            h_open_tags = content.count(f"<h{i}>")
            h_close_tags = content.count(f"</h{i}>")
            for _ in range(h_open_tags - h_close_tags):
                content = content.replace(f"<h{i}>" + ".*?(<h|\Z)", f"<h{i}>" + r"\1" + f"</h{i}>", 1)
        
        # 替换代码块
        content = content.replace("```\n", "<pre><code>").replace("\n```", "</code></pre>")
        
        # 替换粗体
        content = content.replace("**", "<strong>").replace("**", "</strong>")
        
        # 添加特殊样式
        if "## 解决方案" in markdown_result:
            content = content.replace("<h2>解决方案</h2>", "<div class='solution'><h2>解决方案</h2>")
            # 找到下一个h2的位置来闭合div
            next_h2 = content.find("<h2>", content.find("<h2>解决方案</h2>") + 1)
            if next_h2 > 0:
                content = content[:next_h2] + "</div>" + content[next_h2:]
            else:
                content += "</div>"
        
        if "## 错误分析" in markdown_result:
            content = content.replace("<h2>错误分析</h2>", "<div class='error'><h2>错误分析</h2>")
            # 找到下一个h2的位置来闭合div
            next_h2 = content.find("<h2>", content.find("<h2>错误分析</h2>") + 1)
            if next_h2 > 0:
                content = content[:next_h2] + "</div>" + content[next_h2:]
            else:
                content += "</div>"
        
        if "## 根因分析" in markdown_result:
            content = content.replace("<h2>根因分析</h2>", "<div class='root-cause'><h2>根因分析</h2>")
            # 找到下一个h2的位置来闭合div
            next_h2 = content.find("<h2>", content.find("<h2>根因分析</h2>") + 1)
            if next_h2 > 0:
                content = content[:next_h2] + "</div>" + content[next_h2:]
            else:
                content += "</div>"
        
        html_parts.append(content)
        html_parts.extend(["</body>", "</html>"])
        
        return "\n".join(html_parts)


class JSONFormatter:
    """JSON格式化器，负责格式化为JSON格式"""
    
    @staticmethod
    def format_to_json(analysis_result: Dict[str, Any]) -> str:
        """
        将分析结果格式化为JSON字符串
        
        Args:
            analysis_result: 分析结果
            
        Returns:
            JSON格式的字符串
        """
        try:
            return json.dumps(analysis_result, ensure_ascii=False, indent=2)
        except Exception as e:
            return json.dumps({"error": f"JSON格式化失败: {str(e)}"}, ensure_ascii=False)


class InteractiveComponents:
    """交互组件，生成交互式UI元素"""
    
    @staticmethod
    def generate_feedback_html() -> str:
        """
        生成反馈HTML组件
        
        Returns:
            HTML反馈组件
        """
        return """
        <div class="feedback-container">
            <h3>请评价此分析结果</h3>
            <div class="rating">
                <button onclick="sendFeedback(1)">👎 不满意</button>
                <button onclick="sendFeedback(2)">😐 一般</button>
                <button onclick="sendFeedback(3)">👍 满意</button>
                <button onclick="sendFeedback(4)">🌟 非常满意</button>
            </div>
            <div class="feedback-form">
                <textarea id="feedback-text" placeholder="请提供更详细的反馈意见（可选）"></textarea>
                <button onclick="sendDetailedFeedback()">提交反馈</button>
            </div>
            <script>
                function sendFeedback(rating) {
                    // 发送评分反馈的代码
                    alert('感谢您的评价！');
                }
                
                function sendDetailedFeedback() {
                    const feedback = document.getElementById('feedback-text').value;
                    // 发送详细反馈的代码
                    alert('感谢您的详细反馈！');
                    document.getElementById('feedback-text').value = '';
                }
            </script>
            <style>
                .feedback-container {
                    margin-top: 30px;
                    padding: 15px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                }
                .rating {
                    display: flex;
                    justify-content: space-around;
                    margin: 15px 0;
                }
                .rating button {
                    padding: 8px 15px;
                    border: none;
                    border-radius: 5px;
                    background-color: #f0f0f0;
                    cursor: pointer;
                }
                .rating button:hover {
                    background-color: #e0e0e0;
                }
                .feedback-form {
                    display: flex;
                    flex-direction: column;
                }
                .feedback-form textarea {
                    height: 100px;
                    margin-bottom: 10px;
                    padding: 8px;
                }
                .feedback-form button {
                    align-self: flex-end;
                    padding: 8px 15px;
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                }
            </style>
        </div>
        """
    
    @staticmethod
    def generate_follow_up_html() -> str:
        """
        生成后续问题HTML组件
        
        Returns:
            HTML后续问题组件
        """
        return """
        <div class="follow-up-container">
            <h3>后续问题</h3>
            <div class="follow-up-questions">
                <button onclick="askFollowUp('请详细解释解决方案中的第一步')">请详细解释解决方案中的第一步</button>
                <button onclick="askFollowUp('这个错误还可能有哪些其他原因？')">这个错误还可能有哪些其他原因？</button>
                <button onclick="askFollowUp('如何预防此类问题再次发生？')">如何预防此类问题再次发生？</button>
                <button onclick="askFollowUp('有没有相关的教程或文档资源？')">有没有相关的教程或文档资源？</button>
            </div>
            <div class="custom-question">
                <input type="text" id="custom-question" placeholder="输入自定义问题">
                <button onclick="askCustomQuestion()">提问</button>
            </div>
            <script>
                function askFollowUp(question) {
                    // 发送后续问题的代码
                    alert('提问: ' + question);
                }
                
                function askCustomQuestion() {
                    const question = document.getElementById('custom-question').value;
                    if (question.trim() !== '') {
                        askFollowUp(question);
                        document.getElementById('custom-question').value = '';
                    }
                }
            </script>
            <style>
                .follow-up-container {
                    margin-top: 30px;
                    padding: 15px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                }
                .follow-up-questions {
                    display: flex;
                    flex-direction: column;
                    gap: 10px;
                    margin: 15px 0;
                }
                .follow-up-questions button {
                    text-align: left;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    background-color: #f8f8f8;
                    cursor: pointer;
                }
                .follow-up-questions button:hover {
                    background-color: #e8e8e8;
                }
                .custom-question {
                    display: flex;
                    margin-top: 15px;
                }
                .custom-question input {
                    flex-grow: 1;
                    padding: 8px;
                    border: 1px solid #ddd;
                    border-radius: 5px 0 0 5px;
                }
                .custom-question button {
                    padding: 8px 15px;
                    background-color: #3498db;
                    color: white;
                    border: none;
                    border-radius: 0 5px 5px 0;
                    cursor: pointer;
                }
            </style>
        </div>
        """


class OutputManager:
    """输出管理器，负责协调各种输出格式化器"""
    
    def __init__(self):
        """初始化输出管理器"""
        pass
    
    def format_result(self, analysis_result: Dict[str, Any], output_format: str = "markdown") -> str:
        """
        格式化分析结果
        
        Args:
            analysis_result: 分析结果
            output_format: 输出格式，支持"markdown"、"html"、"json"
            
        Returns:
            格式化后的结果字符串
        """
        if output_format == "markdown":
            return ResultFormatter.format_full_result(analysis_result)
        elif output_format == "html":
            html_result = HTMLFormatter.format_to_html(analysis_result)
            
            # 添加交互组件
            interactive_html = InteractiveComponents.generate_feedback_html() + \
                             InteractiveComponents.generate_follow_up_html()
            
            # 在</body>前插入交互组件
            return html_result.replace("</body>", interactive_html + "</body>")
        elif output_format == "json":
            return JSONFormatter.format_to_json(analysis_result)
        else:
            return f"不支持的输出格式: {output_format}"


# 创建全局输出管理器实例
output_manager = OutputManager()


def format_result(analysis_result: Dict[str, Any], output_format: str = "markdown") -> str:
    """
    格式化结果的便捷函数
    
    Args:
        analysis_result: 分析结果
        output_format: 输出格式
        
    Returns:
        格式化后的结果
    """
    return output_manager.format_result(analysis_result, output_format)
