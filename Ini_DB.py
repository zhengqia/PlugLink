<<<<<<< HEAD
import sqlite3,os
import pandas as pd
from Ini_sys import get_base_path
from flask_sqlalchemy import SQLAlchemy


"""
本页为所有数据库操作
ini_开头的均用于配置或通用，不要from任何_Actions的文件
"""

# 数据库文件存放路径
DB_DIR = 'DB'
DB_FILE = 'Main.db'
# db_path = os.path.join(DB_DIR, DB_FILE)
db_path = get_base_path('DB\Main.db')

PLUGINS_DB = SQLAlchemy()  # 创建 SQLAlchemy 的实例

"""<路由配置插件数据库信息>"""
def ini_plugins_db(app):
    # 这里设置所有与数据库相关的配置
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'  # 设置数据库 URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    PLUGINS_DB.init_app(app)

#插件列表的类
class Plugins(PLUGINS_DB.Model):
    __tablename__ = 'MyPlugins'  # 明确指定表名
    id = PLUGINS_DB.Column(PLUGINS_DB.Integer, primary_key=True)
    PlugDir = PLUGINS_DB.Column(PLUGINS_DB.String(120))
    PlugName = PLUGINS_DB.Column(PLUGINS_DB.String(120))
    ICO = PLUGINS_DB.Column(PLUGINS_DB.String(120))
    Ver = PLUGINS_DB.Column(PLUGINS_DB.String(20))
    #Developer = PLUGINS_DB.Column(PLUGINS_DB.Boolean)
    author = PLUGINS_DB.Column(PLUGINS_DB.String(120))
    PlugDes = PLUGINS_DB.Column(PLUGINS_DB.String(300))
    PlugHTML = PLUGINS_DB.Column(PLUGINS_DB.String(120))

"""<通用数据库函数>"""
# 查询数据库中的myplugins表中的字段值是否存在
def is_myplugins_DB(field, value):
    """在MyPlugins表中检查指定字段是否有匹配的值"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = f"SELECT COUNT(*) FROM MyPlugins WHERE {field} = ?"
    cursor.execute(query, (value,))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

# 查询指定表和字段的值是否存在，则返回True
def DB_select_return(table_name, column_name, value_name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # 构造查询SQL
    query = f"SELECT 1 FROM {table_name} WHERE {column_name} = ?"
    # 执行查询
    cursor.execute(query, (value_name,))
    result = cursor.fetchone()
    # 关闭数据库连接
    cursor.close()
    conn.close()
    # 如果查询到结果，返回True
    return result is not None


# 通过插件名检测在数据库中是否存在
def is_plugin_registered(plugdir):
    """检查插件是否在数据库中注册"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT EXISTS(SELECT 1 FROM MyPlugins WHERE PlugDir=?)", (plugdir,))
    result = cursor.fetchone()[0]
    conn.close()
    return bool(result)

