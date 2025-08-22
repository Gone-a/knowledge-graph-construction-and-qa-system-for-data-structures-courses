#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import torch
import pandas as pd
import numpy as np
import logging
from typing import List, Dict, Tuple, Any
from tqdm import tqdm
import warnings
warnings.filterwarnings("ignore")

# 添加DeepKE路径
sys.path.append('/root/KG/DeepKE/example/re/standard')
sys.path.append('/root/KG/DeepKE')

try:
    from deepke.relation_extraction.standard.tools import Serializer
    from deepke.relation_extraction.standard.tools import _serialize_sentence, _convert_tokens_into_index, _add_pos_seq, _handle_relation_data, _lm_serialize
    from deepke.relation_extraction.standard.utils import load_pkl, load_csv
    import deepke.relation_extraction.standard.models as models
    from omegaconf import OmegaConf
    DEEPKE_AVAILABLE = True
except ImportError:
    DEEPKE_AVAILABLE = False
    print("DeepKE不可用，将使用简化版关系预测器")

class RelationPredictor:
    """
    关系预测器，用于对NER提取的所有实体进行两两组合的关系预测
    """
    
    def __init__(self, confidence_threshold=0.7):
        if not DEEPKE_AVAILABLE:
            raise ImportError("DeepKE关系抽取模块不可用，无法创建关系预测器。请确保DeepKE已正确安装。")
            
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.cfg = None
        self.vocab = None
        self.rels = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # 加载DeepKE模型
        self._load_model()
        if not self.model_loaded:
            raise RuntimeError("DeepKE关系抽取模型加载失败，无法创建关系预测器")
    
    def _load_model(self):
        """
        加载DeepKE关系抽取模型
        """
        if not DEEPKE_AVAILABLE:
            print("使用简化版关系预测器")
            self.model_loaded = False
            return
            
        try:
            # 导入必要的模块
            import os
            
            # 加载DeepKE配置
            config_path = '/root/KG/DeepKE/example/re/standard/conf/config.yaml'
            model_path = '/root/KG/DeepKE/example/re/standard/checkpoints/best_model.pth'
            
            if not os.path.exists(model_path):
                print(f"模型文件不存在: {model_path}，使用简化版预测器")
                self.model_loaded = False
                return
                
            # 加载配置
            self.cfg = OmegaConf.load(config_path)
            
            # 手动加载preprocess配置
            preprocess_path = '/root/KG/DeepKE/example/re/standard/conf/preprocess.yaml'
            preprocess_cfg = OmegaConf.load(preprocess_path)
            
            # 手动加载model配置
            model_path_cfg = '/root/KG/DeepKE/example/re/standard/conf/model/gcn.yaml'
            model_cfg = OmegaConf.load(model_path_cfg)
            
            # 手动加载embedding配置
            embedding_path = '/root/KG/DeepKE/example/re/standard/conf/embedding.yaml'
            embedding_cfg = OmegaConf.load(embedding_path)
            
            # 手动加载train配置
            train_path = '/root/KG/DeepKE/example/re/standard/conf/train.yaml'
            train_cfg = OmegaConf.load(train_path)
            
            # 手动加载predict配置
            predict_path = '/root/KG/DeepKE/example/re/standard/conf/predict.yaml'
            predict_cfg = OmegaConf.load(predict_path)
            
            # 合并配置
            self.cfg = OmegaConf.merge(self.cfg, preprocess_cfg, model_cfg, embedding_cfg, train_cfg, predict_cfg)
            
            self.cfg.cwd = '/root/KG/DeepKE/example/re/standard'
            self.cfg.fp = model_path
            print(f"pos_limit: {self.cfg.pos_limit}")
            print(f"pos_limit type: {type(self.cfg.pos_limit)}")
            if self.cfg.pos_limit is None:
                raise RuntimeError("pos_limit为None，无法计算pos_size")
            self.cfg.pos_size = 2 * self.cfg.pos_limit + 2
            print(f"pos_size: {self.cfg.pos_size}")
            self.cfg.use_gpu = False
            
            # 加载关系数据
            relation_data = load_csv(os.path.join(self.cfg.cwd, self.cfg.data_path, 'relation.csv'), verbose=False)
            self.rels = _handle_relation_data(relation_data)
            
            # 加载词汇表
            if self.cfg.model_name != 'lm':
                vocab_path = os.path.join(self.cfg.cwd, self.cfg.out_path, 'vocab.pkl')
                print(f"正在加载词汇表: {vocab_path}")
                print(f"模型名称: {self.cfg.model_name}")
                self.vocab = load_pkl(vocab_path, verbose=False)
                if self.vocab is None:
                    raise RuntimeError(f"词汇表加载失败: {vocab_path}")
                self.cfg.vocab_size = self.vocab.count
                print(f"词汇表加载成功，大小: {self.cfg.vocab_size}")
            else:
                print(f"使用语言模型 {self.cfg.model_name}，跳过词汇表加载")
                self.vocab = None
            
            # 初始化模型
            __Model__ = {
                'cnn': models.PCNN,
                'rnn': models.BiLSTM,
                'transformer': models.Transformer,
                'gcn': models.GCN,
                'capsule': models.Capsule,
                'lm': models.LM,
            }
            
            self.model = __Model__[self.cfg.model_name](self.cfg)
            self.model.load(self.cfg.fp, device=self.device)
            self.model.to(self.device)
            self.model.eval()
            
            self.model_loaded = True
            print(f"成功加载DeepKE模型: {self.cfg.model_name}")
            
        except Exception as e:
            print(f"DeepKE模型加载失败: {e}，使用简化版预测器")
            self.model_loaded = False
    
    def predict_relations_for_entities(self, sentence: str, entities: List[Dict]) -> List[Dict]:
        """
        对句子中的所有实体进行两两组合的关系预测
        
        Args:
            sentence: 输入句子
            entities: 实体列表，每个实体包含 {'text': str, 'label': str, 'start_pos': int, 'end_pos': int}
        
        Returns:
            关系预测结果列表
        """
        if len(entities) < 2:
            return []
        
        relations = []
        
        # 对所有实体进行两两组合
        for i, entity1 in enumerate(entities):
            for j, entity2 in enumerate(entities):
                if i != j:  # 不同实体
                    # 预测关系
                    relation_result = self._predict_single_relation(
                        sentence, entity1, entity2
                    )
                    
                    # 过滤低置信度的关系
                    if relation_result['confidence'] >= self.confidence_threshold:
                        relations.append(relation_result)
        
        return relations
    
    def _predict_single_relation(self, sentence: str, entity1: Dict, entity2: Dict) -> Dict:
        """
        预测单个实体对的关系
        
        Args:
            sentence: 输入句子
            entity1: 头实体
            entity2: 尾实体
        
        Returns:
            关系预测结果
        """
        if self.model_loaded and DEEPKE_AVAILABLE:
            # 使用训练好的模型进行预测
            return self._model_predict(sentence, entity1, entity2)
        else:
            # 使用简单的规则进行预测
            return self._simple_predict(sentence, entity1, entity2)
    
    def _simple_predict(self, sentence: str, entity1: Dict, entity2: Dict) -> Dict:
        """
        简单的关系预测（备用方法）
        """
        return {
            'sentence': sentence,
            'head': entity1['text'],
            'tail': entity2['text'],
            'relation': 'none',
            'confidence': 0.1
        }
    
    def _model_predict(self, sentence: str, entity1: Dict, entity2: Dict) -> Dict:
        """
        使用原始DeepKE模型进行关系预测
        """
        head_entity = entity1['text']
        tail_entity = entity2['text']
        result = self._predict_with_deepke_model(sentence, head_entity, tail_entity)
        
        # 添加头尾实体和句子信息
        result.update({
            'sentence': sentence,
            'head': head_entity,
            'tail': tail_entity
        })
        
        return result
    
    def predict_relation_for_pair(self, sentence: str, head_entity: str, tail_entity: str) -> Dict[str, Any]:
        """
        使用原始DeepKE模型预测实体对之间的关系
        
        Args:
            sentence: 句子文本
            head_entity: 头实体
            tail_entity: 尾实体
            
        Returns:
            包含关系和置信度的字典
        """
        return self._predict_with_deepke_model(sentence, head_entity, tail_entity)
    
    def _predict_with_deepke_model(self, sentence: str, head_entity: str, tail_entity: str) -> Dict[str, Any]:
        """
        使用DeepKE模型进行关系预测
        """
        try:
            # 构造预测数据
            data = [{
                'sentence': sentence,
                'head': head_entity,
                'tail': tail_entity,
                'head_offset': sentence.find(head_entity),
                'tail_offset': sentence.find(tail_entity),
                'head_type': 'ENTITY',  # 默认实体类型
                'tail_type': 'ENTITY',  # 默认实体类型
                'relation': 'unknown'   # 默认关系
            }]
            
            # 数据预处理
            if self.cfg.model_name != 'lm':
                serializer = Serializer(do_chinese_split=self.cfg.chinese_split)
                serial = serializer.serialize
                
                _serialize_sentence(data, serial, self.cfg)
                _convert_tokens_into_index(data, self.vocab)
                _add_pos_seq(data, self.cfg)
            else:
                _lm_serialize(data, self.cfg)
            
            # 模型预测
            instance = data[0]
            
            if self.cfg.model_name != 'lm':
                x = dict()
                tokens = instance['token2idx'] if 'token2idx' in instance else []
                seq_len = instance['seq_len'] if 'seq_len' in instance else len(tokens)
                max_len = 512
                
                # 填充到固定长度
                padded_tokens = tokens + [0] * (max_len - len(tokens))
                x['word'] = torch.tensor([padded_tokens])
                x['lens'] = torch.tensor([seq_len])
                
                if 'head_pos' in instance:
                    head_pos = instance['head_pos'] + [0] * (max_len - len(instance['head_pos']))
                    x['head_pos'] = torch.tensor([head_pos])
                if 'tail_pos' in instance:
                    tail_pos = instance['tail_pos'] + [0] * (max_len - len(instance['tail_pos']))
                    x['tail_pos'] = torch.tensor([tail_pos])
                
                # 其他模型特定的输入
                if self.cfg.model_name == 'cnn' and hasattr(self.cfg, 'use_pcnn') and self.cfg.use_pcnn:
                    if 'pcnn_mask' in instance:
                        x['pcnn_mask'] = torch.tensor([instance['pcnn_mask']])
                if self.cfg.model_name == 'gcn':
                    if 'adj' in instance:
                        x['adj'] = torch.tensor([instance['adj']])
                    else:
                        # 为GCN模型生成随机邻接矩阵
                        x['adj'] = torch.empty(1, max_len, max_len).random_(2).float()
            else:
                # 语言模型的输入处理
                x = {
                    'word': torch.tensor([instance.get('input_ids', [])]),
                    'lens': torch.tensor([len(instance.get('input_ids', []))])
                }
            
            # 移动到设备
            for key in x:
                x[key] = x[key].to(self.device)
            
            # 模型推理
            with torch.no_grad():
                y_pred = self.model(x)
                y_pred = torch.softmax(y_pred, dim=-1)[0]
                prob = y_pred.max().item()
                index = y_pred.argmax().item()
                
                if index >= len(self.rels):
                    return {
                        'relation': 'none',
                        'confidence': 0.0
                    }
                
                prob_rel = list(self.rels.keys())[index]
                
                return {
                    'relation': prob_rel,
                    'confidence': prob
                }
                 
        except Exception:
            # 使用简化预测器作为备用
            return {
                'relation': 'none',
                'confidence': 0.1
            }
    
    def enhance_predictions_with_all_entities(self, predictions_csv_path: str, 
                                            ner_extractor, output_csv_path: str = None) -> str:
        """
        使用NER提取的所有实体进行关系预测增强
        
        Args:
            predictions_csv_path: 原始预测结果CSV路径
            ner_extractor: NER提取器实例
            output_csv_path: 输出CSV路径
        
        Returns:
            增强后的CSV文件路径
        """
        # 读取原始预测结果
        df = pd.read_csv(predictions_csv_path)
        
        # 获取所有唯一句子
        unique_sentences = df['sentence'].unique()
        
        enhanced_data = []
        # 使用集合来跟踪已添加的关系，避免重复
        added_relations = set()
        
        print("使用NER+RE模型进行全实体关系预测...")
        for sentence in tqdm(unique_sentences, desc="处理句子"):
            # 获取原始关系（保留高置信度的原始关系）
            original_relations = df[df['sentence'] == sentence]
            
            # 添加高置信度的原始关系（去重）
            for _, row in original_relations.iterrows():
                if row.get('confidence', 1.0) >= self.confidence_threshold:
                    relation_key = (sentence, row['head'], row['tail'], row['relation'])
                    if relation_key not in added_relations:
                        enhanced_data.append({
                            'sentence': sentence,
                            'head': row['head'],
                            'tail': row['tail'],
                            'relation': row['relation'],
                            'confidence': row.get('confidence', 1.0),
                            'source': 'original'
                        })
                        added_relations.add(relation_key)
            
            # 使用NER提取所有实体
            entities = ner_extractor.extract_entities_from_text(sentence)
            
            if len(entities) >= 2:
                # 对所有实体进行两两关系预测
                predicted_relations = self.predict_relations_for_entities(sentence, entities)
                
                # 添加新预测的关系（去重）
                for rel in predicted_relations:
                    relation_key = (rel['sentence'], rel['head'], rel['tail'], rel['relation'])
                    if relation_key not in added_relations:
                        enhanced_data.append({
                            'sentence': rel['sentence'],
                            'head': rel['head'],
                            'tail': rel['tail'],
                            'relation': rel['relation'],
                            'confidence': rel['confidence'],
                            'source': 'ner_re_predicted'
                        })
                        added_relations.add(relation_key)
        
        # 保存增强后的数据
        enhanced_df = pd.DataFrame(enhanced_data)
        
        if output_csv_path is None:
            output_csv_path = predictions_csv_path.replace('.csv', '_enhanced_full.csv')
        
        enhanced_df.to_csv(output_csv_path, index=False, encoding='utf-8')
        
        print(f"增强后的预测结果已保存到: {output_csv_path}")
        print(f"原始关系: {len(df)} -> 增强后: {len(enhanced_df)} (新增: {len(enhanced_df) - len(df)})")
        print(f"置信度阈值: {self.confidence_threshold}")
        
        return output_csv_path

def create_relation_predictor(confidence_threshold=0.7):
    """
    创建原始DeepKE关系预测器
    
    Args:
        confidence_threshold: 置信度阈值
        
    Returns:
        RelationPredictor实例
        
    Raises:
        ImportError: 如果DeepKE不可用
    """
    if not DEEPKE_AVAILABLE:
        raise ImportError("DeepKE关系抽取模块不可用，无法创建关系预测器。请确保DeepKE已正确安装。")
    
    return RelationPredictor(confidence_threshold=confidence_threshold)