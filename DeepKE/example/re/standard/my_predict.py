import os
import sys
import torch
import logging
import hydra
import csv
import pandas as pd
from hydra import utils
from deepke.relation_extraction.standard.tools import Serializer
from deepke.relation_extraction.standard.tools import _serialize_sentence, _convert_tokens_into_index, _add_pos_seq, _handle_relation_data , _lm_serialize
import matplotlib.pyplot as plt
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))
from deepke.relation_extraction.standard.utils import load_pkl, load_csv
import deepke.relation_extraction.standard.models as models


logger = logging.getLogger(__name__)


def _preprocess_data(data, cfg):
    
    relation_data = load_csv(os.path.join(cfg.cwd, cfg.data_path, 'relation.csv'), verbose=False)
    rels = _handle_relation_data(relation_data)

    if cfg.model_name != 'lm':
        vocab = load_pkl(os.path.join(cfg.cwd, cfg.out_path, 'vocab.pkl'), verbose=False)
        cfg.vocab_size = vocab.count
        serializer = Serializer(do_chinese_split=cfg.chinese_split)
        serial = serializer.serialize

        _serialize_sentence(data, serial, cfg)
        _convert_tokens_into_index(data, vocab)
        _add_pos_seq(data, cfg)
        logger.info('start sentence preprocess...')
        formats = '\nsentence: {}\nchinese_split: {}\nreplace_entity_with_type:  {}\nreplace_entity_with_scope: {}\n' \
                'tokens:    {}\ntoken2idx: {}\nlength:    {}\nhead_idx:  {}\ntail_idx:  {}'
        logger.info(
            formats.format(data[0]['sentence'], cfg.chinese_split, cfg.replace_entity_with_type,
                        cfg.replace_entity_with_scope, data[0]['tokens'], data[0]['token2idx'], data[0]['seq_len'],
                        data[0]['head_idx'], data[0]['tail_idx']))
    else:
        _lm_serialize(data,cfg)

    return data, rels


def _load_csv_data(csv_path):
    """批量加载CSV文件中的预测数据"""
    data = []
    try:
        df = pd.read_csv(csv_path)
        required_columns = ['sentence', 'head', 'tail', 'head_type', 'tail_type']
        
        # 检查CSV是否包含所有必需的列
        for col in required_columns:
            if col not in df.columns:
                logger.error(f"CSV文件缺少必要的列: {col}")
                sys.exit(1)
        
        for _, row in df.iterrows():
            instance = {
                'sentence': str(row['sentence']).strip(),
                'head': str(row['head']).strip(),
                'tail': str(row['tail']).strip(),
                'head_type': str(row['head_type']).strip(),
                'tail_type': str(row['tail_type']).strip()
            }
            data.append(instance)
        logger.info(f'成功从 {csv_path} 加载 {len(data)} 条预测数据')
    except Exception as e:
        logger.error(f'加载CSV文件失败: {e}')
        sys.exit(1)
    
    return data


