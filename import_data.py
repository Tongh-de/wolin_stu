"""
使用 Python 正确导入 SQL 文件（处理 UTF-8 编码）
"""
import re
import pymysql
import sys
import io

# 设置标准输出编码为 UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 数据库配置
DB_CONFIG_NO_DB = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'charset': 'utf8mb4'
}

DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'wolin_test1',
    'charset': 'utf8mb4'
}

# 读取 SQL 文件（使用 UTF-8 编码）
sql_file = 'database_init_test.sql'
with open(sql_file, 'r', encoding='utf-8') as f:
    sql_content = f.read()

def remove_comments(sql):
    """移除 SQL 中的行注释"""
    lines = []
    for line in sql.split('\n'):
        # 找到 -- 注释的位置
        idx = line.find('--')
        if idx >= 0:
            line = line[:idx]
        lines.append(line)
    return '\n'.join(lines)

# 移除行注释
sql_content = remove_comments(sql_content)

# 先连接数据库服务器（不指定数据库）来创建 schema
conn_no_db = pymysql.connect(**DB_CONFIG_NO_DB)
cursor_no_db = conn_no_db.cursor()

try:
    # 使用正则分割语句（以分号+换行分割）
    statements = re.split(r';\s*\n', sql_content)

    # 第一阶段：执行需要数据库服务器的语句（创建schema等）
    phase1_stmts = []
    phase2_stmts = []
    
    for stmt in statements:
        stmt = stmt.strip()
        if not stmt:
            continue
            
        stmt_upper = stmt.upper()
        if 'CREATE SCHEMA' in stmt_upper or 'DROP SCHEMA' in stmt_upper:
            phase1_stmts.append(stmt)
        elif 'USE ' in stmt_upper:
            phase1_stmts.append(stmt)
        else:
            phase2_stmts.append(stmt)

    # 执行第一阶段语句
    success_count = 0
    fail_count = 0
    
    for stmt in phase1_stmts:
        try:
            cursor_no_db.execute(stmt)
            conn_no_db.commit()
            success_count += 1
            preview = stmt[:60].replace('\n', ' ')
            print(f"[OK] {preview}...")
        except Exception as e:
            fail_count += 1
            preview = stmt[:60].replace('\n', ' ')
            print(f"[FAIL] {preview}... | Error: {str(e)[:100]}")

    cursor_no_db.close()
    conn_no_db.close()

    # 第二阶段：连接数据库执行其他语句
    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    for stmt in phase2_stmts:
        stmt = stmt.strip()
        if not stmt:
            continue
            
        try:
            cursor.execute(stmt)
            conn.commit()
            success_count += 1
            preview = stmt[:60].replace('\n', ' ')
            print(f"[OK] {preview}...")
        except Exception as e:
            fail_count += 1
            preview = stmt[:60].replace('\n', ' ')
            print(f"[FAIL] {preview}... | Error: {str(e)[:100]}")

    print(f"\nDone! Success: {success_count}, Failed: {fail_count}")

except Exception as e:
    print(f"Critical error: {e}")
    import traceback
    traceback.print_exc()
finally:
    try:
        cursor.close()
        conn.close()
    except:
        pass