# 查询 SQLite 数据库中的指定表,并返回数据列表
def query_db(table_name, condition=None):
    """
    查询 SQLite 数据库中的指定表，并可选地应用条件过滤。

    :param table_name: 要查询的表名
    :param condition: 可选的查询条件，格式为 SQL WHERE 子句（不含 'WHERE' 关键词）
    :return: 返回查询结果的列表
    注意：返回值是列表
    用例：
    table_name = 'MyPlugins'
    condition = 'PlugName = "ExamplePlugin"'  # 这里的条件应根据实际需要进行修改
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        query = f"SELECT * FROM {table_name}"
        if condition:
            query += f" WHERE {condition}"
        cursor.execute(query)

        # 获取列标题（字段名）
        columns = [description[0] for description in cursor.description]

        # 获取所有行数据并将其转换为字典列表
        data_list = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return data_list
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return []

#删除SQLite中的指定数据
def delete_data_from_table(table_name, condition):
    """
    删除指定表中满足特定条件的数据。

    参数:
    table_name -- 要删除数据的表名，字符串
    condition -- 完整的WHERE子句，包括字段名和比较操作，字符串

    # 示例使用
    # delete_data_from_table('users', 'email = "user@example.com"')

    返回:
    (success, message) -- 操作成功与否的布尔值和消息字符串

    """
    # 确保表名和条件是有效的
    if not table_name or not condition:
        return False, "表名和条件不能为空。"

    # 构建完整的SQL语句
    sql = f"DELETE FROM {table_name} WHERE {condition};"

    # 连接到数据库
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 执行SQL语句
        cursor.execute(sql)
        # 提交事务
        conn.commit()
        return True, "数据删除成功。"
    except sqlite3.Error as e:
        # 打印错误信息
        print(f"An error occurred: {e}")
        return False, f"数据删除失败: {e}"
    finally:
        # 确保数据库连接被关闭
        if conn:
            conn.close()


# 创建数据库表和字段
def check_and_update_db_structure(conn, table_name, fields):

    #检查并更新数据库结构。
    #如果表不存在，将创建新表。
    #如果表存在但缺少字段，则添加这些字段。

    c = conn.cursor()

    # 检查表是否存在
    c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
    if c.fetchone() is None:
        # 如果表不存在，创建表
        fields_str = ', '.join([f"{name} {type}" for name, type in fields.items()])
        c.execute(f"CREATE TABLE {table_name} ({fields_str})")
        print(f"表 '{table_name}' 已创建。")
    else:
        # 如果表存在，检查所有字段是否存在，如果某个字段不存在，则添加
        for field_name, field_type in fields.items():
            c.execute(f"PRAGMA table_info({table_name})")
            columns = [info[1] for info in c.fetchall()]
            if field_name not in columns:
                c.execute(f"ALTER TABLE {table_name} ADD COLUMN {field_name} {field_type}")
                print(f"字段 '{field_name}' 已添加到表 '{table_name}'。")

    conn.commit()

def get_db_connection():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

"""<初始化全部数据库>"""
def Ini_Data():
    # 检查DB目录是否存在，如果不存在，则创建
    if not os.path.exists(get_base_path(DB_DIR)):
        os.makedirs(DB_DIR)
    update_MyFast_db()#我的快捷方式
    update_MyPlugins_db()#初始化我的插件
    update_WorkFlow_db() #初始化工作流_父流
    update_sub_WorkFlow_db() #初始化工作流_子流
    ex_to_sqlite_is_AIxlx() #初始化AI网址
    #update_HTML_MyPlugins_db()#初始化我的插件-HTML记录文件


"""<各表初始化>"""
#初始化我的快捷方式
def update_MyFast_db():

    # 创建或打开数据库文件的完整路径
    conn = sqlite3.connect(db_path)

    # 检查并更新数据库结构
    table_name = 'MyFast'
    fields = {
        'ID': 'INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT',
        'UserID': 'INTEGER NOT NULL DEFAULT 0',
        'WType': 'TEXT',
        'URL': 'TEXT',
        'Title': 'TEXT',
        'Des': 'TEXT',
        'CreDate': 'TEXT',#创建日期
        'UbDate': 'TEXT',#使用日期
        'Utimes': 'INTEGER NOT NULL DEFAULT 0',#使用次数
    }
    check_and_update_db_structure(conn, table_name, fields)

    # 完成后关闭连接
    conn.close()

#初始化我的插件
def update_MyPlugins_db():

    # 创建或打开数据库文件的完整路径
    conn = sqlite3.connect(db_path)

    # 检查并更新数据库结构
    table_name = 'MyPlugins'
    fields = {
        'ID': 'INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT',
        'UserID': 'INTEGER DEFAULT 0',
        'PlugDir': 'TEXT',#插件目录
        'PlugName': 'TEXT',#插件名
        'ICO': 'TEXT',#插件图标
        'PlugHTML': 'TEXT',#HTML主引导页
        'Ver': 'TEXT',#版本号
        'PlugDes': 'TEXT',#插件说明
        'VerDes': 'TEXT',#版本说明
        'help': 'TEXT',#帮助
        'author': 'TEXT',#作者
        'comname': 'TEXT',#公司名
        'website': 'TEXT',#网址
        'uplink': 'TEXT',#升级链接
        'CreDate': 'TEXT',  # 创建日期
        'UbDate': 'TEXT',  # 使用日期
        'Utimes': 'INTEGER NOT NULL DEFAULT 0',  # 使用次数
        #'Developer': 'INTEGER NOT NULL DEFAULT 0',是否为开发者
        'APIDes': 'TEXT',  # API接口说明
        'uploadDir': 'TEXT',  # 临时文件夹
        'Keypass': 'TEXT',  # 唯一密钥
    }
    check_and_update_db_structure(conn, table_name, fields)

    # 完成后关闭连接
    conn.close()

#初始化我的插件-HTML记录文件
def update_HTML_MyPlugins_db():

    # 创建或打开数据库文件的完整路径
    conn = sqlite3.connect(db_path)

    # 检查并更新数据库结构
    table_name = 'MyPlugins_HTML'
    fields = {
        'ID': 'INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT',
        'UserID': 'INTEGER NOT NULL DEFAULT 0',
        'HTMLDir': 'TEXT',  # HTML文件
        'PlugID': 'INTEGER',#插件ID
        'IndexPage': 'INTEGER NOT NULL DEFAULT 0',#是否为主页
        'Render': 'INTEGER NOT NULL DEFAULT 0',#是否是jinja2渲染页
        'Code': 'TEXT',#HTML源代码
    }
    check_and_update_db_structure(conn, table_name, fields)

    # 完成后关闭连接
    conn.close()

#初始化我的工作流_父流
def update_WorkFlow_db():
    # 创建或打开数据库文件的完整路径
    conn = sqlite3.connect(db_path)

    # 检查并更新数据库结构
    table_name = 'WorkFlow'
    fields = {
        'ID': 'INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT',
        'UserID': 'INTEGER NOT NULL DEFAULT 0',
        'WorkFlowName': 'TEXT',  # 工作流名称
        'WorkFlowDes': 'TEXT',  # 工作流描述
    }
    check_and_update_db_structure(conn, table_name, fields)

    # 完成后关闭连接
    conn.close()

#初始化我的工作流_子流
def update_sub_WorkFlow_db():
    # 创建或打开数据库文件的完整路径
    conn = sqlite3.connect(db_path)

    # 检查并更新数据库结构
    table_name = 'sub_WorkFlow'
    fields = {
        'ID': 'INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT',
        'UserID': 'INTEGER NOT NULL DEFAULT 0',
        'WorkFlowID': 'INTEGER',  # 所属父流ID
        'WorkFlowName': 'TEXT',  # 工作流名称
        'PlugID': 'INTEGER',  # 插件ID
        'PlugName': 'TEXT',  # 插件名称
        'PlugDes': 'TEXT',  # 插件描述
        'PlugDir': 'TEXT',  # 插件文件夹
        'Sort': 'INTEGER',  # 排序
        'JSON': 'TEXT',  # JSON配置
        'conn': 'INTEGER NOT NULL DEFAULT 0',  # 流的状态：-1测试失败，0未测试，1测试正常
    }
    check_and_update_db_structure(conn, table_name, fields)

    # 完成后关闭连接
    conn.close()

"""<AI网址大全>"""
#将xlsx转换为sqlite
def ex_to_sqlite_is_AIxlx():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    xlsx_path = get_base_path('AI.xlsx')
    # 读取Excel文件
    xls = pd.ExcelFile(xlsx_path)
    # 创建表名
    table_name = "AIURL"
    # 删除已存在的表
    cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
    # 读取第一张工作表以获取表结构
    df_first = pd.read_excel(xlsx_path, sheet_name=xls.sheet_names[0])
    # 根据第一张工作表的表头创建字段，包括 'sheet_name' 字段
    columns = "ID INTEGER PRIMARY KEY AUTOINCREMENT, " + ", ".join([f"{col} TEXT" for col in df_first.columns]) + ", sheet_name TEXT"
    cursor.execute(f"CREATE TABLE {table_name} ({columns})")
    # 遍历所有工作表
    for sheet_name in xls.sheet_names:
        # 读取工作表数据
        df = pd.read_excel(xlsx_path, sheet_name=sheet_name)
        # 为数据添加 'sheet_name' 字段
        df['sheet_name'] = sheet_name
        # 将数据插入到SQLite数据库，注意这里我们不直接使用to_sql，因为需要确保自增ID能正确处理
        # 准备插入数据的SQL语句
        columns_without_id = ", ".join(df_first.columns) + ", sheet_name"
        placeholders = ", ".join(["?"] * (len(df_first.columns) + 1))
        insert_sql = f"INSERT INTO {table_name} ({columns_without_id}) VALUES ({placeholders})"
        for _, row in df.iterrows():
            cursor.execute(insert_sql, row.to_list())

    # 提交事务并关闭连接
    conn.commit()
    conn.close()

#从json到SQLite
# def wr_SQL_DB_is_AIxlx():
#     data = readjson_is_AIxlx()
#
#     # 连接到SQLite数据库（如果不存在，会自动创建）
#     conn = sqlite3.connect(db_path)
#     cursor = conn.cursor()
#
#     # 检查表是否存在，如果存在，则删除
#     cursor.execute("DROP TABLE IF EXISTS AIURL")
#
#     # 根据数据自动确定字段并创建表
#     if data:
#         # 获取第一条记录中的所有键，假设所有记录的结构相同
#         columns = data[0].keys()
#         # 构造创建表的SQL语句
#         create_table_query = f"CREATE TABLE AIURL ({', '.join([f'{col} TEXT' for col in columns])})"
#         cursor.execute(create_table_query)
#
#         # 准备插入数据的SQL语句
#         insert_query = f"INSERT INTO AIURL ({', '.join(columns)}) VALUES ({', '.join(['?' for _ in columns])})"
#
#         # 插入数据
#         for record in data:
#             values = tuple(record[col] for col in columns)
#             cursor.execute(insert_query, values)
#
#     # 提交事务并关闭数据库连接
#     conn.commit()
#     conn.close()


#将xlsx转换为json
# def ex_to_json_is_AIxlx():
#     # 读取Excel文件的所有工作表
#     xls = pd.read_excel('AI.xlsx', sheet_name=None, engine='openpyxl')
#
#     # 初始化TinyDB数据库
#     db = TinyDB('AI.json')
#
#     # 清空数据库中的现有数据
#     db.truncate()
#
#     # 迭代处理每个工作表
#     for sheet_name, df in xls.items():
#         print(f"正在处理工作表：{sheet_name}")
#         # 将DataFrame转换为字典列表
#         records = df.to_dict(orient='records')
#
#         # 为每条记录添加所属表名字段
#         for record in records:
#             record['sheet_name'] = sheet_name
#
#         # 将数据插入TinyDB数据库
#         db.insert_multiple(records)
=======
import sqlite3,os
import pandas as pd
from Ini_sys import get_base_path
from flask_sqlalchemy import SQLAlchemy


"""
本页为所有数据库操作
ini_开头的均用于配置或通用，不要from任何_Actions的文件
"""

# 数据库文件存放路径
DB_DIR = 'DB'
DB_FILE = 'Main.db'
# db_path = os.path.join(DB_DIR, DB_FILE)
db_path = get_base_path('DB\Main.db')

PLUGINS_DB = SQLAlchemy()  # 创建 SQLAlchemy 的实例

"""<路由配置插件数据库信息>"""
def ini_plugins_db(app):
    # 这里设置所有与数据库相关的配置
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'  # 设置数据库 URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    PLUGINS_DB.init_app(app)

#插件列表的类
class Plugins(PLUGINS_DB.Model):
    __tablename__ = 'MyPlugins'  # 明确指定表名
    id = PLUGINS_DB.Column(PLUGINS_DB.Integer, primary_key=True)
    PlugDir = PLUGINS_DB.Column(PLUGINS_DB.String(120))
    PlugName = PLUGINS_DB.Column(PLUGINS_DB.String(120))
    ICO = PLUGINS_DB.Column(PLUGINS_DB.String(120))
    Ver = PLUGINS_DB.Column(PLUGINS_DB.String(20))
    #Developer = PLUGINS_DB.Column(PLUGINS_DB.Boolean)
    author = PLUGINS_DB.Column(PLUGINS_DB.String(120))
    PlugDes = PLUGINS_DB.Column(PLUGINS_DB.String(300))
    PlugHTML = PLUGINS_DB.Column(PLUGINS_DB.String(120))

"""<通用数据库函数>"""
# 查询数据库中的myplugins表中的字段值是否存在
def is_myplugins_DB(field, value):
    """在MyPlugins表中检查指定字段是否有匹配的值"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = f"SELECT COUNT(*) FROM MyPlugins WHERE {field} = ?"
    cursor.execute(query, (value,))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