@hydra.main(config_path='conf/config.yaml')
def main(cfg):
    cwd = utils.get_original_cwd()
    cfg.cwd = cwd
    cfg.pos_size = 2 * cfg.pos_limit + 2
    print(cfg.pretty())

    # 批量加载CSV文件
    batch_predict_file="data/my_origin/test.csv"
    
    csv_path = os.path.join(cfg.cwd, batch_predict_file)
    data = _load_csv_data(csv_path)

    # preprocess data
    data, rels = _preprocess_data(data, cfg)

    # model
    __Model__ = {
        'cnn': models.PCNN,
        'rnn': models.BiLSTM,
        'transformer': models.Transformer,
        'gcn': models.GCN,
        'capsule': models.Capsule,
        'lm': models.LM,
    }

    # 最好在 cpu 上预测
    cfg.use_gpu = False
    if cfg.use_gpu and torch.cuda.is_available():
        device = torch.device('cuda', cfg.gpu_id)
    else:
        device = torch.device('cpu')
    logger.info(f'device: {device}')

    model = __Model__[cfg.model_name](cfg)
    logger.info(f'model name: {cfg.model_name}')
    logger.info(f'\n {model}')
    model.load(cfg.fp, device=device)
    model.to(device)
    model.eval()

    def process_single_piece(model, piece, device, rels, model_name):
        with torch.no_grad():
            # 确保只传递模型需要的键
            required_keys = ['word', 'lens']
            if model_name != 'lm':
                required_keys.extend(['head_pos', 'tail_pos'])
                if model_name == 'cnn' and cfg.use_pcnn:
                    required_keys.append('pcnn_mask')
                if model_name == 'gcn':
                    required_keys.append('adj')
            
            filtered_piece = {k: v.to(device) for k, v in piece.items() if k in required_keys}
            y_pred = model(filtered_piece)
            y_pred = torch.softmax(y_pred, dim=-1)[0]  
            prob = y_pred.max().item()
            index = y_pred.argmax().item()
            if index >= len(rels):
                print("The index {} is out of range for 'rels' with length {}.".format(index, len(rels)))
                return [], 0, 0
            prob_rel = list(rels.keys())[index]
            return prob_rel, prob, y_pred
        
    # 存储所有预测结果
    all_results = []
    
    for i, instance in enumerate(data):
        logger.info(f"\n处理实例 {i+1}/{len(data)}: {instance['sentence']}")
        
        # 为当前实例创建临时数据
        instance_data = [instance]
        
        if cfg.model_name != 'lm':
            x = dict()
            tokens = instance['token2idx'] if 'token2idx' in instance else []
            seq_len = instance['seq_len'] if 'seq_len' in instance else len(tokens)
            
            # 填充到固定长度
            padded_tokens = tokens + [0] * (512 - len(tokens))
            x['word'] = torch.tensor([padded_tokens])
            x['lens'] = torch.tensor([seq_len])
            
            # 处理位置信息 - 确保这些键存在
            head_pos = instance.get('head_pos', [0]*len(tokens))
            tail_pos = instance.get('tail_pos', [0]*len(tokens))
            padded_head_pos = head_pos + [0] * (512 - len(head_pos))
            padded_tail_pos = tail_pos + [0] * (512 - len(tail_pos))
            x['head_pos'] = torch.tensor(padded_head_pos).unsqueeze(0)  # 增加批次维度
            x['tail_pos'] = torch.tensor(padded_tail_pos).unsqueeze(0)   # 增加批次维度
            
            # 记录输入键的调试信息
            logger.debug(f"模型输入键: {list(x.keys())}")
            
            if cfg.model_name == 'cnn' and cfg.use_pcnn:
                entities_pos = instance.get('entities_pos', [0]*len(tokens))
                padded_entities_pos = entities_pos + [0] * (512 - len(entities_pos))
                x['pcnn_mask'] = torch.tensor([padded_entities_pos])
                
            if cfg.model_name == 'gcn':
                adj = torch.empty(1, 512, 512).random_(2)
                x['adj'] = adj

            prob_rel, prob, y_pred = process_single_piece(model, x, device, rels, cfg.model_name)
            
            logger.info(f"结果: \"{instance['head']}\" 和 \"{instance['tail']}\" 关系为: \"{prob_rel}\", 置信度: {prob:.4f}")
            all_results.append({
                'sentence': instance['sentence'],
                'head': instance['head'],
                'tail': instance['tail'],
                'relation': prob_rel,
                'confidence': prob
            })
        else:  # LM模型处理
            tokenized_input = instance['token2idx']
            max_len = 512
            num_pieces = len(tokenized_input) // max_len + (1 if len(tokenized_input) % max_len > 0 else 0)
            
            max_prob = -1
            best_relation = ''
            
            for j in range(num_pieces):
                start_idx = j * max_len
                end_idx = min((j + 1) * max_len, len(tokenized_input))
                current_piece_input = {
                    'word': torch.tensor([tokenized_input[start_idx:end_idx] + [0] * (max_len - (end_idx - start_idx))]),
                    'lens': torch.tensor([min(end_idx - start_idx, max_len)])
                }
                relation, prob, y_pred = process_single_piece(model, current_piece_input, device, rels, cfg.model_name)
                if prob > max_prob:
                    max_prob = prob
                    best_relation = relation
            
            logger.info(f"结果: \"{instance['head']}\" 和 \"{instance['tail']}\" 关系为: \"{best_relation}\", 置信度: {max_prob:.4f}")
            all_results.append({
                'sentence': instance['sentence'],
                'head': instance['head'],
                'tail': instance['tail'],
                'relation': best_relation,
                'confidence': max_prob
            })
    
    # 保存结果到CSV
    results_dir = os.path.join(cfg.cwd, cfg.out_path, 'predictions')
    os.makedirs(results_dir, exist_ok=True)
    results_file = os.path.join(results_dir, 'predictions.csv')
    
    try:
        results_df = pd.DataFrame(all_results)
        results_df.to_csv(results_file, index=False, encoding='utf-8-sig')
        logger.info(f"预测结果已保存到: {results_file}")
    except Exception as e:
        logger.error(f"保存结果失败: {e}")


if __name__ == '__main__':
    main()