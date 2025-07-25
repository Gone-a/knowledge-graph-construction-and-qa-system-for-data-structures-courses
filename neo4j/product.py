from py2neo import Graph, Node, Relationship
import os
import pandas as pd
import re
from tqdm import tqdm

class Neo4jKnowledgeGraph:
    def __init__(self):
        """初始化Neo4j图数据库连接"""
        # 获取当前文件所在目录
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_path = os.path.join(cur_dir, "data")
        
        # Neo4j连接配置
        self.graph = Graph("bolt://localhost:7687", auth=("neo4j", "055625540"))
        
        # 加载实体类型映射表
        self.entity_type_map = self.load_entity_types("/root/KG/DeepKE/example/ner/prepare-data/vocab_dict.csv")
        print("✅ Neo4j图数据库连接成功")

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
        
        # 过滤无效关系（只移除none关系）
        return df[df['relation'] != 'none']

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

    def create_relationships(self, df, nodes):
        """创建实体间的关系，使用原始关系名称（包括b-前缀）"""
        print("🔄🔄 正在创建关系...")
        
        tx = self.graph.begin()
        relationship_types = set()
        
        for _, row in tqdm(df.iterrows(), total=len(df), desc="创建关系"):
            source = nodes.get(row['head_clean'])
            target = nodes.get(row['tail_clean'])
            
            if not source or not target:
                continue
                
            # 创建关系，使用原始关系名称（包括b-前缀）
            rel_type = row['relation']
            relationship = Relationship(source, rel_type, target, 
                                      confidence=row['confidence'],
                                      source_sentence=row['sentence'])
            tx.create(relationship)
            relationship_types.add(rel_type)
        
        self.graph.commit(tx)
        print(f"✅ 成功创建 {len(df)} 个关系，包含 {len(relationship_types)} 种关系类型")
        
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

    def build_knowledge_graph(self):
        """构建知识图谱主流程"""
        # 彻底清理数据库
        self.clean_database()
        
        # 加载和处理数据
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
    kg_builder = Neo4jKnowledgeGraph()
    kg_builder.build_knowledge_graph()