# 查询指定表和字段的值是否存在，则返回True
def DB_select_return(table_name, column_name, value_name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # 构造查询SQL
    query = f"SELECT 1 FROM {table_name} WHERE {column_name} = ?"
    # 执行查询
    cursor.execute(query, (value_name,))
    result = cursor.fetchone()
    # 关闭数据库连接
    cursor.close()
    conn.close()
    # 如果查询到结果，返回True
    return result is not None


# 通过插件名检测在数据库中是否存在
def is_plugin_registered(plugdir):
    """检查插件是否在数据库中注册"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT EXISTS(SELECT 1 FROM MyPlugins WHERE PlugDir=?)", (plugdir,))
    result = cursor.fetchone()[0]
    conn.close()
    return bool(result)

# 查询 SQLite 数据库中的指定表,并返回数据列表
def query_db(table_name, condition=None):
    """
    查询 SQLite 数据库中的指定表，并可选地应用条件过滤。

    :param table_name: 要查询的表名
    :param condition: 可选的查询条件，格式为 SQL WHERE 子句（不含 'WHERE' 关键词）
    :return: 返回查询结果的列表
    注意：返回值是列表
    用例：
    table_name = 'MyPlugins'
    condition = 'PlugName = "ExamplePlugin"'  # 这里的条件应根据实际需要进行修改
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        query = f"SELECT * FROM {table_name}"
        if condition:
            query += f" WHERE {condition}"
        cursor.execute(query)

        # 获取列标题（字段名）
        columns = [description[0] for description in cursor.description]

        # 获取所有行数据并将其转换为字典列表
        data_list = [dict(zip(columns, row)) for row in cursor.fetchall()]
        conn.close()
        return data_list
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return []

#删除SQLite中的指定数据
def delete_data_from_table(table_name, condition):
    """
    删除指定表中满足特定条件的数据。

    参数:
    table_name -- 要删除数据的表名，字符串
    condition -- 完整的WHERE子句，包括字段名和比较操作，字符串

    # 示例使用
    # delete_data_from_table('users', 'email = "user@example.com"')

    返回:
    (success, message) -- 操作成功与否的布尔值和消息字符串

    """
    # 确保表名和条件是有效的
    if not table_name or not condition:
        return False, "表名和条件不能为空。"

    # 构建完整的SQL语句
    sql = f"DELETE FROM {table_name} WHERE {condition};"

    # 连接到数据库
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 执行SQL语句
        cursor.execute(sql)
        # 提交事务
        conn.commit()
        return True, "数据删除成功。"
    except sqlite3.Error as e:
        # 打印错误信息
        print(f"An error occurred: {e}")
        return False, f"数据删除失败: {e}"
    finally:
        # 确保数据库连接被关闭
        if conn:
            conn.close()


# 创建数据库表和字段
def check_and_update_db_structure(conn, table_name, fields):

    #检查并更新数据库结构。
    #如果表不存在，将创建新表。
    #如果表存在但缺少字段，则添加这些字段。

    c = conn.cursor()

    # 检查表是否存在
    c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}';")
    if c.fetchone() is None:
        # 如果表不存在，创建表
        fields_str = ', '.join([f"{name} {type}" for name, type in fields.items()])
        c.execute(f"CREATE TABLE {table_name} ({fields_str})")
        print(f"表 '{table_name}' 已创建。")
    else:
        # 如果表存在，检查所有字段是否存在，如果某个字段不存在，则添加
        for field_name, field_type in fields.items():
            c.execute(f"PRAGMA table_info({table_name})")
            columns = [info[1] for info in c.fetchall()]
            if field_name not in columns:
                c.execute(f"ALTER TABLE {table_name} ADD COLUMN {field_name} {field_type}")
                print(f"字段 '{field_name}' 已添加到表 '{table_name}'。")

    conn.commit()

