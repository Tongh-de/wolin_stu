import sys
sys.path.insert(0, 'c:/Users/Windows/wolin-student')

try:
    from services.rag_complete import router
    print('✅ RAG模块加载成功')
except Exception as e:
    print(f'❌ RAG模块加载失败: {e}')
    import traceback
    traceback.print_exc()
