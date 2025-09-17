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
import threading
import time

class RunServe():
    def __init__(self):
        self.vue_process = None
        
    def start_vue_async(self):
        """异步启动Vue服务"""
        def run_vue():
            original_dir = os.getcwd()
            try:
                vue_dir = os.path.join(original_dir, 'Vue')
                os.chdir(vue_dir)
                self.vue_process = subprocess.Popen(["npm", "run", "serve"])
                self.vue_process.wait()
            except Exception as e:
                print(f"Vue服务启动失败: {e}")
            finally:
                os.chdir(original_dir)
        
        vue_thread = threading.Thread(target=run_vue, daemon=True)
        vue_thread.start()
        # 给Vue一些时间启动
        time.sleep(2)
    
    @contextlib.contextmanager
    def run(self, str):
        """临时切换目录的上下文管理器"""
        original_dir = os.getcwd()
        try:
            if str == 'neo4j':
                new_dir = os.path.join(os.path.expandvars("$NEO4J_HOME"), "bin")
                os.chdir(new_dir)
                subprocess.run(["neo4j", "restart"])
                yield
            
            elif str == 'Vue':  
                # 异步启动Vue服务，不阻塞主程序
                self.start_vue_async()
                yield
            
            else:
                raise ValueError('输入错误')
        
        finally:
            os.chdir(original_dir)