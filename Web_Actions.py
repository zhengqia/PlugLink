from flask import Flask, request, jsonify, Blueprint, render_template,Response
import sqlite3,os,json,requests,glob,random,string,re,sys,webbrowser,platform,subprocess,chardet,shutil
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from Ini_sys import *
from Ini_DB import *

web_blueprint = Blueprint('web', __name__)

"""<快捷方式操作网址相关函数>"""

# 插入数据到数据库的函数
def insert_website(WType, UserID, URL, Title, Des, CreDate, UbDate, Utimes):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO MyFast (WType, UserID, URL, Title, Des, CreDate, UbDate, Utimes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (WType, UserID, URL, Title, Des, CreDate, UbDate, Utimes))
        conn.commit()
    except sqlite3.Error as e:
        print(f"数据库错误: {e}")
    finally:
        conn.close()

# 调用函数添加网址到数据库
def add_website():
    # 获取JSON数据
    data = request.json
    url = data.get('url')
    title = data.get('title')
    description = data.get('description')

    # 当前时间
    now = datetime.now()
    formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')

    # 插入数据到数据库
    insert_website('website',0,url, title, description, formatted_date, formatted_date, 0)

    return {"message": "添加成功"}  # 返回一个可以被 jsonify 序列化的字典

# 添加插件到数据库
def add_plugin():
    # 获取JSON数据
    data = request.json
    plugin_id = data.get('plugin_id')
    url = data.get('plug_url')
    title = data.get('plug_name')
    description = data.get('plug_description')

    # 检查URL是否已经存在
    existing_urls = DB_select_return('MyFast','URL', url)
    if existing_urls:
        return {"message": "该插件已添加过"}

    # 查找插件信息
    print(plugin_id)
    DB_JSON_List=query_db('MyPlugins', f'ID={plugin_id}')
    DB_JSON = DB_JSON_List[0]
    print(DB_JSON)
    print(DB_JSON['PlugName'])
    # 当前时间
    now = datetime.now()
    formatted_date = now.strftime('%Y-%m-%d %H:%M:%S')

    # 插入数据到数据库
    insert_website('plugin', 0, url, DB_JSON['PlugName'], DB_JSON['PlugDes'], formatted_date, formatted_date, 0)

    return {"message": "添加成功"}  # 返回一个可以被 jsonify 序列化的字典


