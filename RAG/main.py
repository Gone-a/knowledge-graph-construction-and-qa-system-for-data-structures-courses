from py2neo import Graph
from transformers import pipeline
import os

class DSAGraphQA:
    def __init__(self,neo4j_uri,username,password):
        """初始化图数据库连接和NLP模型"""
        #1.连接Neo4j数据库
        self.graph=Graph(neo4j_uri, auth=(username, password))
        self.relation_dict={
            "rely":"依赖",
            "b-rely":"被依赖",
            "belg":"包含",
            "b-belg":"属于",
            "syno":"同义",
            "relative":"相对",
            "attr":"拥有",
            "b-attr":"属性",
            "none":"无"
        }

    def query_graph(self,question,entities):
        """核心查询流程"""
        #1.构建Cypher查询语句
        query=self._build_cypher_query(entities)
        print(f"执行查询: {query}")

        #2.执行查询并过滤低置信度结果
        results=self.graph.run(query).data()
        valid_results=[r for r in results if r['confidence'] > 0.7]

        #将关系类型转换为中文
        for r in valid_results:
            r['relation']=self.relation_dict.get(r['relation'],"未知")

        #3.构造结构化输出
        return self._format_results(question,valid_results)

    def _build_cypher_query(self,entities):
        """构造Cypher查询语句（自动适配实体）"""
        # 示例查询：检索实体及关系路径
        return f"""
        MATCH path=(src)-[r]->(dst)
        WHERE src.name IN {entities} OR dst.name IN {entities}
        RETURN 
          src.name AS source, 
          type(r) AS relation, 
          dst.name AS target,
          r.confidence AS confidence,
          r.source_sentence AS source_sentence
        
        """  # 基础查询模板[1,4](@ref)

    def _format_results(self, question, results):
        """生成带溯源信息的回答"""
        if not results:
            return {"answer":"暂无可靠知识支持","trace":[]}

        #1.生成核心答案
        main_answer=f"{results[0]['source']} → {results[0]['relation']} → {results[0]['target']}"

        #2.构造溯源信息
        trace_info=[]
        for r in results:
            trace_info.append({
                "path": f"{r['source']} → {r['relation']} → {r['target']}",
                "confidence": r['confidence'],
                "source_sentence": r['source_sentence']
            })
        
        return {
            "question":question,
            "answer":main_answer,
            "knowledge_trace":trace_info
        }


def test(qa_system,question = "二叉树和完全二叉树有什么关系？",entities = ["二叉树", "完全二叉树"]):
    result = qa_system.query_graph(question,entities)
    
    print("\n===== 问答结果 =====")
    print(f"问题：{result['question']}")
    print(f"答案：{result['answer']}")
    print("溯源信息：")
    for i, trace in enumerate(result['knowledge_trace']):
        print(f"{i+1}. {trace['path']} (置信度: {trace['confidence']:.0%})")
        print(f"   来源：『{trace['source_sentence']}』")


def main():
    qa_system = DSAGraphQA(
        neo4j_uri="bolt://localhost:7687",
        username="neo4j",
        password=os.getenv("NEO4J_KEY")
    )
    test(qa_system=qa_system)
    

if __name__=="__main__":
    main()