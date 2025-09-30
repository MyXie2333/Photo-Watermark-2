import sys
import io

# 添加src目录到路径
sys.path.insert(0, 'src')

# 读取并执行main.py
with io.open('src/main.py', 'r', encoding='utf-8') as f:
    code = f.read()
    exec(code)