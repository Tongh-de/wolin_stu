from pymilvus import connections, utility
import os
from dotenv import load_dotenv

load_dotenv()

MILVUS_HOST = os.getenv("MILVUS_HOST", "localhost")
MILVUS_PORT = int(os.getenv("MILVUS_PORT", "19530"))

try:
    connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)
    print(f"Milvus 服务连接成功! ({MILVUS_HOST}:{MILVUS_PORT})")
    
    # 列出所有 collections
    collections = utility.list_collections()
    print(f"当前 collections: {collections}")
    
    connections.disconnect('default')
except Exception as e:
    print(f"Milvus 连接失败: {e}")