def get_db_connection():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

"""<初始化全部数据库>"""
def Ini_Data():
    # 检查DB目录是否存在，如果不存在，则创建
    if not os.path.exists(get_base_path(DB_DIR)):
        os.makedirs(DB_DIR)
    update_MyFast_db()#我的快捷方式
    update_MyPlugins_db()#初始化我的插件
    update_WorkFlow_db() #初始化工作流_父流
    update_sub_WorkFlow_db() #初始化工作流_子流
    ex_to_sqlite_is_AIxlx() #初始化AI网址
    #update_HTML_MyPlugins_db()#初始化我的插件-HTML记录文件


"""<各表初始化>"""
#初始化我的快捷方式
def update_MyFast_db():

    # 创建或打开数据库文件的完整路径
    conn = sqlite3.connect(db_path)

    # 检查并更新数据库结构
    table_name = 'MyFast'
    fields = {
        'ID': 'INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT',
        'UserID': 'INTEGER NOT NULL DEFAULT 0',
        'WType': 'TEXT',
        'URL': 'TEXT',
        'Title': 'TEXT',
        'Des': 'TEXT',
        'CreDate': 'TEXT',#创建日期
        'UbDate': 'TEXT',#使用日期
        'Utimes': 'INTEGER NOT NULL DEFAULT 0',#使用次数
    }
    check_and_update_db_structure(conn, table_name, fields)

    # 完成后关闭连接
    conn.close()

