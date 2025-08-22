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
    train()
    predict()


if __name__=="__main__":
    main()
