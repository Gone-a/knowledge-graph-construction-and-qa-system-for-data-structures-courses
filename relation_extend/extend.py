import argparse
import os
import json
from typing import List

from knowledge_graph_builder import KnowledgeGraphBuilder
from prepare import cprint as ct

def arg_parser():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='知识图谱关系拓展')
    parser.add_argument('--project', type=str, default='test_project', help='项目名称')
    parser.add_argument('--gpu', type=int, default=0, help='GPU设备号')
    parser.add_argument('--max_iterations', type=int, default=5, help='最大迭代次数')
    parser.add_argument('--convergence_threshold', type=float, default=0.1, help='收敛阈值')
    parser.add_argument('--resume', type=str, help='从保存的状态继续')
    parser.add_argument('--data_dir', type=str, default='data', help='数据目录路径')
    parser.add_argument('--csv_path', type=str, default='/root/KG/relation_extend/data/predictions.csv', help='预测结果CSV文件路径')
    parser.add_argument('--enable_ner', action='store_true', default=True, help='启用NER实体提取增强')
    parser.add_argument('--confidence_threshold', type=float, default=0.7, help='关系预测置信度阈值')
    parser.add_argument('--iterations', type=int, help='迭代次数（与max_iterations同义）')
    
    return parser.parse_args()

def iterative_build(kg_builder: KnowledgeGraphBuilder, max_iterations: int = 5, convergence_threshold: float = 0.1) -> List[str]:
    """
    迭代构建知识图谱
    
    Args:
        kg_builder: 知识图谱构建器实例
        max_iterations: 最大迭代次数
        convergence_threshold: 收敛阈值
    
    Returns:
        每次迭代生成的知识图谱文件路径列表
    """
    print(f"开始迭代构建知识图谱，最大迭代次数: {max_iterations}, 收敛阈值: {convergence_threshold}")
    
    # 首先构建基础知识图谱
    if not os.path.exists(kg_builder.refined_kg_path):
        print("构建基础知识图谱...")
        kg_builder.get_base_kg_from_csv()
    
    iteration_paths = []
    consecutive_low_growth = 0  # 连续低增长次数
    min_growth_threshold = 0.05  # 最小增长阈值
    
    for i in range(max_iterations):
        print(f"\n=== 第 {i+1} 次迭代 ===")
        
        # 运行一次迭代
        new_relations_count = kg_builder.run_iteration()
        
        # 记录当前迭代的输出路径
        current_path = kg_builder.kg_paths[-1]
        iteration_paths.append(current_path)
        
        # 检查是否收敛
        extend_ratio = kg_builder.extend_ratio()
        print(f"扩展比例: {extend_ratio:.4f}")
        
        # 多重收敛条件
        converged = False
        
        # 条件1: 扩展比例低于阈值
        if extend_ratio < convergence_threshold:
            print(f"扩展比例 {extend_ratio:.4f} 小于阈值 {convergence_threshold}")
            converged = True
        
        # 条件2: 新增关系数为0
        if new_relations_count == 0:
            print("本次迭代未发现新关系")
            converged = True
        
        # 条件3: 连续多次低增长
        if extend_ratio < min_growth_threshold:
            consecutive_low_growth += 1
            print(f"连续低增长次数: {consecutive_low_growth}")
            if consecutive_low_growth >= 2:
                print(f"连续 {consecutive_low_growth} 次低增长，停止迭代")
                converged = True
        else:
            consecutive_low_growth = 0
        
        if converged:
            print("迭代收敛，停止构建")
            break
        
        # 输出质量统计
        _print_iteration_quality_stats(kg_builder, current_path)
    
    print(f"\n迭代完成，共进行了 {len(iteration_paths)} 次迭代")
    _print_final_stats(kg_builder, iteration_paths)
    return iteration_paths

