# -*- coding: utf-8 -*-
"""
DeepSeek大模型API调用模块

提供与DeepSeek API的集成功能，支持智能问答生成
"""

import requests
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

@dataclass
class LLMResponse:
    """大模型响应数据类"""
    content: str
    usage: Dict[str, int]
    model: str
    finish_reason: str
    response_time: float

class DeepSeekLLM:
    """DeepSeek大模型API客户端
    
    负责与DeepSeek API进行通信，生成智能回复
    """
    
    def __init__(self, api_key: str, model_name: str = "deepseek-chat", 
                 base_url: str = "https://api.deepseek.com/v1"):
        """
        初始化DeepSeek客户端
        
        Args:
            api_key: DeepSeek API密钥
            model_name: 模型名称
            base_url: API基础URL
        """
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url.rstrip('/')
        
        # 基本参数配置
        self.max_tokens = 1500
        self.temperature = 0.7
        self.timeout = 30
        
        logging.info(f"DeepSeek LLM客户端初始化完成，模型: {model_name}")
    

    
    def generate_response(self, user_input: str, context: Optional[Dict[str, Any]] = None,
                         system_prompt: Optional[str] = None) -> LLMResponse:
        """
        生成AI回复
        
        Args:
            user_input: 用户输入
            context: 上下文信息（知识图谱查询结果等）
            system_prompt: 系统提示词
            
        Returns:
            LLMResponse: 大模型响应
        """
        try:
            # 构建消息
            messages = self._build_messages(user_input, context, system_prompt)
            
            # 调用API
            response = self._call_api(messages)
            
            # 解析响应
            return self._parse_response(response)
            
        except Exception as e:
            logging.error(f"DeepSeek API调用失败: {e}")
            # 返回错误响应
            return LLMResponse(
                content=f"抱歉，AI服务暂时不可用。错误信息: {str(e)}",
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                model=self.model_name,
                finish_reason="error",
                response_time=0
            )
    
    def _build_messages(self, user_input: str, context: Optional[Dict[str, Any]] = None,
                       system_prompt: Optional[str] = None) -> List[Dict[str, str]]:
        """
        构建对话消息
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            system_prompt: 系统提示词
            
        Returns:
            List[Dict[str, str]]: 消息列表
        """
        messages = []
        
        # 系统提示词
        if not system_prompt:
            system_prompt = self._get_default_system_prompt()
        
        messages.append({
            "role": "system",
            "content": system_prompt
        })
        
        # 构建用户消息（包含上下文）
        user_message = self._build_user_message(user_input, context)
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        return messages
    
    def _get_default_system_prompt(self) -> str:
        """
        获取默认系统提示词
        
        Returns:
            str: 系统提示词
        """

        SYSTEM_PROMPT = """
        # 1. 你的身份 (Your Identity)
    你是一个世界级的数据结构与算法专家，你的名字叫“代码导师”(Code Mentor)。你非常耐心，善于将复杂、抽象的概念用清晰、易于理解的语言解释给初学者听。你的目标是成为用户最信赖的学习伙伴。

    # 2. 你的核心任务 (Your Core Mission)
    你的唯一任务是，严格利用下面`### 背景知识`部分提供的信息，来精准地回答`### 当前用户问题`。你就像一个专业的数据库查询员，只依据给定的事实进行阐述和组织，而不是一个自由发挥的创作者。

    # 3. 行为准则 (Rules of Engagement)

        a. **绝对优先原则 - 严格基于背景知识**: 
        - 你的回答必须，也只能，基于`### 背景知识`部分提供的数据。
        - 如果背景知识足以回答问题，请用自然流畅的语言组织它，并可以适当举例说明。
        - 如果背景知识显示为“无”、“未找到”或包含错误信息，请礼貌的告知用户当前数据库中暂无相关信息，建议用户尝试其他问题。并引导用户提问与数据结构、算法相关的问题。
        - 回答中不得包含任何编造的信息,必须是你很确定的信息

        b. **处理跑题问题**:
        - 当用户的问题明显与数据结构、算法或计算机科学无关时（例如询问天气、新闻、讲笑话），你必须礼貌地拒绝，并温和地将对话引导回主题。
        - 示例回答: “抱歉，我的专业领域是数据结构与算法。关于天气问题我不太了解。不过，我们可以继续讨论一下例如‘图’或者‘排序算法’，您对哪个感兴趣呢？”

        c. **处理模糊问题**:
        - 如果用户的提问很模糊（例如只说“树”），你应该主动提出澄清性问题来帮助用户明确需求。
        - 示例回答: “当然可以聊‘树’！为了更好地帮助您，您是想了解树的基本定义，还是对二叉树、平衡二叉树等具体类型感兴趣，或者是想知道树的遍历算法呢？”

        d. **语气与风格**:
        - 保持专业、严谨、耐心、友好的语气。
        - 避免使用过于随意或口语化的词汇。
        - 多使用鼓励性的语言。

    # 4. 输出格式 (Output Format)
    - 对于定义或概念解释，力求简洁明了。
    - 当需要列举多个项目时（例如多种排序算法），请使用项目符号列表（Markdown的 `-` 或 `*`）。
    - 如果需要展示代码或伪代码，请务必使用Markdown的代码块（```）格式化，以保证清晰可读。
    """
        return SYSTEM_PROMPT
    
    def _build_user_message(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        构建用户消息（包含上下文）
        
        Args:
            user_input: 用户输入
            context: 上下文信息
            
        Returns:
            str: 完整的用户消息
        """
        message_parts = []
        
        # 添加知识图谱上下文
        if context and context.get('knowledge_data'):
            message_parts.append("=== 知识图谱查询结果 ===")
            knowledge_data = context['knowledge_data']
            
            if isinstance(knowledge_data, list) and knowledge_data:
                for i, item in enumerate(knowledge_data[:5], 1):  # 限制显示数量
                    if isinstance(item, dict):
                        # 格式化知识条目
                        formatted_item = self._format_knowledge_item(item)
                        if formatted_item:
                            message_parts.append(f"{i}. {formatted_item}")
            else:
                message_parts.append("未找到相关的知识图谱信息")
            
            message_parts.append("")
        
        # 添加NLU分析结果
        if context and context.get('nlu_result'):
            nlu_result = context['nlu_result']
            message_parts.append("=== 意图分析结果 ===")
            message_parts.append(f"意图: {nlu_result.get('intent', '未知')}")
            
            entities = nlu_result.get('entities', [])
            if entities:
                message_parts.append(f"实体: {', '.join(entities)}")
            
            relations = nlu_result.get('relations', [])
            if relations:
                message_parts.append(f"关系: {', '.join(relations)}")
            
            message_parts.append("")
        
        # 添加用户问题
        message_parts.append("=== 用户问题 ===")
        message_parts.append(user_input)
        message_parts.append("")
        message_parts.append("请基于以上信息回答用户的问题：")
        
        return "\n".join(message_parts)
    
    def _format_knowledge_item(self, item: Dict[str, Any]) -> str:
        """
        格式化知识条目
        
        Args:
            item: 知识条目
            
        Returns:
            str: 格式化后的字符串
        """
        try:
            # 处理实体关系
            if 'entity1' in item and 'entity2' in item:
                entity1 = item.get('entity1', '')
                entity2 = item.get('entity2', '')
                relation = item.get('relation', item.get('relation_name', item.get('relation_type', '')))
                confidence = item.get('confidence', 0)
                
                result = f"{entity1} --[{relation}]--> {entity2}"
                if confidence > 0:
                    result += f" (置信度: {confidence:.2f})"
                
                # 添加路径信息
                if 'relation_path' in item:
                    path_type = item['relation_path']
                    if path_type == 'indirect':
                        result += " [间接关系]"
                    elif path_type == 'direct':
                        result += " [直接关系]"
                
                return result
            
            # 处理其他格式的数据
            elif 'relation' in item:
                return f"关系信息: {item.get('relation', '')}"
            
            # 通用格式化
            else:
                return str(item)
                
        except Exception as e:
            logging.warning(f"格式化知识条目失败: {e}")
            return str(item)
    
    def _call_api(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        调用DeepSeek API
        
        Args:
            messages: 消息列表
            
        Returns:
            Dict[str, Any]: API响应
        """
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": False
        }
        
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=self.timeout
        )
        
        response.raise_for_status()
        return response.json()
    
    def _parse_response(self, response: Dict[str, Any]) -> LLMResponse:
        """
        解析API响应
        
        Args:
            response: API响应
            
        Returns:
            LLMResponse: 解析后的响应
        """
        choice = response['choices'][0]
        message = choice['message']
        
        return LLMResponse(
            content=message['content'].strip(),
            usage=response.get('usage', {}),
            model=response.get('model', self.model_name),
            finish_reason=choice.get('finish_reason', 'unknown'),
            response_time=0
        )
    
    def test_connection(self) -> bool:
        """
        测试API连接
        
        Returns:
            bool: 连接是否成功
        """
        try:
            response = self.generate_response("你好，请简单回复一下。")
            return response.finish_reason != "error"
        except Exception as e:
            logging.error(f"测试DeepSeek连接失败: {e}")
            return False
    
    def set_parameters(self, max_tokens: int = None, temperature: float = None, 
                      timeout: int = None):
        """
        设置生成参数
        
        Args:
            max_tokens: 最大token数
            temperature: 温度参数
            timeout: 超时时间
        """
        if max_tokens is not None:
            self.max_tokens = max_tokens
        if temperature is not None:
            self.temperature = temperature
        if timeout is not None:
            self.timeout = timeout
        
        logging.info(f"更新LLM参数: max_tokens={self.max_tokens}, "
                    f"temperature={self.temperature}, timeout={self.timeout}")