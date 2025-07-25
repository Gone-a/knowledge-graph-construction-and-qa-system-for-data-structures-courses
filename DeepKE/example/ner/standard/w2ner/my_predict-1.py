import os.path
import re
import json
import numpy as np
import torch
import hydra
from hydra import utils
from tqdm import tqdm
from multiprocessing import Pool, cpu_count
from functools import partial
from transformers import AutoTokenizer, logging as transformers_logging
from deepke.name_entity_re.standard.w2ner import *

# 禁用不必要的警告
import warnings
transformers_logging.set_verbosity_error()
warnings.filterwarnings("ignore")

# 定义dis2idx（根据原始模型配置）
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

# 修复问题：添加构建词汇表的函数
def build_vocab(config):
    """构建词汇表以获取label_num"""
    print('*********Building the vocabulary(Need Your Training Set!!!*********')
    processor = NerProcessor()
    train_examples = processor.get_train_examples(os.path.join(utils.get_original_cwd(), config.data_dir))
    
    def trans_Dataset(config, examples: List[InputExample]):
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
    
    train_data = trans_Dataset(config, train_examples)
    vocab = Vocabulary()
    train_ent_num = fill_vocab(vocab, train_data)
    config.label_num = len(vocab.label2id)
    print(f'Building Done! Label num: {config.label_num}\n')
    return config

def process_sentence(sub_sent, tokenizer, max_seq_len):
    """处理单个句子并返回输入数据"""
    sub_sent = sub_sent.strip()
    if not sub_sent:
        return None
    
    words = list(sub_sent)
    length = len(words)
    
    if length > max_seq_len or length == 0:
        return None
    
    # Tokenization
    tokens = [tokenizer.tokenize(word) for word in words]
    pieces = [piece for pieces in tokens for piece in pieces]
    bert_inputs = tokenizer.convert_tokens_to_ids(pieces)
    bert_inputs = np.array([tokenizer.cls_token_id] + bert_inputs + [tokenizer.sep_token_id])
    
    # 构建pieces2word矩阵
    pieces2word = np.zeros((length, len(bert_inputs)), dtype=np.bool_)
    grid_mask2d = np.ones((length, length), dtype=np.bool_)
    
    start = 0
    for i, token_pieces in enumerate(tokens):
        if not token_pieces:
            continue
        end = start + len(token_pieces)
        pieces2word[i, start+1:end+1] = 1  # +1 跳过[CLS]
        start = end
    
    # 距离矩阵向量化计算
    rows, cols = np.indices((length, length))
    dist_array = rows - cols
    abs_dist = np.abs(dist_array)
    abs_dist = np.clip(abs_dist, 0, 999)
    dist_inputs = dis2idx[abs_dist]
    dist_inputs[dist_array < 0] += 9
    dist_inputs[dist_inputs == 0] = 19
    
    return {
        "sentence": sub_sent,
        "words": words,
        "bert_inputs": bert_inputs,
        "pieces2word": pieces2word,
        "grid_mask2d": grid_mask2d,
        "dist_inputs": dist_inputs,
        "length": length
    }