#检测网址，请求TD
def fetch_title_and_description(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # 检查请求是否成功

        # 自动检测字符编码
        detected_encoding = chardet.detect(response.content)['encoding']

        # 如果检测到编码，则使用该编码解码响应内容
        if detected_encoding:
            response.encoding = detected_encoding
        else:
            # 默认编码
            response.encoding = 'utf-8'

        # 解析HTML内容
        soup = BeautifulSoup(response.text, 'html.parser')

        # 尝试获取<title>标签内容作为网页标题
        title = soup.find('title').string if soup.find('title') else '获取不到标题'

        # 尝试获取<meta name="description">标签的内容
        description = soup.find('meta', attrs={'name': 'description'})
        description = description['content'] if description else '获取不到描述'

        return title, description
    except Exception as e:
        return '链接失败', '链接失败'

# 删除快捷方式
def del_myfast(id):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # 执行删除操作
        cursor.execute("DELETE FROM MyFast WHERE ID = ?", (id,))
        conn.commit()
    except sqlite3.Error as e:
        print(f"数据库操作错误: {e}")
        return False
    finally:
        conn.close()
    return True

# 快捷方式记数
def Utimes_myfast(id):
    try:
        conn = sqlite3.connect(db_path)  # 数据库文件路径
        cursor = conn.cursor()

        # 更新Utimes字段，使其值加1
        update_query = "UPDATE MyFast SET Utimes = Utimes + 1 WHERE ID = ?"
        cursor.execute(update_query, (id,))

        conn.commit()  # 提交事务
        conn.close()  # 关闭连接
        return True
    except:
        return False

"""<读取快捷方式列表相关函数>"""

# 提取7天天数和日期
def get_days_ago(ub_date_str):
    ub_date = datetime.strptime(ub_date_str, "%Y-%m-%d %H:%M:%S")
    delta = datetime.now() - ub_date
    if delta.days <= 7:
        return f"{delta.days} 天前"
    else:
        return ub_date_str

# 提取快捷方式列表
def fetch_myfast():
    # 连接到SQLite数据库
    # 数据库文件存放路径
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 执行查询
    query = "SELECT ID,WType, URL, Title, Des, UbDate, Utimes FROM MyFast ORDER BY UbDate DESC"
    cursor.execute(query)
    items = cursor.fetchall()

    # 关闭数据库连接
    conn.close()

    # 处理每条记录
    formatted_items = []
    for item in items:
        ID, WType, URL, Title, Des, UbDate, Utimes = item
        if WType == "website":
            icon_class = "layui-icon-website"
        else:
            icon_class = "layui-icon-component"
        UbDate = get_days_ago(UbDate)

        formatted_items.append({
            "icon_class": icon_class,
            "ID": ID,
            "URL": URL,
            "Title": Title,
            "Des": Des,
            "UbDate": UbDate,
            "Utimes": Utimes
        })

    return formatted_items


"""<AI网址大全相关函数>"""
#获取AI网址中的表名
def get_sheet_names():
    """从数据库中读取所有唯一的sheet_name"""
    # 连接到SQLite数据库
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 执行查询操作，选择不重复的sheet_name
    cur.execute("SELECT DISTINCT sheet_name FROM AIURL")

    # 获取所有结果
    sheets = cur.fetchall()

    # 关闭游标和连接
    cur.close()
    conn.close()

    # 将结果转换为列表
    unique_sheet_names = [sheet[0] for sheet in sheets]

    return unique_sheet_names

# 获取所有字段名
def get_table_columns():
    """获取指定表的所有字段名"""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 使用PRAGMA table_info()语句获取表的元数据
    cur.execute(f"PRAGMA table_info(AIURL)")

    # 获取所有字段的信息，每个字段的信息是一个元组，其中第二个元素是字段名
    columns_info = cur.fetchall()

    # 从每个字段的信息中提取字段名
    column_names = [info[1] for info in columns_info if info[1] != 'sheet_name']

    cur.close()
    conn.close()

    return column_names

# 读取表中所有内容
def get_all_records():
    """获取指定表的所有记录"""
    # 连接到数据库
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 构建查询语句，选择所有字段
    query = f"SELECT * FROM AIURL"

    # 执行查询
    cur.execute(query)

    # 获取所有记录
    records = cur.fetchall()

    # 关闭游标和连接
    cur.close()
    conn.close()

    return records

# 临时文件中心表格显示
def file_center_list():
    # 连接到SQLite数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 查询数据库
    cursor.execute("SELECT PlugName, PlugDir, uploadDir FROM MyPlugins")
    plugins = cursor.fetchall()

    # 存储结果的列表
    result = []

    # 遍历每个插件
    for plug_name, plug_dir, upload_dir in plugins:
        if not upload_dir:
            print(f"插件 {plug_name} 的 uploadDir 字段为空")
            continue

        # 分割uploadDir字段得到子目录
        directories = upload_dir.split(',')
        for dir in directories:
            full_path = os.path.join("plugins", plug_dir, dir)
            if not os.path.exists(full_path):
                print(f"目录 {full_path} 不存在")
                continue

            # 计算目录下的文件数和总占用空间
            file_count = 0
            total_size = 0
            for root, dirs, files in os.walk(full_path):
                file_count += len(files)
                total_size += sum(os.path.getsize(os.path.join(root, name)) for name in files)

            # 占用空间转为MB
            total_size_mb = round(total_size / (1024 * 1024), 2)

            # 将结果加入列表
            result.append({
                "PlugName": plug_name,
                "Directory": full_path,
                "FileCount": file_count,
                "TotalSizeMB": total_size_mb
            })

    # 关闭数据库连接
    conn.close()

    # 转化结果为JSON
    #fc_json = result
    #fc_json = json.dumps(result)
    #return fc_json
    return {"code": 0, "msg": "", "count": len(result), "data": result}

# 删除给定的目录列表及其所有内容
def delete_directories(directories):
    """ 删除给定的目录列表及其所有内容。 """
    try:
        for directory in directories:
            full_path = os.path.join(directory)  # 组合成完整路径
            shutil.rmtree(full_path)  # 删除目录及其所有内容
        return {"code": 0, "msg": "删除成功"}
    except Exception as e:
        return {"code": 500, "msg": str(e)}

"""<一般web端路由交互执行>"""
@web_blueprint.route('/', methods=['POST'])
def handle_web_Execution():
    if request.is_json:  # 确保请求包含 JSON 数据
        data = request.get_json()
        action = data.get('action')
        url = data.get('url')
        id = data.get('id')
        print(f'当前于web路由action状态码：{action}')
        print(file_center_list())
        match action:
            case 'fetch_myfast':# 刷新快捷方式
                results = fetch_myfast()
                return render_template('add_myfast.html', items=results)

            case 'add_website':# 添加网址到快捷方式
                response_data = add_website()
                return jsonify(response_data)

            case 'add_plugin':# 添加插件到快捷方式
                response_data = add_plugin()
                return jsonify(response_data)

            case 'conn_website':# 检测网址
                title, description = fetch_title_and_description(url)
                return jsonify({'title': title, 'description': description})

            case 'del_fast':#删除快捷方式
                if del_myfast(id):
                    return jsonify({"message": "删除成功"})
                else:
                    return jsonify({"error": "删除失败"}), 500

            case 'utimes':#快捷方式计数
                if Utimes_myfast(id):
                    return jsonify({'message': 'Utimes_myfast success'})
                else:
                    return jsonify({'status': 'error', 'message': 'Missing id'}), 400

            case 'file_center_list':  # 临时文件中心表格显示
                return file_center_list()

            case 'del_upload_file':  # 临时文件中心表格显示
                directories = data.get('directories', [])
                result = delete_directories(directories)
                return jsonify(result)

            case 'AIURL_list':#读取网址大全列表
                    unique_sheet_names = get_sheet_names()
                    unique_column_names = get_table_columns()
                    unique_all_records = get_all_records()
                    return render_template('AIURL_List.html',
                                           sheet_names=unique_sheet_names,
                                           column_names=unique_column_names,
                                           all_records=unique_all_records)

            case _:
                return jsonify({"error": "Invalid action or request method"}), 400
    else:
        return jsonify({'error': 'Invalid Content-Type'}), 400
