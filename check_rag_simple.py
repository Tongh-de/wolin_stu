from pymilvus import connections, utility

# 连接 Milvus
connections.connect(host="192.168.184.128", port=19530)

# 要删除的集合列表
collections_to_drop = [
    "document_chunks",
    "langchain_docs",
    "sanguo_qa"
]

# 逐个删除
for name in collections_to_drop:
    if utility.has_collection(name):
        utility.drop_collection(name)
        print(f"✅ 已删除集合：{name}")
    else:
        print(f"ℹ️ 集合 {name} 不存在，跳过")

print("\n🎉 所有指定集合已删除，Milvus 已清空！")