@hydra.main(config_path="conf", config_name='config')
def main(cfg):
    config = type('Config', (), {})()
    for key in cfg.keys():
        config.__setattr__(key, cfg.get(key))
    
    # 修复问题：先构建词汇表
    config = build_vocab(config)
    
    print('*********加载模型和分词器*********')
    model = Model(config).cuda()
    model.load_state_dict(torch.load(os.path.join(utils.get_original_cwd(), config.save_path, 'pytorch_model.bin')))
    model.eval()
    tokenizer = AutoTokenizer.from_pretrained(config.bert_name)
    
    print('*********加载完成!*********')
    # 读取输入文件
    input_file = os.path.join(utils.get_original_cwd(), 'data/data_stream.txt')
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    
    # 分割所有小句
    all_sub_sents = []
    for text in lines:
        sub_sents = re.split(r'[。！？；.;!?]', text)
        all_sub_sents.extend([s.strip() for s in sub_sents if s.strip()])
    
    print(f"待处理小句总数: {len(all_sub_sents)}")
    
    # 多进程预处理
    print("预处理小句...")
    with Pool(cpu_count()) as pool:
        process_func = partial(process_sentence, tokenizer=tokenizer, max_seq_len=config.max_seq_len)
        processed_data = list(tqdm(
            pool.imap(process_func, all_sub_sents), 
            total=len(all_sub_sents),
            desc="预处理进度"
        ))
    
    # 过滤无效结果
    valid_data = [d for d in processed_data if d is not None]
    print(f"有效小句数量: {len(valid_data)}/{len(all_sub_sents)}")
    
    # 批量推理
    print("开始批量推理...")
    all_results = []
    no_entity_sentences = []
    batch_size = 16  # 根据GPU内存调整

    # 按句子长度分组，使批内句子长度相近
    length_groups = {}
    for data in valid_data:
        length = data['length']
        if length not in length_groups:
            length_groups[length] = []
        length_groups[length].append(data)

    # 按长度排序
    sorted_lengths = sorted(length_groups.keys())
    sorted_data = []
    for length in sorted_lengths:
        sorted_data.extend(length_groups[length])

    # 批处理
    for i in tqdm(range(0, len(sorted_data), batch_size), desc="推理进度"):
        batch = sorted_data[i:i+batch_size]
        
        # 找到批内最大长度和最大序列长度
        max_length = max([d['length'] for d in batch])
        max_seq_len = max([len(d['bert_inputs']) for d in batch])
        
        # 初始化批张量
        bert_inputs_batch = torch.full(
            (len(batch), max_seq_len), 
            tokenizer.pad_token_id, 
            dtype=torch.long
        ).cuda()
        
        pieces2word_batch = torch.zeros(
            (len(batch), max_length, max_seq_len), 
            dtype=torch.bool
        ).cuda()
        
        grid_mask2d_batch = torch.zeros(
            (len(batch), max_length, max_length), 
            dtype=torch.bool
        ).cuda()
        
        dist_inputs_batch = torch.zeros(
            (len(batch), max_length, max_length), 
            dtype=torch.long
        ).cuda()
        
        sent_length_batch = torch.tensor(
            [d['length'] for d in batch], 
            dtype=torch.long
        ).cuda()
        
        # 填充批张量
        for j, data in enumerate(batch):
            seq_len = len(data['bert_inputs'])
            bert_inputs_batch[j, :seq_len] = torch.tensor(data['bert_inputs'], dtype=torch.long)
            
            # 填充pieces2word
            pieces2word = torch.tensor(data['pieces2word'], dtype=torch.bool)
            pieces2word_batch[j, :pieces2word.size(0), :pieces2word.size(1)] = pieces2word
            
            # 填充grid_mask2d
            grid_mask2d_batch[j, :data['length'], :data['length']] = torch.tensor(data['grid_mask2d'], dtype=torch.bool)
            
            # 填充dist_inputs
            dist_inputs_batch[j, :data['length'], :data['length']] = torch.tensor(data['dist_inputs'], dtype=torch.long)
        
        # 模型推理
        with torch.no_grad():
            outputs = model(bert_inputs_batch, grid_mask2d_batch, dist_inputs_batch, pieces2word_batch, sent_length_batch)
            outputs = torch.argmax(outputs, -1)
        
        # 解码结果
        for j, data in enumerate(batch):
            output = outputs[j].unsqueeze(0)  # 添加批次维度
            decode_entities = decode(output.cpu().numpy(), data["sentence"], [data["length"]])[3][0]
            words = data["words"]
            
            result = {"sentence": data["sentence"], "head": "", "tail": "", "head_offset": "", "tail_offset": ""}
            entity_found = False
            
            # 按照起始位置排序实体
            if len(decode_entities) > 0:
                # 按实体起始位置排序
                sorted_entities = sorted(decode_entities, key=lambda x: min(x[0]))
                
                # 确保头实体在前
                head_entity = sorted_entities[0]
                tail_entity = sorted_entities[1] if len(sorted_entities) > 1 else None
                
                # 处理头实体
                head_indexes, head_label = head_entity
                result["head"] = ''.join([words[idx] for idx in head_indexes])
                result["head_offset"] = str(min(head_indexes))
                entity_found = True
                
                # 处理尾实体（如果存在且位置在头实体后）
                if tail_entity:
                    tail_indexes, tail_label = tail_entity
                    if min(tail_indexes) > min(head_indexes):  # 确保尾实体在头实体之后
                        result["tail"] = ''.join([words[idx] for idx in tail_indexes])
                        result["tail_offset"] = str(min(tail_indexes))
                    else:
                        # 如果尾实体在头实体前，交换它们
                        result["head"], result["tail"] = result["tail"], result["head"]
                        result["head_offset"], result["tail_offset"] = result["tail_offset"], result["head_offset"]
            
            # 新增：检查头尾实体是否相同，相同则丢弃
            if entity_found and result["head"] and result["tail"]:
                if result["head"] == result["tail"]:
                    entity_found = False
                    same_entity_sentences.append(data["sentence"])  # 记录头尾相同的句子
            
            all_results.append(result)
            if not entity_found or not result["head"] or not result["tail"]:
                no_entity_sentences.append(data["sentence"])
        
    # 保存结果
    os.makedirs(os.path.join(utils.get_original_cwd(), 'output_predict'), exist_ok=True)
    
    # 过滤有效结果
    filtered_results = [r for r in all_results if r.get('head') and r.get('tail')]
    output_path = os.path.join(utils.get_original_cwd(), 'output_predict', 'predict.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(filtered_results, f, ensure_ascii=False, indent=2)
    print(f"已保存预测结果到 {output_path} (有效实体: {len(filtered_results)}/{len(all_results)})")
    
    # 保存无实体句子
    no_entity_path = os.path.join(utils.get_original_cwd(), 'output_predict', 'no_entity_sentences.txt')
    with open(no_entity_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(set(no_entity_sentences)))  # 去重
    print(f"未抽取出实体的小句已保存到 {no_entity_path} (数量: {len(set(no_entity_sentences))})")

if __name__ == "__main__":
    main()