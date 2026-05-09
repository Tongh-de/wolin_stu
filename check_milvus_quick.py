# -*- coding: utf-8 -*-
import os
os.environ['GRPC_SSL_CIPHERS'] = 'ECDHE+AESGCM:ECDHE+RSA+AESGCM:RSA+AESGCM'

from pymilvus import connections

MILVUS_HOST = "192.168.184.128"
MILVUS_PORT = 19530

try:
    print("Connecting to Milvus at {}:{}...".format(MILVUS_HOST, MILVUS_PORT))
    connections.connect(host=MILVUS_HOST, port=MILVUS_PORT, timeout=10)
    print("SUCCESS: Milvus connected!")

    from pymilvus import utility
    collections = utility.list_collections()
    print("Collections: {}".format(collections))

    connections.disconnect(alias='default')
except Exception as e:
    print("FAIL: {}".format(e))
