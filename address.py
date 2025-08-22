#集成了re模型(抽取关系)训练与预测,需要对w2ner_relations.csv数据标注relation字段
import argparse
import torch
from torch.utils.data import Dataset,DataLoader
import os
import sys

# 将DeepKE目录添加到Python路径
sys.path.append(os.path.join(os.getcwd(), 'DeepKE'))
from DeepKE.example.re.standard.run import main as train_main
from DeepKE.example.re.standard.my_predict import main as predict_main

device=torch.device("cuda:0" if torch.cuda.is_available() else "cpu")


#接受命令参数(已淘汰)
def arg_process():
    parser=argparse.ArgumentParser(description='KG')
    parser.add_argument("--data_path",type=str,default="./data",help="data path")
    parser.add_argument("--model_path",type=str,default="./model/best_model.pth",help="model path")
    parser.add_argument("--epoch",type=int,default=100,help="epoch")
    parser.add_argument("--lr",type=float,default=1e-4,help="learning rate")
    parser.add_argument("--batch_size",type=int,default=64,help="batch size")
    parser.add_argument("--train_file",type=str,default="./data/train.json",help="train file")
    parser.add_argument("--dev_file",type=str,default="./data/dev.json",help="dev file")
    parser.add_argument("--test_file",type=str,default="./data/test.json",help="test file")
    parser.add_argument("--output",type=str,default="./model",help="output path")
    parser.add_argument("--process",type=bool,default=False,help="process data")
    cfg=parser.parse_args()
    cfg.device=device
    cfg.cwd=os.getcwd()
    return cfg

def train():
    # 切换到DeepKE的标准关系抽取目录
    original_cwd = os.getcwd()
    deepke_dir = os.path.join(original_cwd, "DeepKE/example/re/standard")
    os.chdir(deepke_dir)
    
    try:
        train_main()
    finally:
        # 恢复原始工作目录
        os.chdir(original_cwd)
    
def predict():
    # 切换到DeepKE的标准关系抽取目录
    original_cwd = os.getcwd()
    deepke_dir = os.path.join(original_cwd, "DeepKE/example/re/standard")
    os.chdir(deepke_dir)
    
    try:
        predict_main()
    finally:
        # 恢复原始工作目录
        os.chdir(original_cwd)
    



def main():
    #cfg=arg_process()
    #print(cfg)
    train()
    predict()


if __name__=="__main__":
    main()
