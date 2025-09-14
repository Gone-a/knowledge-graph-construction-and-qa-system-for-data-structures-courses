# -*- coding: utf-8 -*-
from intent_recognition.enre import KNOWLEDGE_BASE
import torch
import json
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# ==============================================================================
# 1. 知识库 (Knowledge Base)
#    存放系统已知的所有实体和关系。
#    键(key)是标准名称(ID)，值(value)是用户可能会提到的各种说法（同义词）。
# ==============================================================================


# ==============================================================================
# 2. 自然语言理解模块 (Natural Language Understanding Module)
#    这是系统的大脑，负责解析用户输入。
# ==============================================================================
class NLU_DeepLearning:
    def __init__(self, model_path):
        # 1. 加载模型、分词器和标签映射
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        
        with open(f"{model_path}/label_map.json", 'r') as f:
            label_map = json.load(f)
            self.id2label = label_map['id2label']
            # 注意json加载后key会变成字符串，需要转换回来
            self.id2label = {int(k): v for k, v in self.id2label.items()}

        # 知识库部分仍然保留，用于实体提取
        self.entities_kb = KNOWLEDGE_BASE["entities"]
        self.relations_kb = KNOWLEDGE_BASE["relations"]
        print("深度学习NLU模型加载成功！")

    def _extract_elements(self, text):
        # 实体和关系提取部分保持不变，仍然使用关键字匹配
        # 未来这一部分也可以升级为NER（命名实体识别）深度学习模型
        found_entities = []
        found_relations = []
        for entity_id, synonyms in self.entities_kb.items():
            for synonym in synonyms:
                if synonym in text:
                    found_entities.append(entity_id)
                    break
        for relation_id, synonyms in self.relations_kb.items():
            for synonym in synonyms:
                if synonym in text:
                    found_relations.append(relation_id)
                    break
        return found_entities, found_relations

    def recognize_intent(self, text):
        """
        使用加载的深度学习模型进行意图识别。
        """
        # 2. 对输入文本进行编码
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        
        # 3. 模型预测
        with torch.no_grad(): # 推理时不需要计算梯度
            logits = self.model(**inputs).logits
            
        # 4. 解码结果
        predicted_class_id = logits.argmax().item()
        return self.id2label[predicted_class_id]

    def understand(self, text):
        """
        NLU模组的主函数，整合所有功能。
        """
        # 步骤1: 使用深度学习模型识别意图
        intent = self.recognize_intent(text)
        
        # 步骤2: 使用关键字匹配提取元素
        found_entities, found_relations = self._extract_elements(text)
        
        # 步骤3: 组装结果
        return {
            "text": text,
            "intent": intent,
            "entities": found_entities,
            "relations": found_relations
        }
# ==============================================================================
# 3. 對話管理/執行模組 (Core / Handler)
#    根據NLU的分析結果，決定要如何回應。
# ==============================================================================
class Handler:
    def __init__(self, nlu_processor):
        self.nlu = nlu_processor

    def process(self, user_input):
        """处理单次用户输入并返回结果"""
        
        # 从NLU模块获取分析结果
        nlu_result = self.nlu.understand(user_input)
        
        intent = nlu_result["intent"]
        entities = nlu_result["entities"]
        relations = nlu_result["relations"]
        
        print(f"--- 分析中 ---")
        print(f"原始对话: '{user_input}'")
        print(f"NLU 结果: {nlu_result}")
        print(f"--- 回应 ---")

        # 根据不同的意图，执行不同的动作
        if intent == "find_relation_by_two_entities":
            # 意图一的处理逻辑
            # 在这里你可以加入实际查询知识图谱的代码
            response = f"意图识别: [通过两端点找线段]。\n找到的两个端点是: {entities[0]} 和 {entities[1]}。"
            return response

        elif intent == "find_entity_by_relation_and_entity":
            # 意图二的处理逻辑
            response = f"意图识别: [通过线段和一端点找另一端点]。\n找到的线段是: {relations[0]}，端点是: {entities[0]}。"
            return response
            
        else: # intent == "other"
            # 其他意图的处理逻辑
            return "意图识别: [其他]。\n抱歉，我不太理解您的意思，请换个方式说说看？"
# ==============================================================================
# 主程式入口 (Main Execution)
# ==============================================================================
if __name__ == "__main__":
    # 知识库定义 (KNOWLEDGE_BASE) 和 Handler 类保持不变...
    # ... (此处省略和之前框架中相同的代码)
    
    # 1. 初始化NLU和处理器
    # 注意！这里我们实例化新的NLU类
    MODEL_PATH = "./my_intent_model" # 指定模型路径
    nlu_processor = NLU_DeepLearning(MODEL_PATH)
    handler = Handler(nlu_processor) # Handler类无需任何改动

    # 2. 模拟不同的用户输入
    test_queries = [
        "A点和B点连起来是啥",                 # 应该预测为意图一
        "已知BC线段和C点，求另一个点",        # 应该预测为意图二
        "今天星期几？",                      # 应该预测为other
        "我想查查B和C组成的线",              # 应该预测为意图一
    ]

    # 3. 执行并印出结果
    for query in test_queries:
        result = handler.process(query)
        print(result)
        print("="*30)