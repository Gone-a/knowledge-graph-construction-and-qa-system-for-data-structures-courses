import re

CON = {}
ARI = {}

file_input = "/root/KG/DeepKE/example/ner/prepare-data/vocab_dict.csv"
file_output = "/root/KG/DeepKE/example/ner/prepare-data/vocab_dict.txt"

def load_existing_entities():
    try:
        with open(file_output, "r", encoding='utf-8') as f:
            current_section = None
            for line in f:
                line = line.strip()
                if line == "CON:":
                    current_section = "CON"
                elif line == "ARI:":
                    current_section = "ARI"
                elif current_section and line:
                    if current_section == "CON":
                        CON[line] = 1
                    elif current_section == "ARI":
                        ARI[line] = 1
    except FileNotFoundError:
        pass

def save_new_entity(entity, label):
    # 将新实体追加到 vocab_dict.txt 文件
    with open(file_output, 'a', encoding='utf-8') as f:
        if label == "CON":
            if not CON:
                f.write("CON:\n")
            f.write(f"{entity}\n")
        elif label == "ARI":
            if not ARI:
                f.write("ARI:\n")
            f.write(f"{entity}\n")
    # 将新实体追加到 vocab_dict.csv 文件
    with open(file_input, 'a', encoding='utf-8') as csv_f:
        csv_f.write(f"{entity},{label}\n")

def main():
    # 从 csv 文件加载初始数据
    with open(file_input, "r", encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entity, label = line.split(",")
            if label == "ARI":
                if entity not in ARI:
                    ARI[entity] = 1
            else:
                if entity not in CON:
                    CON[entity] = 1

    # 从输出文件加载已有的实体
    load_existing_entities()

    while True:
        print("请输入要加入的实体:")
        entity = input().strip()
        if entity == 'q':
            break
        if not entity:
            continue
        # 使用正则表达式判断是否只包含英文字母
        if re.match(r'^[a-zA-Z]+$', entity):
            print("不要输入英文")
            continue

        print("请输入实体类型(CON:1/ARI:2):")
        label = input().strip().upper()
        if label == "1":
            label = "CON"
            if entity in CON:
                print("(CON)实体已存在")
            else:
                CON[entity] = 1
                save_new_entity(entity, label)
        elif label == "2":
            label = "ARI"
            if entity in ARI:
                print("(ARI)实体已存在")
            else:
                ARI[entity] = 1
                save_new_entity(entity, label)
        else:
            print("无效的实体类型,请输入1(CON)或2(ARI)")

if __name__ == "__main__":
    main()
        

        