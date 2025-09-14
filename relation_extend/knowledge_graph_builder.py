import os
import json
import pandas as pd

class KnowledgeGraphBuilder:
    def __init__(self, args) -> None:
        """知识图谱构建器"""
        self.data_dir = os.path.join("data", args.project)
        self.predictions_csv = getattr(args, 'csv_path', os.path.join(self.data_dir, "predictions.csv"))
        self.base_kg_path = os.path.join(self.data_dir, "base.json")
        self.refined_kg_path = os.path.join(self.data_dir, "base_refined.json")
        
        self.version = 0
        self.kg_paths = []
        
        os.makedirs(self.data_dir, exist_ok=True)
    
    def load_predictions_from_csv(self):
        """从predictions.csv文件加载预测结果并转换为知识图谱格式"""
        df = pd.read_csv(self.predictions_csv)
        df = df[df['relation'] != 'none']
        
        kg_data = []
        sentence_groups = df.groupby('sentence')
        
        item_id = 0
        for sentence, group in sentence_groups:
            relations = []
            for _, row in group.iterrows():
                relation = {
                    "em1Text": row['head'],
                    "em2Text": row['tail'], 
                    "label": row['relation'],
                    "confidence": float(row.get('confidence', 0.0))
                }
                relations.append(relation)
            
            if relations:
                item = {
                    "id": item_id,
                    "sentText": sentence,
                    "relationMentions": relations
                }
                kg_data.append(item)
                item_id += 1
        
        return kg_data
    
    def get_base_kg_from_csv(self):
        """从CSV文件构建基础知识图谱"""
        kg_data = self.load_predictions_from_csv()
        
        with open(self.base_kg_path, 'w', encoding='utf-8') as f:
            for item in kg_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        with open(self.refined_kg_path, 'w', encoding='utf-8') as f:
            for item in kg_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    def run_iteration(self):
        """
        运行一次迭代：基于现有知识图谱扩展新的关系
        """
        print(ct.green("Start Running Iteration."), ct.yellow(f"Version:{self.version}"))
        
        # 如果是第一次迭代，直接读取refined_kg_path
        cur_data_path = self.kg_paths[-1] if self.version > 0 else self.refined_kg_path
        cur_out_path = os.path.join(self.data_dir, f"iteration_version_{self.version}.json")
        
        print(ct.green("Current Data Path:"), ct.yellow(cur_data_path))
        print(ct.green("Output Path:"), ct.yellow(cur_out_path))
        
        # 读取现有数据
        existing_data = []
        if os.path.exists(cur_data_path):
            with open(cur_data_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        existing_data.append(json.loads(line))
        
        # 扩展知识图谱
        extended_data = self._extend_knowledge_graph(existing_data)
        
        # 写入输出文件
        with open(cur_out_path, 'w', encoding='utf-8') as f:
            for item in extended_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        
        self.kg_paths.append(cur_out_path)
        self.save()
        
        # 统计扩展效果
        original_relations = sum(len(item.get('relationMentions', [])) for item in existing_data)
        extended_relations = sum(len(item.get('relationMentions', [])) for item in extended_data)
        new_relations = extended_relations - original_relations
        
        print(ct.green(f"Iteration {self.version} completed. Output: {cur_out_path}"))
        print(ct.blue(f"原有关系数: {original_relations}, 扩展后关系数: {extended_relations}, 新增关系数: {new_relations}"))
        
        self.version += 1
        
        return new_relations
    
    def _extend_knowledge_graph(self, existing_data):
        """
        扩展知识图谱：基于现有实体发现新的关系
        """
        print(ct.blue("开始扩展知识图谱..."))
        
        # 如果没有启用NER和关系预测，直接返回原数据
        if not self.enable_ner or not self.ner_extractor or not self.relation_predictor:
            print(ct.yellow("NER或关系预测器未启用，跳过扩展"))
            return existing_data
        
        extended_data = []
        
        # 收集所有已知实体
        all_entities = set()
        for item in existing_data:
            for relation in item.get('relationMentions', []):
                all_entities.add(relation['em1Text'])
                all_entities.add(relation['em2Text'])
        
        print(ct.blue(f"已知实体数量: {len(all_entities)}"))
        
        for item in existing_data:
            sentence = item['sentText']
            existing_relations = item.get('relationMentions', [])
            
            # 使用NER提取句子中的所有实体
            sentence_entities = self.ner_extractor.extract_entities_from_text(sentence)
            
            # 生成新的实体对组合
            new_relations = []
            existing_pairs = set()
            
            # 记录已存在的实体对
            for rel in existing_relations:
                existing_pairs.add((rel['em1Text'], rel['em2Text']))
                existing_pairs.add((rel['em2Text'], rel['em1Text']))
            
            # 尝试发现新的关系
            for i, entity1 in enumerate(sentence_entities):
                for j, entity2 in enumerate(sentence_entities):
                    if i != j:
                        e1_text = entity1['text']
                        e2_text = entity2['text']
                        
                        # 跳过已存在的实体对
                        if (e1_text, e2_text) in existing_pairs:
                            continue
                        
                        # 预测关系
                        result = self.relation_predictor.predict_relation_for_pair(
                            sentence, e1_text, e2_text
                        )
                        
                        predicted_relation = result.get('relation', 'none')
                        confidence = result.get('confidence', 0.0)
                        
                        # 只保留置信度高于阈值且不是'none'的关系
                        if (confidence >= self.relation_predictor.confidence_threshold and 
                            predicted_relation != 'none'):
                            
                            new_relation = {
                                "em1Text": e1_text,
                                "em2Text": e2_text,
                                "label": predicted_relation,
                                "confidence": confidence,
                                "head_type": entity1.get('label', 'UNK'),
                                "tail_type": entity2.get('label', 'UNK'),
                                "is_new": True  # 标记为新发现的关系
                            }
                            new_relations.append(new_relation)
                            existing_pairs.add((e1_text, e2_text))
            
            # 合并原有关系和新关系
            all_relations = existing_relations + new_relations
            
            # 按置信度排序
            all_relations.sort(key=lambda x: x.get('confidence', 0.0), reverse=True)
            
            # 更新平均置信度
            avg_confidence = (sum(r.get('confidence', 0.0) for r in all_relations) / len(all_relations) 
                            if all_relations else 0.0)
            
            extended_item = {
                "id": item['id'],
                "sentText": sentence,
                "relationMentions": all_relations,
                "avg_confidence": avg_confidence,
                "new_relations_count": len(new_relations)
            }
            
            extended_data.append(extended_item)
        
        total_new_relations = sum(item.get('new_relations_count', 0) for item in extended_data)
        print(ct.green(f"扩展完成，新增 {total_new_relations} 个关系"))
        
        return extended_data
    
    def extend_ratio(self):
        """
        计算扩展比例：(新增关系数) / (原有关系数)
        """
        if self.version < 2 or len(self.kg_paths) < 2:
            return 1.0
        
        # 获取前一次和当前的知识图谱文件
        prev_kg_path = self.kg_paths[-2]
        curr_kg_path = self.kg_paths[-1]
        
        # 统计前一次的关系数量
        prev_relations = 0
        if os.path.exists(prev_kg_path):
            with open(prev_kg_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        item = json.loads(line)
                        prev_relations += len(item.get('relationMentions', []))
        
        # 统计当前的关系数量
        curr_relations = 0
        new_relations_count = 0
        if os.path.exists(curr_kg_path):
            with open(curr_kg_path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        item = json.loads(line)
                        curr_relations += len(item.get('relationMentions', []))
                        new_relations_count += item.get('new_relations_count', 0)
        
        # 计算扩展比例
        if prev_relations == 0:
            return 1.0
        
        ratio = new_relations_count / prev_relations
        
        print(ct.blue(f"扩展统计 - 前次关系数: {prev_relations}, 当前关系数: {curr_relations}, 新增关系数: {new_relations_count}, 扩展比例: {ratio:.4f}"))
        
        return max(0.0, ratio)  # 确保比例不为负数
    
    def save(self, save_path=None):
        """
        保存当前状态
        """
        if save_path is None:
            timestr = time.strftime("%Y%m%d-%H%M%S")
            history_dir = os.path.join(self.data_dir, "history")
            os.makedirs(history_dir, exist_ok=True)
            save_path = os.path.join(history_dir, f"{timestr}_iter_v{self.version}")
        
        # 创建可序列化的状态字典，排除NER提取器和关系预测器
        state_dict = {k: v for k, v in self.__dict__.items() if k not in ['ner_extractor', 'relation_predictor']}
        
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(state_dict, f, ensure_ascii=False, indent=4)
        
        print(f"保存状态至{save_path}")
        print(ct.blue(f"当前版本:{self.version}"))
        print("你可以使用", ct.green(f"--resume {save_path}"), ct.blue("来继续迭代"))
    
    def load(self, load_path=None):
        """
        加载状态
        """
        if load_path is None:
            raise ValueError("load_path 不能为空")
        with open(load_path, "r", encoding="utf-8") as f:
            state = json.load(f)
        self.__dict__.update(state)

