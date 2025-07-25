import os.path

from deepke.name_entity_re.standard.w2ner import *
import numpy as np
import hydra
from hydra import utils
import pickle
import torch

# 处理警告信息
import warnings
warnings.filterwarnings("ignore")
from transformers import logging as transformers_logging
transformers_logging.set_verbosity_error()

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
                i+=1
                while(i < len(sentence) and label[i][0] == 'I'):
                    i+=1
                d.append([start_index, i, flag[2:]])
            elif flag[0] == 'I':
                start_index = i
                i+=1
                while(i < len(sentence) and label[i][0] == 'I'):
                    i+=1
                d.append([start_index, i, flag[2:]])
            else:
                i+=1
        for s_e_flag in d:
            start_span, end_span, flag = s_e_flag[0], s_e_flag[1], s_e_flag[2]
            span_infos.append({'index': list(range(start_span, end_span)), 'type': flag})
        D.append({'sentence': sentence, 'ner': span_infos})

    return D

@hydra.main(config_path="conf", config_name='config')
def main(cfg):
    config = type('Config', (), {})()
    for key in cfg.keys():
        config.__setattr__(key, cfg.get(key))

    print('*********Building the vocabulary(Need Your Training Set!!!!)*********')
    processor = NerProcessor()
    train_examples = processor.get_train_examples(os.path.join(utils.get_original_cwd(), config.data_dir))
    train_data = trans_Dataset(config, train_examples)
    vocab = Vocabulary()
    train_ent_num = fill_vocab(vocab, train_data)
    print('Building Done!\n')

    config.label_num = len(vocab.label2id)
    print('*********Loading the Final Model*********')
    model = Model(config)
    model = model.cuda()
    model.load_state_dict(torch.load(os.path.join(utils.get_original_cwd(), config.save_path, 'pytorch_model.bin')))
    tokenizer = AutoTokenizer.from_pretrained(config.bert_name)
    print('Loading Done!\n')

    # 读取待预测文本文件，每行一句
    input_file = os.path.join(utils.get_original_cwd(), 'data/data_stream.txt')  # 可修改为你的输入文件
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]

    import re  # 用于分句
    all_results = []
    no_entity_sentences = []  # 存放未抽取出实体的小句
    for entity_text in lines:
        # 按标点分割为小句
        sub_sentences = re.split(r'[。！？；.;!?]', entity_text)
        for sub_sent in sub_sentences:
            sub_sent = sub_sent.strip()
            if not sub_sent:
                continue
            length = len([word for word in sub_sent])
            tokens = [tokenizer.tokenize(word) for word in sub_sent]
            pieces = [piece for pieces in tokens for piece in pieces]
            bert_inputs = tokenizer.convert_tokens_to_ids(pieces)
            bert_inputs = np.array([tokenizer.cls_token_id] + bert_inputs + [tokenizer.sep_token_id])
            pieces2word = np.zeros((length, len(bert_inputs)), dtype=np.bool_)
            grid_mask2d = np.ones((length, length), dtype=np.bool_)
            dist_inputs = np.zeros((length, length), dtype=np.int_)
            sent_length = length
            if tokenizer is not None:
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
            result = []
            with torch.no_grad():
                bert_inputs_t = torch.tensor([bert_inputs], dtype=torch.long).cuda()
                grid_mask2d_t = torch.tensor([grid_mask2d], dtype=torch.bool).cuda()
                dist_inputs_t = torch.tensor([dist_inputs], dtype=torch.long).cuda()
                pieces2word_t = torch.tensor([pieces2word], dtype=torch.bool).cuda()
                sent_length_t = torch.tensor([sent_length], dtype=torch.long).cuda()
                outputs = model(bert_inputs_t, grid_mask2d_t, dist_inputs_t, pieces2word_t, sent_length_t)
                length_t = sent_length_t
                grid_mask2d_t = grid_mask2d_t.clone()
                outputs = torch.argmax(outputs, -1)
                ent_c, ent_p, ent_r, decode_entities = decode(outputs.cpu().numpy(), sub_sent, length_t.cpu().numpy())
                decode_entities = decode_entities[0]
                input_sentence = [word for word in sub_sent]
                # 严格按格式输出：每小句只输出head/tail/offset等
                if len(decode_entities) >= 2:
                    head_indexes, head_label = decode_entities[0]
                    tail_indexes, tail_label = decode_entities[1]
                    head_str = ''.join([input_sentence[i] for i in head_indexes])
                    tail_str = ''.join([input_sentence[i] for i in tail_indexes])
                    all_results.append({
                        "sentence": sub_sent,
                        "head": head_str,
                        "tail": tail_str,
                        "head_offset": str(head_indexes[0]),
                        "tail_offset": str(tail_indexes[0])
                    })
                    # 只要头或尾实体为空就记录
                    if not head_str or not tail_str:
                        no_entity_sentences.append(sub_sent)
                elif len(decode_entities) == 1:
                    head_indexes, head_label = decode_entities[0]
                    head_str = ''.join([input_sentence[i] for i in head_indexes])
                    all_results.append({
                        "sentence": sub_sent,
                        "head": head_str,
                        "tail": "",
                        "head_offset": str(head_indexes[0]),
                        "tail_offset": ""
                    })
                    # 只要头或尾实体为空就记录
                    if not head_str:
                        no_entity_sentences.append(sub_sent)
                else:
                    all_results.append({
                        "sentence": sub_sent,
                        "head": "",
                        "tail": "",
                        "head_offset": "",
                        "tail_offset": ""
                    })
                    no_entity_sentences.append(sub_sent)  # 记录未抽取出实体的小句
    # 保存为json文件
    import json
    # 过滤掉 head 和 tail 都为空的结果
    filtered_results = [r for r in all_results if r.get('head') and r.get('tail')]
    output_path = os.path.join(utils.get_original_cwd(), 'output_predict', 'predict.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(filtered_results, f, ensure_ascii=False, indent=2)
    print(f"已保存预测结果到 {output_path}")

    # 保存未抽取出实体的小句到文件
    no_entity_path = os.path.join(utils.get_original_cwd(), 'output_predict', 'no_entity_sentences.txt')
    with open(no_entity_path, 'w', encoding='utf-8') as f:
        for sent in no_entity_sentences:
            if re.search(r'[\u4e00-\u9fa5a-zA-Z]', sent):  # 只保存含有中文或字母的句子
                f.write(sent + '\n')
    print(f"未抽取出实体的小句已保存到 {no_entity_path}")

if __name__ == "__main__":
    main()