#初始化我的插件
def update_MyPlugins_db():

    # 创建或打开数据库文件的完整路径
    conn = sqlite3.connect(db_path)

    # 检查并更新数据库结构
    table_name = 'MyPlugins'
    fields = {
        'ID': 'INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT',
        'UserID': 'INTEGER DEFAULT 0',
        'PlugDir': 'TEXT',#插件目录
        'PlugName': 'TEXT',#插件名
        'ICO': 'TEXT',#插件图标
        'PlugHTML': 'TEXT',#HTML主引导页
        'Ver': 'TEXT',#版本号
        'PlugDes': 'TEXT',#插件说明
        'VerDes': 'TEXT',#版本说明
        'help': 'TEXT',#帮助
        'author': 'TEXT',#作者
        'comname': 'TEXT',#公司名
        'website': 'TEXT',#网址
        'uplink': 'TEXT',#升级链接
        'CreDate': 'TEXT',  # 创建日期
        'UbDate': 'TEXT',  # 使用日期
        'Utimes': 'INTEGER NOT NULL DEFAULT 0',  # 使用次数
        #'Developer': 'INTEGER NOT NULL DEFAULT 0',是否为开发者
        'APIDes': 'TEXT',  # API接口说明
        'uploadDir': 'TEXT',  # 临时文件夹
        'Keypass': 'TEXT',  # 唯一密钥
    }
    check_and_update_db_structure(conn, table_name, fields)

    # 完成后关闭连接
    conn.close()

