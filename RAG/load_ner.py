import os
import json
import torch
import hydra 
from transformers import AutoTokenizer
import numpy as np 
from deepke.name_entity_re.standard.w2ner import *


@hydra.main(config_path="../DeepKE/example/ner/standard/conf", config_name='config')
def main(cfg):
    config = type('Config', (), {})()
    for key in cfg.keys():
        config.__setattr__(key, cfg.get(key))
    
    #构建词汇表
    config = build_vocab(config)
    
    
    print('*********加载模型和分词器*********')
    model = Model(config).cuda()
    model.load_state_dict(torch.load(os.path.join(utils.get_original_cwd(), config.save_path, 'pytorch_model.bin')))
    model.eval()
    tokenizer = AutoTokenizer.from_pretrained(config.bert_name)
    
    print('*********加载完成!*********')

if __name__ == "__main__":
    main()