def _print_iteration_quality_stats(kg_builder, current_path):
    """
    打印当前迭代的质量统计信息
    """
    try:
        with open(current_path, 'r', encoding='utf-8') as f:
            total_relations = 0
            high_confidence_relations = 0
            new_relations = 0
            avg_confidences = []
            
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    relations = item.get('relationMentions', [])
                    total_relations += len(relations)
                    new_relations += item.get('new_relations_count', 0)
                    
                    for rel in relations:
                        confidence = rel.get('confidence', 0.0)
                        if confidence >= 0.8:
                            high_confidence_relations += 1
                        avg_confidences.append(confidence)
            
            overall_avg_confidence = sum(avg_confidences) / len(avg_confidences) if avg_confidences else 0.0
            high_confidence_ratio = high_confidence_relations / total_relations if total_relations > 0 else 0.0
            
            print(ct.blue(f"质量统计 - 总关系数: {total_relations}, 新增: {new_relations}, 高置信度比例: {high_confidence_ratio:.2%}, 平均置信度: {overall_avg_confidence:.3f}"))
    except Exception as e:
        print(ct.yellow(f"质量统计失败: {e}"))

def _print_final_stats(kg_builder, iteration_paths):
    """
    打印最终统计信息
    """
    print(ct.green("\n=== 最终统计 ==="))
    
    if not iteration_paths:
        print(ct.yellow("没有进行任何迭代"))
        return
    
    try:
        # 统计最终结果
        final_path = iteration_paths[-1]
        with open(final_path, 'r', encoding='utf-8') as f:
            total_sentences = 0
            total_relations = 0
            total_new_relations = 0
            confidence_distribution = {'high': 0, 'medium': 0, 'low': 0}
            
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    total_sentences += 1
                    relations = item.get('relationMentions', [])
                    total_relations += len(relations)
                    total_new_relations += item.get('new_relations_count', 0)
                    
                    for rel in relations:
                        confidence = rel.get('confidence', 0.0)
                        if confidence >= 0.8:
                            confidence_distribution['high'] += 1
                        elif confidence >= 0.6:
                            confidence_distribution['medium'] += 1
                        else:
                            confidence_distribution['low'] += 1
        
        print(ct.blue(f"处理句子数: {total_sentences}"))
        print(ct.blue(f"总关系数: {total_relations}"))
        print(ct.blue(f"新增关系数: {total_new_relations}"))
        print(ct.blue(f"置信度分布 - 高(≥0.8): {confidence_distribution['high']}, 中(0.6-0.8): {confidence_distribution['medium']}, 低(<0.6): {confidence_distribution['low']}"))
        
        # 计算总体扩展效果
        if len(iteration_paths) > 0:
            expansion_rate = total_new_relations / (total_relations - total_new_relations) if total_relations > total_new_relations else 0
            print(ct.green(f"总体扩展率: {expansion_rate:.2%}"))
        
    except Exception as e:
        print(ct.red(f"最终统计失败: {e}"))

def main():
    """主函数"""
    args = arg_parser()
    
    # 处理iterations参数的兼容性
    if args.iterations is not None:
        args.max_iterations = args.iterations
    
    # 创建知识图谱构建器
    kg_builder = KnowledgeGraphBuilder(args)
    
    # 如果指定了resume参数，从保存的状态继续
    if args.resume:
        print(f"从保存的状态继续: {args.resume}")
        kg_builder.load(args.resume)
    
    # 迭代构建知识图谱
    iteration_paths = iterative_build(
        kg_builder,
        max_iterations=args.max_iterations,
        convergence_threshold=args.convergence_threshold
    )
    
    print("\n=== 构建完成 ===")
    print(f"总共进行了 {len(iteration_paths)} 次迭代")
    for i, path in enumerate(iteration_paths, 1):
        print(f"第 {i} 次迭代结果: {path}")
    
    # 保存最终状态
    final_save_path = os.path.join(kg_builder.data_dir, "final_state.json")
    kg_builder.save(final_save_path)
    print(f"最终状态已保存到: {final_save_path}")

if __name__ == "__main__":
    main()
