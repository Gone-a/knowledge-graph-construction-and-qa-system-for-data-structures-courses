import json
import random
import time  # 引入time模块，用于生成随时间变化的种子

def json_to_csv(input_json, output_csv):
    # （原代码不变）
    try:
        with open(input_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        with open(output_csv, 'w', encoding='utf-8') as csv_file:
            csv_file.write("sentence,relation,head,tail,head_offset,tail_offset\n")
        for i in data:
            if 'head' in i and 'tail' in i:
                head = i['head']
                tail = i['tail']
                sentence = '"' + str(i['sentence']).replace('"', '""') + '"'
                head_offset = i['head_offset']
                tail_offset = i['tail_offset']
                relation = i["relation"]
                with open(output_csv, 'a', encoding='utf-8') as csv_file:
                    csv_file.write(f"{sentence},{relation},{head},{tail},{head_offset},{tail_offset}\n")
    except FileNotFoundError:
        print(f"文件 {input_json} 未找到")
    except json.JSONDecodeError:
        print(f"无法解析 {input_json} 中的 JSON 数据")
    except Exception as e:
        print(f"写入 CSV 文件时出现错误: {e}")

def split_csv(input_csv, train_csv, test_csv, valid_csv):
    try:
        with open(input_csv, 'r', encoding='utf-8') as csv_file:
            lines = csv_file.readlines()
            header = lines[0]  # 表头不参与打乱
            data_lines = lines[1:]  # 数据行
            
            # 增强随机性：设置随机种子为当前时间戳（随时间动态变化）
            # 每次运行时种子不同，shuffle结果更随机
            random.seed(time.time_ns())  # 使用纳秒级时间戳作为种子，精度更高
            
            # 打乱数据行
            random.shuffle(data_lines)
            
            total_lines = len(data_lines)
            train_lines = int(total_lines * 0.7)
            test_lines = int(total_lines * 0.1)

            with open(train_csv, 'w', encoding='utf-8') as train_file:
                train_file.write(header)
                train_file.writelines(data_lines[:train_lines])

            with open(test_csv, 'w', encoding='utf-8') as test_file:
                test_file.write(header)
                test_file.writelines(data_lines[train_lines:train_lines + test_lines])

            with open(valid_csv, 'w', encoding='utf-8') as val_file:
                val_file.write(header)
                val_file.writelines(data_lines[train_lines + test_lines:])
    except FileNotFoundError:
        print(f"文件 {input_csv} 未找到")
    except Exception as e:
        print(f"划分数据集时出现错误: {e}")

def main():
    input_csv = "/root/KG/DeepKE/example/re/standard/optimized_relations.csv"
    train_csv = "/root/KG/DeepKE/example/re/standard/data/origin/train.csv"
    test_csv = "/root/KG/DeepKE/example/re/standard/data/origin/test.csv"
    valid_csv = "/root/KG/DeepKE/example/re/standard/data/origin/valid.csv"

    # 先将json转csv（如果需要的话，原代码main中未调用，若需要可添加）
    # json_to_csv(input_json, output_csv)
    
    split_csv(input_csv, train_csv, test_csv, valid_csv)

if __name__ == "__main__":
    main()