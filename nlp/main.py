# main.py
import torch
import json
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from transformers import AutoTokenizer, AutoModelForSequenceClassification
from RAG.query_fixed import DSAGraphQAFixed
# 从我们创建的文件中导入必要的变量和函数
from config import NLU_MODEL_PATH
from knowledge_base import KNOWLEDGE_BASE
from api_calls import call_kg_api_for_segment, call_kg_api_for_point, call_deepseek_api

class ConversationHistory:
    def __init__(self):
        self.history = []
    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
    def get_history(self):
        return self.history

class NLU_DeepLearning:
    def __init__(self, model_path):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        with open(f"{model_path}/label_map.json", 'r', encoding='utf-8') as f:
            label_map = json.load(f)
            self.id2label = {int(k): v for k, v in label_map['id2label'].items()}
        # 这里我们直接使用从 knowledge_base.py 导入的 KNOWLEDGE_BASE
        self.entities_kb = KNOWLEDGE_BASE["entities"]
        self.relations_kb = KNOWLEDGE_BASE["relations"]
        print("深度学习NLU模型加载成功！")

    def _extract_elements(self, text):
        found_entities, found_relations = [], []
        for entity_id, synonyms in self.entities_kb.items():
            for synonym in synonyms:
                if synonym in text: found_entities.append(entity_id); break
        for relation_id, synonyms in self.relations_kb.items():
            for synonym in synonyms:
                if synonym in text: found_relations.append(relation_id); break
        return found_entities, found_relations

    def recognize_intent(self, text):
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        with torch.no_grad():
            logits = self.model(**inputs).logits
        return self.id2label[logits.argmax().item()]

    def understand(self, text):
        intent = self.recognize_intent(text)
        entities, relations = self._extract_elements(text)
        return {"intent": intent, "entities": entities, "relations": relations}

class Handler:
    def __init__(self, nlu_processor):
        self.nlu = nlu_processor

    def process(self, user_input: str, history: ConversationHistory,qa_system: DSAGraphQAFixed):
        # ... (nlu_result 和 knowledge_data 的获取逻辑无需改动) ...
        nlu_result = self.nlu.understand(user_input)
        print(f"\n--- 分析中 ---")
        print(f"NLU 结果: {nlu_result}")
        
        intent, entities, relations = nlu_result["intent"], nlu_result["entities"], nlu_result["relations"]
        
        knowledge_data = None
        if intent == "find_relation_by_two_entities" and len(entities) == 2:
            knowledge_data = call_kg_api_for_segment(entities[0], entities[1],qa_system)
        elif intent == "find_entity_by_relation_and_entity" and len(entities) == 1 and len(relations) == 1:
            knowledge_data = call_kg_api_for_point(relations[0], entities[0],qa_system)
        
        knowledge_str = json.dumps(knowledge_data, ensure_ascii=False) if knowledge_data else "无"
        
        history.add_message("user", user_input)
        
        # --- 已更改: 调用新的函数 ---
        ai_response = call_deepseek_api(history.get_history(), knowledge_str)
        
        history.add_message("assistant", ai_response)
        
        return ai_response

if __name__ == "__main__":
    try:
        nlu_processor = NLU_DeepLearning(NLU_MODEL_PATH)
    except Exception as e:
        print(f"加载NLU模型失败，请确认 '{NLU_MODEL_PATH}' 路径正确。错误: {e}")
        exit()
        
    handler = Handler(nlu_processor)
    history = ConversationHistory()
    qa_system = DSAGraphQAFixed(
        "bolt://localhost:7687",
        "neo4j",
        os.getenv("NEO4J_KEY")
    )

    print("\n欢迎使用智能对话系统！")
    while True:
        user_input = input("您: ")
        # 从Handler获取回复。注意：Handler内部已经更新了history
        ai_response = handler.process(user_input, history,qa_system)
        
        print(f"AI: {ai_response}")
    