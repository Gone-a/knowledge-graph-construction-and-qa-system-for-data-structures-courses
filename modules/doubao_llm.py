# -*- coding: utf-8 -*-
"""豆包（火山方舟）LLM调用模块"""
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from volcenginesdkarkruntime import Ark  # 火山方舟SDK
from modules.config_manager import get_config_manager
import json
# 复用原LLMResponse数据类，确保返回格式兼容
@dataclass
class LLMResponse:
    content: str
    usage: Dict[str, int]
    model: str
    finish_reason: str
    response_time: float

class DoubaoLLM:
    """豆包（火山方舟）LLM客户端"""
class DoubaoLLM:
    def __init__(self, user_api_key: Optional[str] = None, user_model_id: Optional[str] = None):
        """
        初始化豆包客户端（支持用户自定义API Key和模型ID）
        :param user_api_key: 用户传入的火山方舟API Key
        :param user_model_id: 用户传入的豆包Model ID
        """
        self.config = get_config_manager().get_api_config()
        self.llm_config = get_config_manager().get_llm_config()
        
        # 1. 优先级：用户传入 > 系统配置
        self.ark_api_key = user_api_key.strip() if (user_api_key and user_api_key.strip()) else self.config.get('ark_api_key')
        self.doubao_model_id = user_model_id.strip() if (user_model_id and user_model_id.strip()) else self.config.get('doubao_model_id')
        
        # 2. 初始化火山方舟客户端
        self.client = Ark(api_key=self.ark_api_key)
        self.history_messages = []  # 历史对话列表
        # 3. 默认温度（后续可动态修改）
        self.default_temperature = self.llm_config.get('temperature', 0.7)
        self.max_tokens = self.llm_config.get('max_tokens', 2000)

        logging.info(f"豆包LLM客户端初始化完成（API Key：{'用户自定义' if user_api_key else '系统默认'}，模型ID：{self.doubao_model_id}）")

    def _get_default_system_prompt(self) -> str:
        """复用now项目的SYSTEM_PROMPT，确保回答逻辑一致"""
        return """
# 1. 你的身份 (Your Identity)
你是一个世界级的数据结构与算法专家，你的名字叫“代码导师”(Code Mentor)。...（完整复制now项目api_calls.py的SYSTEM_PROMPT）
        """.strip()

    def _build_messages(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
        """构建豆包API所需的消息格式（参考now项目的call_deepseek_api）"""
        # 1. 系统提示
        messages = [{"role": "system", "content": self._get_default_system_prompt()}]
        # 2. 拼接用户问题+知识图谱上下文（复用913原逻辑）
        context_str = json.dumps(context, ensure_ascii=False) if context else "无"
        user_content = f"### 当前用户问题：{user_input}\n### 背景知识（来自知识图谱）：{context_str}"
        messages.append({"role": "user", "content": user_content})
        return messages

    def generate_response(self, user_input: str, 
                         temperature: Optional[float] = None) -> LLMResponse:
        """
        生成AI响应（支持历史对话拼接和动态温度）
        :param user_input: 当前用户输入
        :param history_messages: 历史对话列表（格式：[{"role": "user/assistant", "content": "..."}]）
        :param temperature: 用户传入的温度（0-2，无则用默认）
        """
        try:
            # 1. 处理温度参数（校验范围：0-2，避免无效值）
            final_temp = temperature if (temperature is not None and 0 <= temperature <= 2) else self.default_temperature
            
            # 2. 拼接对话上下文（系统提示 + 历史对话 + 当前输入）
            messages = [{"role": "system", "content": self._get_default_system_prompt()}]
            # 追加历史对话（若存在）
            if self.history_messages and isinstance(self.history_messages, list):
                messages.extend([msg for msg in self.history_messages if isinstance(msg, dict) and msg.get('role') in ['user', 'assistant']])
            # 追加当前用户输入
            messages.append({"role": "user", "content": user_input.strip()})

            # 3. 调用豆包API
            completion = self.client.chat.completions.create(
                model=self.doubao_model_id,
                messages=messages,
                temperature=final_temp,
                max_tokens=self.max_tokens,
                stream=False
            )

            # 4. 解析响应
            resp_msg = completion.choices[0].message
            return LLMResponse(
                content=resp_msg.content.strip(),
                usage=completion.usage.__dict__ if hasattr(completion, 'usage') else {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                model=self.doubao_model_id,
                finish_reason=completion.choices[0].finish_reason,
                response_time=0
            )

        except Exception as e:
            err_msg = f"豆包调用失败：{str(e)}"
            logging.error(err_msg)
            return LLMResponse(
                content=f"抱歉，服务暂时不可用：{err_msg}",
                usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                model=self.doubao_model_id,
                finish_reason="error",
                response_time=0
            )

    def set_parameters(self, max_tokens: int = None, temperature: float = None):
        """复用原set_parameters方法，确保接口兼容"""
        if max_tokens:
            self.max_tokens = max_tokens
        if temperature:
            self.temperature = temperature