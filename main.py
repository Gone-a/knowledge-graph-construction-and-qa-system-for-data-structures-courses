#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识图谱问答系统 - 主程序

集成意图识别、知识图谱查询和后端API功能的统一入口
支持性能优化和模块化架构
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.config_manager import get_config_manager
from modules.intent_recognition import IntentRecognizer
from modules.knowledge_graph_query import KnowledgeGraphQuery
from modules.run_serve import RunServe
from modules.backend_api import APIHandler, create_flask_app
from modules.doubao_llm import DoubaoLLM

# 导入知识库
try:
    from intent_recognition.knowledge_base import KNOWLEDGE_BASE
except ImportError:
    KNOWLEDGE_BASE = {"entities": {}, "relations": {}}

class KnowledgeGraphApp:
    """知识图谱应用主类"""
    
    def __init__(self):
        self.config = get_config_manager()
        self.intent_recognizer = None
        self.kg_query = None
        self.api_handler = None
        self.app = None
    
    def initialize(self):
        """初始化应用程序"""
        #初始化服务开启器
        self.run_serve = RunServe()
        with self.run_serve.run('neo4j'):
            pass
        with self.run_serve.run('Vue'):
            pass
        
        

        # 初始化意图识别器
        model_path = self.config.get('model.nlu_model_path')
        self.intent_recognizer = IntentRecognizer(model_path, KNOWLEDGE_BASE)
        
        # 初始化知识图谱查询器
        db_config = self.config.get_database_config()
        self.kg_query = KnowledgeGraphQuery(
            db_config['uri'],
            db_config['user_name'], 
            db_config['password']
        )
        
        # 初始化LLM客户端
        try:
            api_config = self.config.get_api_config()
            llm_config = self.config.get_llm_config()
            llm_client = DoubaoLLM(
                user_api_key=api_config.get('ark_api_key'),
                user_model_id=api_config.get('doubao_model_id')
            )
            llm_client.set_parameters(
                max_tokens=llm_config['max_tokens'],
                temperature=llm_config['temperature']
            )
        except ValueError as e:
            print(f"警告：LLM初始化失败 - {e}")
            print("将使用默认的空LLM客户端")
            llm_client = None
        
        # 初始化API处理器
        self.api_handler = APIHandler(self.intent_recognizer, self.kg_query, llm_client)
        
        # 测试API
        #result=self.api_handler.process_query("你好")
        #print(result)

        # 创建Flask应用
        self.app = create_flask_app(self.api_handler)
    

    
    def run(self):
        """运行应用程序"""
        server_config = self.config.get_server_config()
        host = server_config.get('host', 'localhost')
        port = server_config.get('port', 5000)
        debug = server_config.get('debug', False)
        
        self.app.run(host=host, port=port, debug=debug)
    
def main():
    """主函数"""
    print("知识图谱问答系统启动中...")
    
    app = KnowledgeGraphApp()
    app.initialize()
    app.run()

if __name__ == "__main__":
    main()