# -*- coding: utf-8 -*-
import os
os.environ['GRPC_SSL_CIPHERS'] = 'ECDHE+AESGCM:ECDHE+RSA+AESGCM:RSA+AESGCM'

from pymilvus import connections, Collection, utility

MILVUS_HOST = "192.168.184.128"
MILVUS_PORT = 19530
COLLECTION_NAME = "rag_knowledge"

try:
    print("Connecting to Milvus...")
    connections.connect(host=MILVUS_HOST, port=MILVUS_PORT, timeout=30)
    print("Connected!")

    # 检查 collection 是否存在
    collections = utility.list_collections()
    print("Collections: {}".format(collections))

    if COLLECTION_NAME in collections:
        collection = Collection(COLLECTION_NAME)

        # 检查加载状态
        print("Collection '{}' exists".format(COLLECTION_NAME))

        # 尝试获取实体数量
        try:
            stats = collection.num_entities
            print("Entities count: {}".format(stats))
        except Exception as e:
            print("Error getting entities: {}".format(e))

        # 检查索引
        indexes = collection.indexes
        print("Indexes: {}".format(indexes))

        # 加载 collection
        print("Loading collection...")
        collection.load()

        # 等待加载完成 (Milvus 2.x)
        utility.wait_for_loading_complete(COLLECTION_NAME, timeout=30)
        print("Collection loaded!")

        # 测试查询
        from langchain_huggingface import HuggingFaceEmbeddings
        print("Loading embeddings model...")
        embeddings = HuggingFaceEmbeddings(
            model_name="BAAI/bge-m3",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
        print("Model loaded!")

        query = "红楼梦"
        print("Embedding query: {}".format(query))
        query_vector = embeddings.embed_query(query)
        print("Query vector length: {}".format(len(query_vector)))

        # 搜索
        search_params = {"metric_type": "L2", "params": {"nprobe": 10}}
        results = collection.search(
            data=[query_vector],
            anns_field="vector",
            param=search_params,
            limit=3,
            output_fields=["filename", "category", "text"]
        )

        print("\nSearch results:")
        for i, hits in enumerate(results):
            print("  Hit {}: {} results".format(i, len(hits)))
            for j, hit in enumerate(hits):
                text = hit.entity.get("text", "")[:100]
                print("    [{}] Score: {:.4f}, Text: {}...".format(j, hit.distance, text))

    else:
        print("Collection '{}' not found!".format(COLLECTION_NAME))

    connections.disconnect(alias='default')
    print("\nDone!")

except Exception as e:
    import traceback
    print("ERROR: {}".format(e))
    traceback.print_exc()
