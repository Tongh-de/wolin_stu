from pymilvus import connections, utility

MILVUS_HOST = "192.168.184.128"
MILVUS_PORT = 19530

try:
    print(f"正在连接 Milvus ({MILVUS_HOST}:{MILVUS_PORT})...")
    connections.connect(host=MILVUS_HOST, port=MILVUS_PORT, timeout=10)
    print("✓ Milvus 连接成功!")

    # 检查 collections
    collections = utility.list_collections()
    print(f"现有 collections: {collections}")

    # 检查 rag_knowledge collection
    COLLECTION_NAME = "rag_knowledge"
    if COLLECTION_NAME in collections:
        from pymilvus import Collection
        collection = Collection(COLLECTION_NAME)
        collection.load()
        stats = collection.num_entities
        print(f"✓ '{COLLECTION_NAME}' collection 包含 {stats} 条记录")
    else:
        print(f"⚠ '{COLLECTION_NAME}' collection 不存在，需要先上传文档")

    connections.disconnect(alias='default')
    print("\nMilvus 服务正常!")

except Exception as e:
    print(f"✗ Milvus 连接失败: {e}")
