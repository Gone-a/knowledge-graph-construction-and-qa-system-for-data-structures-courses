from py2neo import Graph, Node, Relationship
import os
import pandas as pd
import re
import json
from tqdm import tqdm

class Neo4jKnowledgeGraph:
    def __init__(self, uri="bolt://localhost:7687", user="neo4j", password="123456",confidence=0.82):
        self.confidence=confidence
        """初始化Neo4j图数据库连接
        
        Args:
            uri (str): Neo4j数据库URI
            user (str): 用户名
            password (str): 密码
        """
        # 获取当前文件所在目录
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_path = os.path.join(cur_dir, "data")
        
        # Neo4j连接配置
        try:
            #从环境变量获取连接信息
            password = os.getenv("NEO4J_KEY", password)
            self.graph = Graph(uri, auth=(user, password))
            # 测试连接
            self.graph.run("RETURN 1")
            print("✅ Neo4j图数据库连接成功")
        except Exception as e:
            print(f"❌ Neo4j连接失败: {e}")
            raise e
        
        # 加载实体类型映射表
        vocab_path = "/root/KG/DeepKE/example/ner/prepare-data/vocab_dict.csv"
        if os.path.exists(vocab_path):
            self.entity_type_map = self.load_entity_types(vocab_path)
        else:
            print(f"⚠️ 词汇表文件不存在: {vocab_path}，使用默认实体类型")
            self.entity_type_map = {}

        self.relation_dict={
            "rely":"依赖",
            "b-rely":"被依赖",
            "belg":"包含",
            "b-belg":"被包含",
            "syno":"同义",
            "relative":"相对",
            "attr":"拥有",
            "b-attr":"属性",
            "none":"无"
        }

    def clean_database(self):
        """彻底清理数据库：删除所有节点、关系和标签定义"""
        try:
            # 先删除所有索引和约束（解决索引已存在的问题）
            self.graph.run("DROP CONSTRAINT entity_name_unique IF EXISTS")
            self.graph.run("DROP INDEX entity_name_index IF EXISTS")
            self.graph.run("DROP INDEX entity_type_index IF EXISTS")
            
            # 删除所有节点和关系
            self.graph.run("MATCH (n) DETACH DELETE n")
            print("🧹🧹 数据库已彻底清理")
        except Exception as e:
            print(f"清理数据库时出错: {e}")
            # 备选方案：如果删除索引失败，只删除节点
            print("⚠️ 尝试备选清理方案...")
            self.graph.run("MATCH (n) DETACH DELETE n")

    def load_entity_types(self, vocab_path):
        """加载实体类型映射表"""
        entity_type_map = {}
        with open(vocab_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 2:
                    entity = parts[0].strip()
                    entity_type = parts[1].strip()
                    entity_type_map[entity] = entity_type
        return entity_type_map

    def normalize_entity(self, entity):
        """标准化实体名称，提取核心术语"""
        # 检查输入是否为空或None
        if not entity or not str(entity).strip():
            return None
            
        # 移除描述性文本和特殊字符
        patterns = [
            r'是[\u4e00-\u9fa5]+的[\u4e00-\u9fa5]+',
            r'指[\u4e00-\u9fa5]+',
            r'通过[\u4e00-\u9fa5]+',
            r'利用[\u4e00-\u9fa5]+',
            r'从[\u4e00-\u9fa5]+'
        ]
        
        for pattern in patterns:
            entity = re.sub(pattern, '', entity)
        
        # 移除特殊字符和多余空格
        entity = re.sub(r'[^\w\u4e00-\u9fa5]+', ' ', entity).strip()
        entity = re.sub(r'\s+', ' ', entity)
        
        # 如果处理后为空字符串，返回None
        if not entity or len(entity.strip()) == 0:
            return None
            
        return entity

    def get_entity_type(self, entity):
        """根据实体名称获取类型"""
        # 检查是否在词汇表中
        if entity in self.entity_type_map:
            return self.entity_type_map[entity]
        
        # 如果不在词汇表中，根据名称特征判断
        if '排序' in entity or '查找' in entity or '搜索' in entity or '算法' in entity:
            return "ARI"
        return "CON"

    def load_data(self):
        """加载并处理CSV数据，保留原始关系名称（包括b-前缀）"""
        file_path = os.path.join(self.data_path, "predictions.csv")
        df = pd.read_csv(file_path)
        
        # 实体标准化
        df['head_clean'] = df['head'].apply(self.normalize_entity)
        df['tail_clean'] = df['tail'].apply(self.normalize_entity)
        
        # 过滤无效关系：移除none关系和包含空实体的记录
        df_filtered = df[
            (df['relation'] != 'none') & 
            (df['head_clean'].notna()) & 
            (df['tail_clean'].notna()) &
            (df['head_clean'] != '') &
            (df['tail_clean'] != '')
        ]
        
        print(f"📊 数据过滤: 原始 {len(df)} 条 -> 有效 {len(df_filtered)} 条")
        return df_filtered
    
    def load_json_data(self, json_file_path):
        """加载并处理JSON格式的知识图谱数据"""
        relations_data = []
        
        print(f"🔄 正在加载JSON文件: {json_file_path}")
        
        with open(json_file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line.strip())
                    sentence = data.get('sentText', '')
                    
                    for relation in data.get('relationMentions', []):
                        head_entity = relation.get('em1Text', '')
                        tail_entity = relation.get('em2Text', '')
                        relation_type = relation.get('label', '')
                        
                        # 实体标准化
                        head_clean = self.normalize_entity(head_entity)
                        tail_clean = self.normalize_entity(tail_entity)
                        
                        # 过滤无效关系
                        if (relation_type != 'none' and 
                            head_clean and tail_clean and 
                            head_clean.strip() and tail_clean.strip()):
                            
                            # 从JSON数据中提取置信度信息
                            confidence = relation.get('confidence', 1.0)
                            
                            relations_data.append({
                                'sentence': sentence,
                                'head': head_entity,
                                'tail': tail_entity,
                                'relation': relation_type,
                                'head_clean': head_clean,
                                'tail_clean': tail_clean,
                                'confidence': confidence  # 使用实际的置信度值
                            })
                            
                except json.JSONDecodeError as e:
                    print(f"⚠️ 第{line_num}行JSON解析错误: {e}")
                    continue
                except Exception as e:
                    print(f"⚠️ 第{line_num}行处理错误: {e}")
                    continue
        
        df = pd.DataFrame(relations_data)
        print(f"📊 JSON数据加载完成: 共 {len(df)} 条有效关系")
        return df

    def create_nodes(self, df):
        """创建所有实体节点"""
        print("🔄🔄 正在创建实体节点...")
        
        # 获取所有唯一实体
        all_entities = set(df['head_clean'].tolist() + df['tail_clean'].tolist())
        
        # 批量创建节点
        tx = self.graph.begin()
        nodes = {}
        
        for entity in tqdm(all_entities, desc="创建节点"):
            # 获取实体类型
            entity_type = self.get_entity_type(entity)
            
            # 创建带标签的节点
            node = Node("Entity", name=entity, type=entity_type)
            nodes[entity] = node
            tx.create(node)
        
        self.graph.commit(tx)
        print(f"✅ 成功创建 {len(nodes)} 个实体节点")
        return nodes

    def deduplicate_relationships(self, df):
        """去除重复关系，按置信度保留最高的关系,并且过滤掉置信度小于0.8的关系"""
        print("🔄🔄 正在去重关系...")
        
        # 过滤掉置信度小于0.8的关系
        df = df[df['confidence'] >= self.confidence].copy()

        #过滤掉头尾实体为空和相同的关系
        df = df[(df['head_clean'].notna()) & (df['tail_clean'].notna()) & (df['head_clean'] != '') & (df['tail_clean'] != '') & (df['head_clean'] != df['tail_clean'])].copy()

        
        # 过滤掉关系为空的关系
        df = df[df['relation'].notna() & (df['relation'] != '')].copy()

        
        # 过滤掉关系为none的关系
        df = df[df['relation'] != 'none'].copy()
        
        
        # 创建关系唯一标识：头实体-尾实体-关系类型
        df['relation_key'] = df['head_clean'] + '|' + df['tail_clean'] + '|' + df['relation']
        
        # 按关系唯一标识分组，保留置信度最高的记录
        df_dedup = df.loc[df.groupby('relation_key')['confidence'].idxmax()]
        
        # 处理互相指向的相同关系类型（A->B 和 B->A 的同类关系），允许不同关系类型的相互指向
        mutual_relations = []
        processed_pairs = set()
        
        for _, row in df_dedup.iterrows():
            head, tail, relation = row['head_clean'], row['tail_clean'], row['relation']
            # 创建包含关系类型的唯一标识，用于识别相同关系类型的互相指向
            pair_key = tuple(sorted([head, tail]) + [relation])
            
            if pair_key in processed_pairs:
                continue
                
            # 查找互相指向的相同关系类型
            reverse_relation = df_dedup[
                (df_dedup['head_clean'] == tail) & 
                (df_dedup['tail_clean'] == head) & 
                (df_dedup['relation'] == relation)
            ]
            
            if not reverse_relation.empty:
                # 存在互相指向的相同关系类型，保留置信度更高的
                current_confidence = row['confidence']
                reverse_confidence = reverse_relation.iloc[0]['confidence']
                
                if current_confidence >= reverse_confidence:
                    mutual_relations.append(row)
                else:
                    mutual_relations.append(reverse_relation.iloc[0])
                    
                processed_pairs.add(pair_key)
            else:
                # 没有互相指向的相同关系类型，直接保留
                mutual_relations.append(row)
        
        result_df = pd.DataFrame(mutual_relations)
        print(f"📊 去重前: {len(df)} 条关系，去重后: {len(result_df)} 条关系")
        return result_df
    
    def create_relationships(self, df, nodes):
        """创建实体间的关系，使用原始关系名称（包括b-前缀）"""
        print("🔄🔄 正在创建关系...")
        
        # 先进行关系去重
        df_dedup = self.deduplicate_relationships(df)
        
        tx = self.graph.begin()
        relationship_types = set()
        
        for _, row in tqdm(df_dedup.iterrows(), total=len(df_dedup), desc="创建关系"):
            source = nodes.get(row['head_clean'])
            target = nodes.get(row['tail_clean'])
            
            if not source or not target:
                continue
                
            # 创建关系，使用中文关系名称
            rel_type = self.relation_dict.get(row['relation'], row['relation'])
            relationship = Relationship(source, rel_type, target, 
                                      confidence=row['confidence'],
                                      source_sentence=row['sentence'])
            tx.create(relationship)
            relationship_types.add(rel_type)
        
        self.graph.commit(tx)
        print(f"✅ 成功创建 {len(df_dedup)} 个关系，包含 {len(relationship_types)} 种关系类型")
        
    def create_indexes(self):
        """创建索引优化查询性能"""
        try:
            # 检查索引是否已存在
            existing_indexes = self.graph.run("SHOW INDEXES").data()
            index_names = [index['name'] for index in existing_indexes]
            
            # 如果索引不存在则创建
            if "entity_name_unique" not in index_names:
                self.graph.run("CREATE CONSTRAINT entity_name_unique FOR (e:Entity) REQUIRE e.name IS UNIQUE")
            
            if "entity_type_index" not in index_names:
                self.graph.run("CREATE INDEX entity_type_index FOR (e:Entity) ON (e.type)")
            
            print("✅ 索引创建完成")
        except Exception as e:
            print(f"创建索引时出错: {e}")
            # 尝试创建索引而不检查（作为备选方案）
            try:
                self.graph.run("CREATE CONSTRAINT entity_name_unique IF NOT EXISTS FOR (e:Entity) REQUIRE e.name IS UNIQUE")
                self.graph.run("CREATE INDEX entity_type_index IF NOT EXISTS FOR (e:Entity) ON (e.type)")
                print("✅ 备选方案索引创建完成")
            except Exception as e2:
                print(f"备选方案创建索引时出错: {e2}")

    def build_knowledge_graph(self, data_source='csv', json_file_path=None, csv_file_path=None):
        """
        构建知识图谱
        
        Args:
            data_source (str): 数据源类型，'csv' 或 'json'
            json_file_path (str): JSON文件路径（当data_source='json'时必需）
            csv_file_path (str): CSV文件路径（当data_source='csv'且指定文件时必需）
        """
        # 彻底清理数据库
        self.clean_database()
        
        # 根据数据源类型加载数据
        if data_source == 'json':
            if not json_file_path:
                raise ValueError("使用JSON数据源时必须提供json_file_path参数")
            if not os.path.exists(json_file_path):
                raise FileNotFoundError(f"JSON文件不存在: {json_file_path}")
            df = self.load_json_data(json_file_path)
        else:
            if csv_file_path:
                if not os.path.exists(csv_file_path):
                    raise FileNotFoundError(f"CSV文件不存在: {csv_file_path}")
                df = pd.read_csv(csv_file_path)
                # 标准化列名
                if 'head' in df.columns and 'head_clean' not in df.columns:
                    df['head_clean'] = df['head']
                if 'tail' in df.columns and 'tail_clean' not in df.columns:
                    df['tail_clean'] = df['tail']
            else:
                df = self.load_data()
            
        print(f"📊📊 已加载 {len(df)} 条知识记录")
        
        # 创建节点和关系
        nodes = self.create_nodes(df)
        self.create_relationships(df, nodes)
        
        # 创建索引
        self.create_indexes()
        
        # 验证图结构
        try:
            result = self.graph.run("MATCH (n) RETURN count(n) AS node_count").data()
            print(f"📈📈 知识图谱构建完成！包含 {result[0]['node_count']} 个节点")
        except Exception as e:
            print(f"验证图结构时出错: {e}")

if __name__ == "__main__":
    import sys
    
    kg_builder = Neo4jKnowledgeGraph()
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        if sys.argv[1] == '--json' and len(sys.argv) > 2:
            # 使用JSON数据源
            json_file_path = sys.argv[2]
            print(f"🔄 使用JSON数据源: {json_file_path}")
            kg_builder.build_knowledge_graph(data_source='json', json_file_path=json_file_path)
        elif sys.argv[1] == '--csv' and len(sys.argv) > 2:
            # 使用指定的CSV数据源
            csv_file_path = sys.argv[2]
            print(f"🔄 使用CSV数据源: {csv_file_path}")
            kg_builder.build_knowledge_graph(data_source='csv', csv_file_path=csv_file_path)
        else:
            print("用法: python product.py [--json <json_file_path>] [--csv <csv_file_path>]")
            print("示例: python product.py --json /path/to/iteration_version_1.json")
            print("示例: python product.py --csv /path/to/predictions.csv")
    else:
        # 默认使用CSV数据源
        print("🔄 使用默认CSV数据源")
        kg_builder.build_knowledge_graph()