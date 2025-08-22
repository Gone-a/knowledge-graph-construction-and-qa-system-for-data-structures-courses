import os
import re
import json
import numpy as np
import torch
import pandas as pd
from typing import List, Dict, Tuple
from transformers import AutoTokenizer, logging as transformers_logging
from tqdm import tqdm
import warnings

# 禁用不必要的警告
transformers_logging.set_verbosity_error()
warnings.filterwarnings("ignore")

# 尝试导入DeepKE的W2NER模块
try:
    import sys
    sys.path.append('/root/KG/DeepKE/src')
    from deepke.name_entity_re.standard.w2ner import *
    DEEPKE_AVAILABLE = True
except ImportError:
    print("Warning: DeepKE W2NER module not available. NER extraction will be disabled.")
    DEEPKE_AVAILABLE = False

class NERExtractor:
    """
    基于W2NER模型的命名实体识别提取器
    用于从文本中提取更多实体，优化知识图谱拓展性能
    """
    
    def __init__(self, model_path=None, config_path=None):
        self.model = None
        self.tokenizer = None
        self.config = None
        self.dis2idx = self._build_dis2idx()
        self.model_loaded = False
        
        if DEEPKE_AVAILABLE and model_path and config_path:
            self._load_model(model_path, config_path)
    
    def _build_dis2idx(self):
        """构建距离索引映射"""
        dis2idx = np.zeros((1000), dtype='int64')
        dis2idx[1] = 1
        dis2idx[2:] = 2
        dis2idx[4:] = 3
        dis2idx[8:] = 4
        dis2idx[16:] = 5
        dis2idx[32:] = 6
        dis2idx[64:] = 7
        dis2idx[128:] = 8
        dis2idx[256:] = 9
        return dis2idx
    
    def _load_model(self, model_path, config_path):
        """加载W2NER模型，参考my_predict-1.py的加载方式"""
        try:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            print(f"使用设备: {device}")
            
            # 创建配置对象，包含必要的参数
            self.config = type('Config', (), {
                'bert_name': 'bert-base-chinese',
                'max_seq_len': 512,
                'label_num': 5,  # 根据模型权重确定的标签数量
                'data_dir': 'data',
                'save_path': os.path.dirname(model_path) if model_path else 'checkpoints',
                # 添加W2NER模型需要的配置属性
                'dist_emb_size': 20,
                'type_emb_size': 20,
                'lstm_hid_size': 512,
                'conv_hid_size': 96,
                'bert_hid_size': 768,
                'biaffine_size': 512,
                'ffnn_hid_size': 288,
                'dilation': [1, 2, 3],
                'emb_dropout': 0.5,
                'conv_dropout': 0.5,
                'out_dropout': 0.33,
                'do_lower_case': True,
                'use_bert_last_4_layers': True,
                'use_lstm': True,
                'use_cnn': True
            })()
            
            # 尝试加载词汇表以获取正确的label_num
            vocab_path = os.path.join(self.config.save_path, 'vocab.pkl')
            if os.path.exists(vocab_path):
                try:
                    import pickle
                    with open(vocab_path, 'rb') as f:
                        vocab = pickle.load(f)
                    self.config.label_num = len(vocab.label2id)
                    # 设置词汇表相关配置
                    self.config.label2id = vocab.label2id
                    self.config.id2label = vocab.id2label
                    print(f"从词汇表加载label_num: {self.config.label_num}")
                except Exception as e:
                    print(f"加载词汇表失败，使用默认label_num: {e}")
            
            if os.path.exists(model_path):
                # 创建模型实例
                self.model = Model(self.config)
                self.model.to(device)
                
                # 加载模型权重
                state_dict = torch.load(model_path, map_location=device)
                self.model.load_state_dict(state_dict)
                self.model.eval()
                
                # 加载分词器
                self.tokenizer = AutoTokenizer.from_pretrained(self.config.bert_name)
                self.model_loaded = True
                print("NER模型加载成功")
            else:
                print(f"模型文件不存在: {model_path}")
                self.model_loaded = False
                
        except Exception as e:
            print(f"加载NER模型失败: {e}")
            import traceback
            traceback.print_exc()
            self.model_loaded = False
    
    def _process_sentence(self, sentence: str) -> Dict:
        """预处理单个句子"""
        sentence = sentence.strip()
        if not sentence or len(sentence) > self.config.max_seq_len:
            return None
        
        words = list(sentence)
        length = len(words)
        
        tokens = [self.tokenizer.tokenize(word) for word in words]
        pieces = [piece for pieces in tokens for piece in pieces]
        bert_inputs = self.tokenizer.convert_tokens_to_ids(pieces)
        bert_inputs = np.array([self.tokenizer.cls_token_id] + bert_inputs + [self.tokenizer.sep_token_id])
        
        pieces2word = np.zeros((length, len(bert_inputs)), dtype=np.bool_)
        grid_mask2d = np.ones((length, length), dtype=np.bool_)
        
        start = 0
        for i, token_pieces in enumerate(tokens):
            if token_pieces:
                end = start + len(token_pieces)
                pieces2word[i, start+1:end+1] = 1
                start = end
        
        rows, cols = np.indices((length, length))
        dist_array = rows - cols
        abs_dist = np.clip(np.abs(dist_array), 0, 999)
        dist_inputs = self.dis2idx[abs_dist]
        dist_inputs[dist_array < 0] += 9
        dist_inputs[dist_inputs == 0] = 19
        
        return {
            "sentence": sentence,
            "words": words,
            "bert_inputs": bert_inputs,
            "pieces2word": pieces2word,
            "grid_mask2d": grid_mask2d,
            "dist_inputs": dist_inputs,
            "length": length
        }
    
    def extract_entities_from_text(self, text: str) -> List[Dict]:
        """从文本中提取实体"""
        if not self.model_loaded or not DEEPKE_AVAILABLE:
            print("NER模型未加载或DeepKE不可用，跳过实体提取")
            return []
        
        # 分割句子
        sentences = re.split(r'[。！？；.;!?]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        all_entities = []
        
        for sentence in sentences:
            entities = self._extract_entities_from_sentence(sentence)
            all_entities.extend(entities)
        
        return all_entities
    
    def _extract_entities_from_sentence(self, sentence: str) -> List[Dict]:
        """从单个句子中提取实体，参考my_predict-1.py的推理方式"""
        processed_data = self._process_sentence(sentence)
        if not processed_data:
            return []
        
        try:
            # 检查模型是否在CUDA上
            device = next(self.model.parameters()).device
            
            # 准备输入张量，确保维度正确
            bert_inputs = torch.tensor([processed_data['bert_inputs']], dtype=torch.long).to(device)
            pieces2word = torch.tensor([processed_data['pieces2word']], dtype=torch.bool).to(device)
            grid_mask2d = torch.tensor([processed_data['grid_mask2d']], dtype=torch.bool).to(device)
            dist_inputs = torch.tensor([processed_data['dist_inputs']], dtype=torch.long).to(device)
            sent_length = torch.tensor([processed_data['length']], dtype=torch.long).to(device)
            
            # 模型推理
            with torch.no_grad():
                outputs = self.model(bert_inputs, grid_mask2d, dist_inputs, pieces2word, sent_length)
                outputs = torch.argmax(outputs, -1)
            
            # 解码实体，使用与my_predict-1.py相同的方式
            decode_entities = decode(outputs.cpu().numpy(), processed_data["sentence"], [processed_data["length"]])[3][0]
            
            entities = []
            for entity_indexes, entity_label in decode_entities:
                entity_text = ''.join([processed_data["words"][idx] for idx in entity_indexes])
                entities.append({
                    'text': entity_text,
                    'label': entity_label,
                    'start_pos': min(entity_indexes),
                    'end_pos': max(entity_indexes),
                    'sentence': sentence
                })
            
            return entities
            
        except Exception as e:
            print(f"实体提取失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def enhance_predictions_with_ner(self, predictions_csv_path: str, output_csv_path: str = None) -> str:
        """
        使用NER模型增强现有的预测结果
        从原始句子中提取更多实体，生成新的关系候选
        """
        if not self.model_loaded:
            print("NER模型未加载，无法增强预测结果")
            return predictions_csv_path
        
        # 读取原始预测结果
        df = pd.read_csv(predictions_csv_path)
        
        # 获取所有唯一句子
        unique_sentences = df['sentence'].unique()
        
        enhanced_data = []
        
        print("使用NER模型提取更多实体...")
        for sentence in tqdm(unique_sentences, desc="处理句子"):
            # 获取原始关系
            original_relations = df[df['sentence'] == sentence]
            
            # 添加原始关系
            for _, row in original_relations.iterrows():
                enhanced_data.append({
                    'sentence': sentence,
                    'head': row['head'],
                    'tail': row['tail'],
                    'relation': row['relation'],
                    'confidence': row.get('confidence', 1.0),
                    'source': 'original'
                })
            
            # 提取新实体
            entities = self._extract_entities_from_sentence(sentence)
            
            # 生成新的实体对组合
            existing_pairs = set()
            for _, row in original_relations.iterrows():
                existing_pairs.add((row['head'], row['tail']))
            
            # 为新提取的实体生成关系候选
            for i, entity1 in enumerate(entities):
                for j, entity2 in enumerate(entities):
                    if i != j:  # 不同实体
                        pair = (entity1['text'], entity2['text'])
                        if pair not in existing_pairs and entity1['text'] != entity2['text']:
                            # 添加新的关系候选（关系类型设为unknown，需要后续处理）
                            enhanced_data.append({
                                'sentence': sentence,
                                'head': entity1['text'],
                                'tail': entity2['text'],
                                'relation': 'unknown',  # 需要关系分类模型进一步处理
                                'confidence': 0.5,  # 较低的置信度
                                'source': 'ner_extracted'
                            })
                            existing_pairs.add(pair)
        
        # 保存增强后的数据
        enhanced_df = pd.DataFrame(enhanced_data)
        
        if output_csv_path is None:
            output_csv_path = predictions_csv_path.replace('.csv', '_enhanced.csv')
        
        enhanced_df.to_csv(output_csv_path, index=False, encoding='utf-8')
        
        print(f"增强后的预测结果已保存到: {output_csv_path}")
        print(f"原始关系数量: {len(df)}")
        print(f"增强后关系数量: {len(enhanced_df)}")
        print(f"新增关系数量: {len(enhanced_df) - len(df)}")
        
        return output_csv_path



def create_ner_extractor(model_path=None, config_path=None):
    """
    创建NER提取器实例
    必须使用原始DeepKE W2NER模型
    """
    if not DEEPKE_AVAILABLE:
        raise ImportError("DeepKE W2NER模块不可用，无法创建NER提取器。请确保DeepKE已正确安装。")
    
    # 设置默认的模型和配置路径
    if model_path is None:
        model_path = '/root/KG/DeepKE/example/ner/standard/w2ner/output/pytorch_model.bin'
    if config_path is None:
        config_path = '/root/KG/DeepKE/example/ner/standard/w2ner/conf/config.yaml'
    
    print(f"使用原始DeepKE W2NER模型: {model_path}")
    return NERExtractor(model_path, config_path)