# import os

# import subprocess
# def neo4j_restart():
#     neo_path = os.path.join(os.path.expandvars("$NEO4J_HOME"), "bin")

#     if os.path.exists(neo_path):
#         os.chdir(neo_path)
#         subprocess.run(["neo4j", "restart"])

import os
import contextlib
from pathlib import Path

#开启neo4j图知识库或Vue

import os
import contextlib
import subprocess

class RunServe():
    def __init__(self):
        pass
    
    @contextlib.contextmanager
    def run(self,str):
        """临时切换目录的上下文管理器"""
        original_dir = os.getcwd()
        try:
            if str == 'neo4j':
                new_dir = os.path.join(os.path.expandvars("$NEO4J_HOME"), "bin")
                os.chdir(new_dir)
                subprocess.run(["neo4j", "restart"])
                yield
            
            elif str == 'Vue':  
                new_dir = os.path.join('Vue')
                os.chdir(new_dir)
                subprocess.run(["npm", "run", "serve"])
                yield
            
            else:
                raise ValueError('输入错误')
        
        finally:
            os.chdir(original_dir)