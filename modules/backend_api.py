# -*- coding: utf-8 -*-
"""
后端API模块
提供简化的REST接口，适配Vue3前端
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import logging
from typing import Dict, Any, Optional

try:
    from .intent_recognition import IntentRecognizer
    from .knowledge_graph import KnowledgeGraphQuery
    from .config_manager import get_config_manager
    from .deepseek_llm import DeepSeekLLM
except ImportError:
    # 如果模块不存在，使用简单的模拟实现
    IntentRecognizer = None
    KnowledgeGraphQuery = None
    get_config_manager = None
    DeepSeekLLM = None

class APIHandler:
    """简化的API处理器
    
    负责处理用户请求，提供基本的聊天功能
    """
    
    def __init__(self, intent_recognizer=None, kg_query=None, llm_client=None):
        """
        初始化API处理器
        
        Args:
            intent_recognizer: 意图识别器实例（可选）
            kg_query: 知识图谱查询器实例（可选）
            llm_client: LLM客户端实例（可选）
        """
        self.api_url = "http://localhost:5000"
        self.intent_recognizer = intent_recognizer
        self.kg_query = kg_query
        self.llm_client = llm_client
        
        logging.info("API处理器初始化完成")
    

        
    def set_api_url(self, url: str):
        """
        设置API地址
        
        Args:
            url: API地址
        """
        self.api_url = url.strip()
        logging.info(f"API地址已设置为: {self.api_url}")

    def process_query(self, user_input: str) -> Dict[str, Any]:
        """
        处理用户查询
        
        Args:
            user_input: 用户输入
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        if not user_input or not user_input.strip():
            return {"success": False, "message": "输入不能为空"}
        
        user_input = user_input.strip()
        
        # 使用可用的组件处理查询
        nlu_result = {}
        knowledge_data = None
        
        if self.intent_recognizer:
            nlu_result = self.intent_recognizer.understand(user_input)
        
        if self.kg_query and nlu_result.get('intent') != 'unknown':
            knowledge_data = self.kg_query.query(
                user_input, 
                intent=nlu_result.get('intent'),
                entities=nlu_result.get('entities', [])
            )
        
        # 生成回复
        response_text = self._generate_response(nlu_result, knowledge_data, user_input)
        return {"success": True, "message": response_text}
    
    def _generate_response(self, nlu_result: Dict[str, Any], 
                          knowledge_data: Any, user_input: str) -> str:
        """
        生成回复
        
        Args:
            nlu_result: 意图识别结果
            knowledge_data: 知识图谱数据
            user_input: 用户输入
            
        Returns:
            str: 生成的回复
        """
        # 使用大模型生成回复
        if self.llm_client:
            response = self.llm_client.generate_response(user_input)
            if response and response.strip():
                return response.strip()
        
        # 使用模板回复
        return self._generate_template_response(nlu_result, knowledge_data, user_input)
    
    def _generate_template_response(self, nlu_result: Dict[str, Any], 
                                   knowledge_data: Any, user_input: str) -> str:
        """
        生成简单的模板回复
        
        Args:
            nlu_result: 意图识别结果
            knowledge_data: 知识图谱数据
            user_input: 用户输入
            
        Returns:
            str: 模板回复
        """
        intent = nlu_result.get('intent', 'unknown')
        
        # 简化的回复逻辑
        if intent == 'greeting':
            return "您好！有什么可以帮助您的吗？"
        elif intent == 'help':
            return "我可以帮您查询信息和回答问题。"
        elif knowledge_data:
            return "我找到了相关信息。"
        else:
            return f"收到您的消息：{user_input}"
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取系统状态
        
        Returns:
            Dict[str, Any]: 系统状态信息
        """
        return {
            "api_url": self.api_url,
            "intent_recognizer": self.intent_recognizer is not None,
            "knowledge_graph": self.kg_query is not None,
            "llm_client": self.llm_client is not None
        }

def create_flask_app(api_handler=None) -> Flask:
    """
    创建Flask应用
    
    Args:
        api_handler: API处理器实例（可选）
    
    Returns:
        配置好的Flask应用
    """
    app = Flask(__name__)
    
    # 配置Flask应用
    app.config['JSON_AS_ASCII'] = False  # 支持中文JSON
    
    # 配置CORS - 允许所有来源
    CORS(app, resources={
        r"/*": {
            "origins": ["*"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"]
        }
    })
    
    # 使用传入的API处理器或创建新的
    if api_handler is None:
        api_handler = APIHandler()
    
    # 简单的错误处理
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "接口不存在"}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "服务器内部错误"}), 500
    
    # 主要的聊天接口 - 兼容前端的 /test 路由
    @app.route("/test", methods=["POST"])
    def chat():
        """聊天接口 - 兼容前端"""
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"message": "缺少message参数"})
        
        message = data['message'].strip()
        if not message:
            return jsonify({"message": "消息不能为空"})
        
        # 处理查询
        result = api_handler.process_query(message)
        # result = {"message": "测试回复"}
        
        # 返回前端期望的格式
        return jsonify({"message": result["message"]})
    
    # API地址设置接口 - 兼容前端的 /set_api 路由
    @app.route("/set_api", methods=["POST"])
    def set_api():
        """设置API地址接口 - 兼容前端"""
        data = request.get_json()
        if not data or 'apiUrl' not in data:
            return "缺少apiUrl参数", 400
        
        api_url = data['apiUrl'].strip()
        if not api_url:
            return "API地址不能为空", 400
        
        # 设置API地址
        api_handler.set_api_url(api_url)
        return "API地址设置成功"
    
    # 健康检查接口
    @app.route("/health", methods=["GET"])
    def health_check():
        """健康检查接口"""
        status = api_handler.get_status()
        return jsonify({
            "status": "healthy",
            "system_status": status
        })
    
    @app.route("/reply", methods=["GET"])
    def reply():
        return "测试"
    return app


# 创建应用实例的便捷函数
def create_app():
    """创建Flask应用实例"""
    return create_flask_app()


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 创建并运行应用
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)