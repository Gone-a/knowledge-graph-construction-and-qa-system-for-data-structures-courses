# train_intent_model.py
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from datasets import Dataset
from transformers import Trainer, TrainingArguments
from train_data import train_data



# 将文本标签转换为数字ID
unique_labels = list(set([label for _, label in train_data]))
label2id = {label: i for i, label in enumerate(unique_labels)}
id2label = {i: label for label, i in label2id.items()}

print(f"标签映射: {label2id}")

MODEL_NAME = 'bert-base-chinese'
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME, 
    num_labels=len(unique_labels) # 告诉模型我们要分成几类
)

# 将我们的数据转换成Hugging Face的Dataset格式
texts = [item[0] for item in train_data]
labels = [label2id[item[1]] for item in train_data]
dataset = Dataset.from_dict({"text": texts, "label": labels})

# 创建一个预处理函数
def preprocess_function(examples):
    return tokenizer(examples['text'], truncation=True, padding=True, max_length=128)

# 对整个数据集进行预处理
tokenized_dataset = dataset.map(preprocess_function, batched=True)
training_args = TrainingArguments(
    output_dir="./intent_classifier", # 训练结果输出目录
    num_train_epochs=10,             # 训练轮数
    per_device_train_batch_size=4,   # 每个设备的批处理大小
    logging_steps=1,                 # 每隔多少步打印一次日志
    save_strategy="epoch",           # 每个epoch保存一次模型
)

# 4. 创建并开始训练
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset,
)
print("开始训练模型...")
trainer.train()
print("训练完成！")

# 5. 保存模型、分词器和标签映射
MODEL_SAVE_PATH = "./my_intent_model"
model.save_pretrained(MODEL_SAVE_PATH)
tokenizer.save_pretrained(MODEL_SAVE_PATH)

import json
with open(f"{MODEL_SAVE_PATH}/label_map.json", 'w') as f:
    json.dump({'label2id': label2id, 'id2label': id2label}, f)

print(f"模型已保存至 {MODEL_SAVE_PATH}")