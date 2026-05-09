from pymilvus import connections
print('开始连接 Milvus...')
connections.connect(host='192.168.184.128', port='19530', timeout=10)
print('Milvus连接成功')
