#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
W2NER模型数据处理脚本
用于处理data_stream.txt文件，生成包含sentence,head,tail,head_offset,tail_offset,head_type,tail_type字段的CSV文件
"""

import os
import sys
import csv
import json
import re
import numpy as np
import torch
import warnings
from typing import List, Dict, Any

# 添加DeepKE路径
sys.path.append('/root/KG/DeepKE/example/ner/standard/w2ner')

# 处理警告信息
warnings.filterwarnings("ignore")
from transformers import logging as transformers_logging
transformers_logging.set_verbosity_error()

# 导入w2ner相关模块
try:
    from deepke.name_entity_re.standard.w2ner import *
    from transformers import AutoTokenizer
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保已正确安装DeepKE和相关依赖")
    sys.exit(1)

class W2NERProcessor:
    """W2NER模型处理器"""
    
    def __init__(self, model_path='/root/KG/DeepKE/example/ner/standard/w2ner'):
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.vocab = None
        self.config = None
        
    def load_model(self):
        """加载W2NER模型"""
        print('*********加载W2NER模型*********')
        
        # 切换到模型目录
        original_cwd = os.getcwd()
        os.chdir(self.model_path)
        
        try:
            # 直接创建配置对象，使用默认参数
            config = type('Config', (), {})()
            
            # 设置基本配置参数
            config.data_dir = 'data'
            config.save_path = 'output'
            config.bert_name = 'bert-base-chinese'
            config.do_lower_case = True
            config.max_seq_len = 512
            config.batch_size = 6
            config.epochs = 15
            config.device = 0 if torch.cuda.is_available() else -1
            
            # 训练参数
            config.do_train = True
            config.do_eval = True
            config.do_predict = True
            config.warm_factor = 0.1
            config.weight_decay = 0.1
            config.clip_grad_norm = 5.0
            config.bert_learning_rate = 1e-5
            config.learning_rate = 1e-3
            config.use_bert_last_4_layers = True
            config.seed = 123
            
            # 模型参数
            config.dist_emb_size = 20
            config.type_emb_size = 20
            config.lstm_hid_size = 512
            config.conv_hid_size = 96
            config.bert_hid_size = 768
            config.biaffine_size = 512
            config.ffnn_hid_size = 288
            config.dilation = [1, 2, 3]
            
            # dropout参数
            config.emb_dropout = 0.5
            config.conv_dropout = 0.5
            config.out_dropout = 0.33
            
            self.config = config
            
            # 构建词汇表
            print('构建词汇表...')
            processor = NerProcessor()
            train_examples = processor.get_train_examples(config.data_dir)
            train_data = self.trans_Dataset(config, train_examples)
            
            vocab = Vocabulary()
            fill_vocab(vocab, train_data)
            self.vocab = vocab
            
            config.label_num = len(vocab.label2id)
            
            # 加载模型
            print('加载模型权重...')
            model = Model(config)
            if torch.cuda.is_available():
                model = model.cuda()
                model.load_state_dict(torch.load(os.path.join(config.save_path, 'pytorch_model.bin')))
            else:
                model.load_state_dict(torch.load(os.path.join(config.save_path, 'pytorch_model.bin'), map_location='cpu'))
            
            model.eval()
            self.model = model
            
            # 加载tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(config.bert_name)
            
            print('模型加载完成！\n')
            
        except Exception as e:
            print(f"模型加载失败: {e}")
            raise e
        finally:
            # 恢复原始工作目录
            os.chdir(original_cwd)
    
    def trans_Dataset(self, config, examples):
        """转换数据集格式"""
        D = []
        for example in examples:
            span_infos = []
            sentence, label, d = example.text_a.split(' '), example.label, []
            if len(sentence) > config.max_seq_len:
                continue
            assert len(sentence) == len(label)
            i = 0
            while i < len(sentence):
                flag = label[i]
                if flag[0] == 'B':
                    start_index = i
                    i += 1
                    while(i < len(sentence) and label[i][0] == 'I'):
                        i += 1
                    d.append([start_index, i, flag[2:]])
                elif flag[0] == 'I':
                    start_index = i
                    i += 1
                    while(i < len(sentence) and label[i][0] == 'I'):
                        i += 1
                    d.append([start_index, i, flag[2:]])
                else:
                    i += 1
            for s_e_flag in d:
                start_span, end_span, flag = s_e_flag[0], s_e_flag[1], s_e_flag[2]
                span_infos.append({'index': list(range(start_span, end_span)), 'type': flag})
            D.append({'sentence': sentence, 'ner': span_infos})
        return D
    
    def preprocess_text(self, text):
        """预处理文本"""
        length = len([word for word in text])
        tokens = [self.tokenizer.tokenize(word) for word in text]
        pieces = [piece for pieces in tokens for piece in pieces]
        
        bert_inputs = self.tokenizer.convert_tokens_to_ids(pieces)
        bert_inputs = np.array([self.tokenizer.cls_token_id] + bert_inputs + [self.tokenizer.sep_token_id])
        
        pieces2word = np.zeros((length, len(bert_inputs)), dtype=np.bool_)
        grid_mask2d = np.ones((length, length), dtype=np.bool_)
        dist_inputs = np.zeros((length, length), dtype=np.int_)
        sent_length = length
        
        if self.tokenizer is not None:
            start = 0
            for i, pieces in enumerate(tokens):
                if len(pieces) == 0:
                    continue
                pieces = list(range(start, start + len(pieces)))
                pieces2word[i, pieces[0] + 1:pieces[-1] + 2] = 1
                start += len(pieces)
        
        for k in range(length):
            dist_inputs[k, :] += k
            dist_inputs[:, k] -= k
        
        for i in range(length):
            for j in range(length):
                if dist_inputs[i, j] < 0:
                    dist_inputs[i, j] = dis2idx[-dist_inputs[i, j]] + 9
                else:
                    dist_inputs[i, j] = dis2idx[dist_inputs[i, j]]
        dist_inputs[dist_inputs == 0] = 19
        
        return {
            'bert_inputs': bert_inputs,
            'grid_mask2d': grid_mask2d,
            'dist_inputs': dist_inputs,
            'pieces2word': pieces2word,
            'sent_length': sent_length
        }
    
    def map_entity_type(self, original_label):
        """将原始实体标签映射为CON或ARI类型"""
        # 根据实体含义进行映射
        # CON: 概念类实体 (如数据结构、算法概念等)
        # ARI: 属性类实体 (如数值、特征、操作等)
        
        concept_entities = {
            '树', '图', '栈', '队列', '链表', '数组', '哈希表', '堆',
            '算法', '排序', '搜索', '遍历', '递归', '迭代',
            '数据结构', '线性表', '非线性结构', '二叉树', '平衡树',
            '图论', '网络', '节点', '边', '路径', '环'
        }
        
        attribute_entities = {
            '时间复杂度', '空间复杂度', '效率', '性能', '速度',
            '长度', '大小', '容量', '深度', '高度', '宽度',
            '权重', '值', '键', '索引', '位置', '偏移',
            '操作', '插入', '删除', '查找', '更新', '修改'
        }
        
        # 检查实体文本是否包含概念或属性关键词
        for concept in concept_entities:
            if concept in original_label:
                return 'CON'
        
        for attribute in attribute_entities:
            if attribute in original_label:
                return 'ARI'
        
        # 默认映射为CON
        return 'CON'
    
    def predict_entities(self, text):
        """预测实体"""
        if self.model is None:
            raise ValueError("模型未加载，请先调用load_model()")
        
        preprocessed = self.preprocess_text(text)
        
        with torch.no_grad():
            if torch.cuda.is_available():
                bert_inputs_t = torch.tensor([preprocessed['bert_inputs']], dtype=torch.long).cuda()
                grid_mask2d_t = torch.tensor([preprocessed['grid_mask2d']], dtype=torch.bool).cuda()
                dist_inputs_t = torch.tensor([preprocessed['dist_inputs']], dtype=torch.long).cuda()
                pieces2word_t = torch.tensor([preprocessed['pieces2word']], dtype=torch.bool).cuda()
                sent_length_t = torch.tensor([preprocessed['sent_length']], dtype=torch.long).cuda()
            else:
                bert_inputs_t = torch.tensor([preprocessed['bert_inputs']], dtype=torch.long)
                grid_mask2d_t = torch.tensor([preprocessed['grid_mask2d']], dtype=torch.bool)
                dist_inputs_t = torch.tensor([preprocessed['dist_inputs']], dtype=torch.long)
                pieces2word_t = torch.tensor([preprocessed['pieces2word']], dtype=torch.bool)
                sent_length_t = torch.tensor([preprocessed['sent_length']], dtype=torch.long)
            
            outputs = self.model(bert_inputs_t, grid_mask2d_t, dist_inputs_t, pieces2word_t, sent_length_t)
            outputs = torch.argmax(outputs, -1)
            
            ent_c, ent_p, ent_r, decode_entities = decode(outputs.cpu().numpy(), text, sent_length_t.cpu().numpy())
            decode_entities = decode_entities[0]
            
            entities = []
            input_sentence = [word for word in text]
            for ner in decode_entities:
                ner_indexes, ner_label = ner
                entity_text = ''.join([input_sentence[ner_index] for ner_index in ner_indexes])
                original_label = self.vocab.id2label[ner_label]
                
                # 将实体类型映射为CON或ARI
                mapped_label = self.map_entity_type(original_label)
                
                entities.append({
                    'text': entity_text,
                    'label': mapped_label,
                    'original_label': original_label,
                    'start': ner_indexes[0],
                    'end': ner_indexes[-1] + 1,
                    'indexes': ner_indexes
                })
            
            return entities

def generate_relation_data(entities, sentence):
    """从实体列表生成实体数据"""
    entity_data = []
    
    # 如果实体数量少于2个，无法构成关系
    if len(entities) < 2:
        return entity_data
    
    # 生成所有可能的实体对
    for i in range(len(entities)):
        for j in range(i + 1, len(entities)):
            head_entity = entities[i]
            tail_entity = entities[j]
            
            entity_data.append({
                'sentence': sentence,
                'head': head_entity['text'],
                'tail': tail_entity['text'],
                'head_offset': head_entity['start'],
                'tail_offset': tail_entity['start'],
                'head_type': head_entity['label'],
                'tail_type': tail_entity['label']
            })
    
    return entity_data



def process_data_stream(input_file, output_file):
    """处理数据流文件"""
    print(f"开始处理文件: {input_file}")
    
    # 初始化W2NER处理器
    processor = W2NERProcessor()
    processor.load_model()
    
    # 读取输入文件
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    
    all_relations = []
    
    print(f"开始处理 {len(lines)} 行数据...")
    
    for i, line in enumerate(lines):
        if i % 100 == 0:
            print(f"已处理 {i}/{len(lines)} 行")
        
        # 按标点分割为小句
        sub_sentences = re.split(r'[。！？；.;!?]', line)
        
        for sub_sent in sub_sentences:
            sub_sent = sub_sent.strip()
            if not sub_sent or len(sub_sent) < 3:  # 过滤太短的句子
                continue
            
            try:
                # 预测实体
                entities = processor.predict_entities(sub_sent)
                
                # 生成关系数据
                relations = generate_relation_data(entities, sub_sent)
                all_relations.extend(relations)
                
            except Exception as e:
                print(f"处理句子时出错: {sub_sent[:50]}... 错误: {e}")
                continue
    
    # 保存为CSV文件
    print(f"保存结果到: {output_file}")
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['sentence', 'head', 'tail', 'head_offset', 'tail_offset', 'head_type', 'tail_type']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for relation in all_relations:
            writer.writerow(relation)
    
    print(f"处理完成！共生成 {len(all_relations)} 条实体数据")
    return all_relations

def main():
    """主函数"""
    input_file = '/root/KG/DeepKE/example/ner/prepare-data/source_data/data_stream.txt'
    output_file = '/root/KG/w2ner_relations.csv'
    
    if not os.path.exists(input_file):
        print(f"输入文件不存在: {input_file}")
        return
    
    try:
        relations = process_data_stream(input_file, output_file)
        print(f"\n成功处理完成！")
        print(f"输入文件: {input_file}")
        print(f"输出文件: {output_file}")
        print(f"生成实体数据数量: {len(relations)}")
        
        # 显示前几条结果作为示例
        if relations:
            print("\n前5条结果示例:")
            for i, rel in enumerate(relations[:5]):
                print(f"{i+1}. 句子: {rel['sentence'][:50]}...")
                print(f"   实体对: {rel['head']} --> {rel['tail']}")
                print(f"   类型: {rel['head_type']} --> {rel['tail_type']}")
                print()
        
    except Exception as e:
        print(f"处理过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()