#初始化我的插件-HTML记录文件
def update_HTML_MyPlugins_db():

    # 创建或打开数据库文件的完整路径
    conn = sqlite3.connect(db_path)

    # 检查并更新数据库结构
    table_name = 'MyPlugins_HTML'
    fields = {
        'ID': 'INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT',
        'UserID': 'INTEGER NOT NULL DEFAULT 0',
        'HTMLDir': 'TEXT',  # HTML文件
        'PlugID': 'INTEGER',#插件ID
        'IndexPage': 'INTEGER NOT NULL DEFAULT 0',#是否为主页
        'Render': 'INTEGER NOT NULL DEFAULT 0',#是否是jinja2渲染页
        'Code': 'TEXT',#HTML源代码
    }
    check_and_update_db_structure(conn, table_name, fields)

    # 完成后关闭连接
    conn.close()

#初始化我的工作流_父流
def update_WorkFlow_db():
    # 创建或打开数据库文件的完整路径
    conn = sqlite3.connect(db_path)

    # 检查并更新数据库结构
    table_name = 'WorkFlow'
    fields = {
        'ID': 'INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT',
        'UserID': 'INTEGER NOT NULL DEFAULT 0',
        'WorkFlowName': 'TEXT',  # 工作流名称
        'WorkFlowDes': 'TEXT',  # 工作流描述
    }
    check_and_update_db_structure(conn, table_name, fields)

    # 完成后关闭连接
    conn.close()

#初始化我的工作流_子流
def update_sub_WorkFlow_db():
    # 创建或打开数据库文件的完整路径
    conn = sqlite3.connect(db_path)

    # 检查并更新数据库结构
    table_name = 'sub_WorkFlow'
    fields = {
        'ID': 'INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT',
        'UserID': 'INTEGER NOT NULL DEFAULT 0',
        'WorkFlowID': 'INTEGER',  # 所属父流ID
        'WorkFlowName': 'TEXT',  # 工作流名称
        'PlugID': 'INTEGER',  # 插件ID
        'PlugName': 'TEXT',  # 插件名称
        'PlugDes': 'TEXT',  # 插件描述
        'PlugDir': 'TEXT',  # 插件文件夹
        'Sort': 'INTEGER',  # 排序
        'JSON': 'TEXT',  # JSON配置
        'conn': 'INTEGER NOT NULL DEFAULT 0',  # 流的状态：-1测试失败，0未测试，1测试正常
    }
    check_and_update_db_structure(conn, table_name, fields)

    # 完成后关闭连接
    conn.close()

