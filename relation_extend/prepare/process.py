import os
#from data.schema import schema_v4

# os.environ["CUDA_VISIBLE_DEVICES"] = '1'
# UIE和PaddlePaddle相关功能已被移除
# 所有关系抽取现在直接使用CSV文件

def paddle_relation_ie(content):
    """
    已废弃：原UIE关系抽取功能
    """
    print("UIE功能已被移除，请使用CSV文件进行关系抽取")
    return []

def rel_json(content):
    """
    已废弃：原关系抽取功能
    """
    print("UIE功能已被移除，请使用CSV文件进行关系抽取")
    return []

def uie_execute(texts):
    """
    已废弃：原UIE执行功能
    """
    print("UIE功能已被移除，请使用CSV文件进行关系抽取")
    return []
