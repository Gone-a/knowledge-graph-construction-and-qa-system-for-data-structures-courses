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
            knowledge_data = self.kg_query.query_graph(
                user_input, 
                entities=nlu_result.get('entities', [])
            )
        
        # 生成回复
        response_text = self._generate_response(nlu_result, knowledge_data, user_input)
        return {"success": True, "message": response_text}
    
    def _generate_response(self, nlu_result: Dict[str, Any], knowledge_data: Dict[str, Any], user_input: str) -> str:
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
            # 构建包含上下文信息的提示
            context = f"用户问题：{user_input}\n"
            if nlu_result:
                context += f"意图：{nlu_result.get('intent', '未知')}\n"
                if nlu_result.get('entities'):
                    context += f"实体：{', '.join(nlu_result.get('entities', []))}\n"
            if knowledge_data and knowledge_data.get('answer'):
                context += f"知识图谱信息：{knowledge_data.get('answer')}\n"
            
            response = self.llm_client.generate_response(context)
            if response and response.content and response.content.strip():
                return response.content.strip()
        
        # 如果没有LLM或生成失败，返回默认回复
        if knowledge_data and knowledge_data.get('answer'):
            return knowledge_data.get('answer')
        return "抱歉，我无法理解您的问题。"
    
    
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
    @app.route("/reply", methods=["POST"])
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
        #result = {"message": "测回复"}

        #图的字典
        graph_dict={}
        # 返回前端期望的格式
        return jsonify({"message": result["message"],"graph":graph_dict})
    
    
    @app.route("/set_api", methods=["POST"])
    def set_api():
        """设置API地址接口 - 兼容前端"""
        data = request.get_json()
        print(data)
        conf={
            "key":"api",
            "value":{
                'api_key': data["apiKey"],
                'model_name': data["model"],
                'base_url': data["baseUrl"]
            }
        }
        if conf['value']['api_key'] is not None:

            api_handler.llm_client.ark_api_key=conf['value']['api_key']

        if conf['value']['model_name'] is not None:

            api_handler.llm_client.doubao_model_id=conf['value']['model_name']
        # TODO 设置api

        return "API设置成功"
        
    
    @app.route("/set_database", methods=["POST"])
    def set_database():
        data = request.get_json()
        print(data)
        conf={
            'key':'database',
            'value':{
                'database.user_name':data["username"],
                'database.password':data["password"],
                'database.uri':data["boltUrl"],
                'database.browserUrl':data["browserUrl"]
            }
        }

        # TODO 设置数据库

        return "数据库设置成功"
    
    @app.route("/switchChat", methods=["POST"])
    def switchChat():
        data = request.get_json()
        # print(data)
        # data 是 json 格式 [{sender:,test:,timestamp:}]
        converted = []
        for item in data:
            # 假设sender的值是"user"或"assistant"，如果实际情况不同需要调整这里的映射关系
            converted_item = {
                "role": item["sender"],
                "content": item["text"]
            }
            converted.append(converted_item)
            # TODO 改变模型的上下文
        api_handler.llm_client.history_messages=converted
        return data

    # 健康检查接口
    @app.route("/health", methods=["GET"])
    def health_check():
        """健康检查接口"""
        status = api_handler.get_status()
        return jsonify({
            "status": "healthy",
            "system_status": status
        })
    
    @app.route("/test", methods=["GET"])
    def reply():
        return "测试"
    return app


# 创建应用实例的便捷函数
def create_app():
    """创建Flask应用实例"""
    return create_flask_app()