"""<AI网址大全>"""
#将xlsx转换为sqlite
def ex_to_sqlite_is_AIxlx():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    xlsx_path = get_base_path('AI.xlsx')
    # 读取Excel文件
    xls = pd.ExcelFile(xlsx_path)
    # 创建表名
    table_name = "AIURL"
    # 删除已存在的表
    cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
    # 读取第一张工作表以获取表结构
    df_first = pd.read_excel(xlsx_path, sheet_name=xls.sheet_names[0])
    # 根据第一张工作表的表头创建字段，包括 'sheet_name' 字段
    columns = "ID INTEGER PRIMARY KEY AUTOINCREMENT, " + ", ".join([f"{col} TEXT" for col in df_first.columns]) + ", sheet_name TEXT"
    cursor.execute(f"CREATE TABLE {table_name} ({columns})")
    # 遍历所有工作表
    for sheet_name in xls.sheet_names:
        # 读取工作表数据
        df = pd.read_excel(xlsx_path, sheet_name=sheet_name)
        # 为数据添加 'sheet_name' 字段
        df['sheet_name'] = sheet_name
        # 将数据插入到SQLite数据库，注意这里我们不直接使用to_sql，因为需要确保自增ID能正确处理
        # 准备插入数据的SQL语句
        columns_without_id = ", ".join(df_first.columns) + ", sheet_name"
        placeholders = ", ".join(["?"] * (len(df_first.columns) + 1))
        insert_sql = f"INSERT INTO {table_name} ({columns_without_id}) VALUES ({placeholders})"
        for _, row in df.iterrows():
            cursor.execute(insert_sql, row.to_list())

    # 提交事务并关闭连接
    conn.commit()
    conn.close()

#从json到SQLite
# def wr_SQL_DB_is_AIxlx():
#     data = readjson_is_AIxlx()
#
#     # 连接到SQLite数据库（如果不存在，会自动创建）
#     conn = sqlite3.connect(db_path)
#     cursor = conn.cursor()
#
#     # 检查表是否存在，如果存在，则删除
#     cursor.execute("DROP TABLE IF EXISTS AIURL")
#
#     # 根据数据自动确定字段并创建表
#     if data:
#         # 获取第一条记录中的所有键，假设所有记录的结构相同
#         columns = data[0].keys()
#         # 构造创建表的SQL语句
#         create_table_query = f"CREATE TABLE AIURL ({', '.join([f'{col} TEXT' for col in columns])})"
#         cursor.execute(create_table_query)
#
#         # 准备插入数据的SQL语句
#         insert_query = f"INSERT INTO AIURL ({', '.join(columns)}) VALUES ({', '.join(['?' for _ in columns])})"
#
#         # 插入数据
#         for record in data:
#             values = tuple(record[col] for col in columns)
#             cursor.execute(insert_query, values)
#
#     # 提交事务并关闭数据库连接
#     conn.commit()
#     conn.close()


#将xlsx转换为json
# def ex_to_json_is_AIxlx():
#     # 读取Excel文件的所有工作表
#     xls = pd.read_excel('AI.xlsx', sheet_name=None, engine='openpyxl')
#
#     # 初始化TinyDB数据库
#     db = TinyDB('AI.json')
#
#     # 清空数据库中的现有数据
#     db.truncate()
#
#     # 迭代处理每个工作表
#     for sheet_name, df in xls.items():
#         print(f"正在处理工作表：{sheet_name}")
#         # 将DataFrame转换为字典列表
#         records = df.to_dict(orient='records')
#
#         # 为每条记录添加所属表名字段
#         for record in records:
#             record['sheet_name'] = sheet_name
#
#         # 将数据插入TinyDB数据库
#         db.insert_multiple(records)
>>>>>>> 33969d2a895ce8a09fca410185bb3cfa811bfe73
