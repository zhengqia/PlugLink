<<<<<<< HEAD
from flask import jsonify, Flask, Blueprint, request, send_file, render_template,current_app
import sqlite3,os,json,requests,glob,random,string,re,zipfile,io,shutil,time,importlib,ast
from datetime import datetime
from flask_socketio import emit
from threading import Timer
from Ini_sys import *
from Ini_DB import *

plugins_blueprint = Blueprint('plugins', __name__)

PLUGINS_DIR = get_base_path('plugins')

"""<关于插件>"""
def install_plugin_dependencies():
    """遍历plugins目录并安装未注册插件的依赖"""
    print(f'正在准备扫描插件依赖，扫描目录：{PLUGINS_DIR}')
    print("pip 路径:", get_pip_path())
    for plugdir in os.listdir(PLUGINS_DIR):
        plugin_path = os.path.join(PLUGINS_DIR, plugdir)
        if plugdir in ['__pycache__', '__init__.py']:
            continue

        print(f'正在历遍并安装依赖：{plugin_path}')

        if os.path.isdir(plugin_path) and is_plugin_registered(plugdir):
            print(f"检查插件: {plugdir}")
            dependencies = get_plugin_dependencies(plugin_path)
            if dependencies:
                print(f"发现依赖项: {dependencies}, 正在安装...")
                installed_deps, failed_deps = install_dependencies(plugin_path, dependencies)
                if installed_deps:
                    print(f"成功安装依赖: {', '.join(installed_deps)}")
                if failed_deps:
                    print(f"安装失败的依赖: {', '.join([dep[0] for dep in failed_deps])}")
            else:
                print(f"插件 {plugdir} 没有依赖或依赖已安装。")
        else:
            print(f"插件 {plugdir} 未安装，跳过。")

# 加载插件的libs依赖目录
def load_plugin(plugin_name):
    plugin_dir = os.path.join(get_base_path('plugins'), plugin_name)
    libs_path = os.path.join(plugin_dir, 'libs')

    # 保存当前的 sys.path
    original_sys_path = sys.path.copy()
    try:
        # 将插件的目录和 libs 目录添加到 sys.path，前提是它们不在 sys.path 中
        if plugin_dir not in sys.path and os.path.exists(plugin_dir):
            sys.path.insert(0, plugin_dir)
            print(f'已添加插件{plugin_name}的目录：{plugin_dir}')
        if libs_path not in sys.path and os.path.exists(libs_path):
            sys.path.insert(0, libs_path)
            print(f'已添加插件{plugin_name}的依赖路径：{libs_path}')

        print(f'sys路径：{sys.path}')

        # 动态导入插件模块
        #module = importlib.import_module(plugin_name)
        #print(f'已成功导入插件{plugin_name}模块')

    except Exception as e:
        # 恢复原始的 sys.path
        sys.path = original_sys_path
        print(f"导入{plugin_name}插件时发生错误: {str(e)}")
    #return module
#若启动时不需要预先加载，以下是示例代码
# def handle_request(plugin_name, request_data):
#     plugin = load_plugin(plugin_name)
#     if plugin:
#         return plugin.handle(request_data)  # 假设插件有 handle 方法处理请求

#若要启动时自动扫描所有插件，则执行此函数
def load_all_plugins():
    plugin_dir = get_base_path('plugins')
    print(f'即将扫描插件依赖路径：{plugin_dir}')
    plugins = [name for name in os.listdir(plugin_dir) if os.path.isdir(os.path.join(plugin_dir, name))]
    for plugin_name in plugins:
        if is_plugin_registered(plugin_name):
            load_plugin(plugin_name)
        else:
            print(f'{plugin_name}该插件没有安装...跳过')

#历遍自定义插件里面的文件
def plugin_dir(path):
    """
    递归扫描指定路径下的所有文件和文件夹，并将其结构化为layui tree组件需要的格式。
    """
    path = get_base_path(path)
    tree = []
    if os.path.exists(path):
        for name in os.listdir(path):
            node_path = os.path.join(path, name)
            if os.path.isdir(node_path):
                tree.append({
                    "title": name,
                    "children": plugin_dir(node_path)
                })
            else:
                tree.append({"title": name})
    return tree

#提交我的插件-注册进程-加载myplugin_temp.json
def load_plugin_info():
    base_path = get_base_path('plugins')
    file_name = 'myplugin_temp.json'
    full_path = os.path.join(base_path, file_name)

    try:
        with open(full_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"Error:文件未找到: {full_path}")
    except json.JSONDecodeError:
        print(f"Error:JSON解析错误: {full_path}")
    except Exception as e:
        print(f"Error:加载插件信息时发生错误: {str(e)}")

    return None

#提交我的插件-安装进程-检测目录
def check_plugin_directory(plugin_data):
    base_path = get_base_path('plugins')
    plug_dir = plugin_data.get('PlugDir', '')

    # 构建插件目录的完整路径
    plugin_path = os.path.join(base_path, plug_dir)

    # 第一步：检查插件目录是否存在
    if not os.path.exists(plugin_path) or not os.path.isdir(plugin_path):
        return {'status': 'error', 'message': f"找不到插件目录：{plug_dir}"}

    # 第二步：检查main.py或main.exe是否存在
    # if not os.path.isfile(os.path.join(plugin_path, 'main.py')) and not os.path.isfile(os.path.join(plugin_path, 'main.exe')):
    #     return {'status': 'error', 'message': '找不到main主文件'}

    # 第三步：如果有main.py，检查是否有__init__.py
    if os.path.isfile(os.path.join(plugin_path, 'main.py')) and not os.path.isfile(os.path.join(plugin_path, '__init__.py')):
        return {'status': 'error', 'message': '缺少__init__.py文件'}

    # 第四步：检查是否有*.json文件，表示插件已注册
    if glob.glob(os.path.join(plugin_path, 'ThePlugin.json')):
        return {'status': 'error', 'message': '该插件已经注册'}

    # 第五步：检查indexpage目录及其下是否有html文件
    indexpage_path = os.path.join(plugin_path, 'static')
    if not os.path.exists(indexpage_path) or not any(fname.endswith('.html') for fname in os.listdir(indexpage_path)):
        return {'status': 'error', 'message': '找不到HTML主文件'}

    # 所有检查通过
    return {'status': 'success', 'message': '目录合法性检测成功！'}

#提交我的插件-安装进程-检测插件名称
def check_and_rename_plug_name(plug_name):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM MyPlugins WHERE PlugName = ?", (plug_name,))
    exists = cur.fetchone()[0] > 0

    if exists:
        # 如果名称存在，生成一个新的名称
        new_plug_name = plug_name + '_' + ''.join(random.choices(string.ascii_letters + string.digits, k=3))
        cur.close()
        conn.close()
        return new_plug_name
    else:
        cur.close()
        conn.close()
        return plug_name

#提交我的插件-安装进程-实时可保存myplugin_temp.json
def save_plugin_info(plugin_data):
    base_path = get_base_path('plugins')
    full_path = os.path.join(base_path, 'myplugin_temp.json')
    with open(full_path, 'w', encoding='utf-8') as f:
        json.dump(plugin_data, f, ensure_ascii=False, indent=4)

#提交我的插件-安装进程-装载ICO图标
def load_icon(plug_dir):
    base_path = get_base_path('plugins')
    target_path = os.path.join(base_path, plug_dir)

    plug_path = os.path.join(plug_dir)
    supported_formats = ('.jpg', '.png')
    icon_files = [f for f in os.listdir(target_path) if os.path.splitext(f)[1].lower() in supported_formats]

    if icon_files:
        # 随机选择一个ICO图标文件
        chosen_icon = random.choice(icon_files)
        icon_path = os.path.join(plug_path, chosen_icon)
    else:
        # 如果没有找到支持的文件格式，使用默认ICO图标
        icon_path = 'favicon.jpg'

    return icon_path

#提交我的插件-安装进程-定义HTML
def check_html_main_page(plug_dir, plug_html):
    base_path = get_base_path('plugins')
    indexpage_path = os.path.join(base_path, plug_dir, 'static')

    # 检查indexpage文件夹是否存在
    if not os.path.exists(indexpage_path):
        return 'Error:找不到HTML文件夹'

    # 确保plug_html以.html结尾
    if not plug_html.endswith('.html'):
        plug_html += '.html'

    # 检查指定的HTML文件是否存在
    html_file_path = os.path.join(indexpage_path, plug_html)
    if not os.path.isfile(html_file_path):
        return f'Error:找不到HTML主文件: {plug_html}'

    return '完成HTML主页定义！'

# 生成一个36位的随机密钥，包括大小写字母和数字
def generate_keypass(length=36):
    characters = string.ascii_letters + string.digits  # 包含大小写英文字母和数字
    return ''.join(random.choices(characters, k=length))



#提交我的插件-安装进程-保存开发信息
def save_author_info(plugin_data, base_path='plugins'):
    # 构造目标目录路径
    target_dir = os.path.join(get_base_path(base_path), plugin_data['PlugDir'])
    # 确保目标目录存在
    os.makedirs(target_dir, exist_ok=True)

    # 构造ThePlugin.json文件的完整路径
    json_file_path = os.path.join(target_dir, 'ThePlugin.json')

    # 准备保存的信息
    info_to_save = plugin_data.copy()  # 创建一个字典的副本，以避免修改原始数据

    # 添加创建日期
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    info_to_save['CreDate'] = now

    # 如果存在'action'键，并且其值为'add_myplugin'，则从字典中移除
    if info_to_save.get('action') == 'add_myplugin':
        del info_to_save['action']

    # 保存到ThePlugin.json文件
    with open(json_file_path, 'w', encoding='utf-8') as f:
        json.dump(info_to_save, f, ensure_ascii=False, indent=4)


    # # 构造目标目录路径
    # target_dir = os.path.join(base_path, plugin_data['PlugDir'])
    # # 确保目标目录存在
    # os.makedirs(target_dir, exist_ok=True)
    #
    # # 构造ThePlugin.json文件的完整路径
    # json_file_path = os.path.join(target_dir, 'ThePlugin.json')
    #
    # # 准备保存的信息
    # info_to_save = plugin_data.copy()  # 创建一个字典的副本，以避免修改原始数据
    #
    # # 如果存在'action'键，并且其值为'add_myplugin'，则从字典中移除
    # if info_to_save.get('action') == 'add_myplugin':
    #     del info_to_save['action']
    #
    # # 保存到ThePlugin.json文件
    # with open(json_file_path, 'w', encoding='utf-8') as f:
    #     json.dump(info_to_save, f, ensure_ascii=False, indent=4)

# 提交我的插件-安装进程-修改HTML样式路径
def update_resource_paths(plug_dir_name):
    # 构建完整的插件目录路径，加入了"plugins"上级目录
    plug_dir = os.path.join(get_base_path('plugins'), plug_dir_name)

    # 定义原路径和新路径的映射
    path_mappings = {
        r'layui\.css': '<link href="../../../static/res/layui/css/layui.css" rel="stylesheet">',
        r'admin\.css': '<link href="../../../static/res/adminui/dist/css/admin.css" rel="stylesheet">',
        r'jquery-3.6.0.min.js': '<script src="../../../static/res/jquery-3.6.0.min.js"></script>',
        r'layui.js': '<script src="../../../static/res/layui/layui.js"></script>',
        r'socket.io.js': '<script src="../../../static/res/socket.io.js"></script>'
    }

    # 构建搜索路径
    search_path = os.path.join(plug_dir, "static", "*.html")

    # 遍历所有HTML文件
    for file_path in glob.glob(search_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # 对每个路径进行检查和替换
        for original, new in path_mappings.items():
            # 构造正则表达式，捕获对应的文件引用
            pattern = re.compile(r'<.*?["\'].*?(' + original + r').*?["\'].*?>', re.IGNORECASE)
            # 如果找到匹配，则替换
            if pattern.search(content):
                content = pattern.sub(new, content)

        # 将修改后的内容写回文件
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)


# 提交我的插件-安装进程-写入HTML到数据库
def process_html_files(plugin_data, db_path):
    messages = []  # 用于存储操作结果和消息的列表
    base_path = get_base_path('plugins')
    plug_dir = plugin_data.get('PlugDir', '')
    dir_paths = {
        'static': os.path.join(base_path, plug_dir, 'static'),
        'templates': os.path.join(base_path, plug_dir, 'templates')
    }

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # 获取PlugID
        cur.execute("SELECT id FROM MyPlugins WHERE PlugDir = ?", (plug_dir,))
        plug_id_row = cur.fetchone()
        if plug_id_row:
            plug_id = plug_id_row[0]
        else:
            messages.append({'message': f'找不到{plug_dir}对应的插件ID', 'status': 'error'})
            return messages

        for dir_name, dir_path in dir_paths.items():
            if os.path.exists(dir_path):
                for file_name in os.listdir(dir_path):
                    if file_name.endswith('.html'):
                        file_path = os.path.join(dir_path, file_name)
                        with open(file_path, 'r', encoding='utf-8') as file:
                            code = file.read()

                            # 判断是否为IndexPage或Render
                            is_indexpage = (dir_name == 'static' and file_name == plugin_data.get('PlugHTML'))
                            is_render = (dir_name == 'templates')

                            # 写入数据库
                            cur.execute(
                                "INSERT INTO MyPlugins_HTML (HTMLDir, Code, IndexPage, Render, PlugID) VALUES (?, ?, ?, ?, ?)",
                                (file_path.replace(base_path, '').lstrip(os.sep), code, is_indexpage, is_render,
                                 plug_id))
            else:
                messages.append({'message': f'缺少{dir_name}文件夹', 'status': 'warning'})

        conn.commit()
    except Exception as e:
        conn.rollback()
        messages.append({'message': f'操作HTML文件失败，异常原因是：{str(e)}', 'status': 'error'})
    finally:
        conn.close()

    if not messages:  # 如果没有错误消息，表示操作成功
        messages.append({'message': '完成对HTML的初始化！', 'status': 'success'})

    return messages

# 提交我的插件-安装进程-最后一步，删除临时文件
def delete_temp_file(base_path='plugins', temp_file_name='myplugin_temp.json'):
    temp_file_path = os.path.join(get_base_path(base_path), temp_file_name)

    # 尝试删除文件
    try:
        os.remove(temp_file_path)
        return True, '安装完成！'  # 成功删除文件
    except OSError as e:
        return False, f'删除临时文件失败，异常原因是：{str(e)}'


"""<安装插件>"""
#安装插件-安装进程-加载ThePlugin.json.json
def load_ThePlugin_json(plugdir):
    base_path = get_base_path('plugins')
    file_name = 'ThePlugin.json'
    full_path = os.path.join(get_base_path(plugdir),file_name)
    print(full_path)
    try:
        with open(full_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"Error:文件未找到: {full_path}")
    except json.JSONDecodeError:
        print(f"Error:JSON解析错误: {full_path}")
    except Exception as e:
        print(f"Error:加载插件信息时发生错误: {str(e)}")

#安装插件-安装进程-写入数据库
def write_to_database(plugin_data, db_path):
    plugdir = plugin_data.get('PlugDir')

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # 检查数据库中是否已存在相同的 PlugDir
        cur.execute("SELECT COUNT(*) FROM MyPlugins WHERE PlugDir = ?", (plugdir,))
        if cur.fetchone()[0] > 0:
            return "该插件已经安装过了，无须再安装。"

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        plugin_data.update({'UbDate': now})

        # 准备数据插入语句
        columns = ', '.join(plugin_data.keys())
        placeholders = ':' + ', :'.join(plugin_data.keys())
        sql = f"INSERT INTO MyPlugins ({columns}) VALUES ({placeholders})"
        cur.execute(sql, plugin_data)
        conn.commit()

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

    return None  # 返回None表示无错误

    # data_to_insert = plugin_data.copy()
    # action = data_to_insert.pop('action', None)  # 移除action，但不修改原plugin_data
    #
    # try:
    #     conn = sqlite3.connect(db_path)
    #     cur = conn.cursor()
    #
    #     # 准备数据插入语句，注意不再包含action
    #     columns = ', '.join(data_to_insert.keys())
    #     placeholders = ':' + ', :'.join(data_to_insert.keys())
    #     sql = f"INSERT INTO MyPlugins ({columns}, CreDate, UbDate) VALUES ({placeholders}, :CreDate, :UbDate)"
    #
    #     now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #     data_to_insert.update({'CreDate': now, 'UbDate': now})
    #
    #     cur.execute(sql, data_to_insert)
    #     conn.commit()
    #
    # except Exception as e:
    #     # 回滚变更
    #     conn.rollback()
    #     # 使用id作为唯一标识进行数据删除
    #     if 'id' in plugin_data:
    #         cur.execute("DELETE FROM MyPlugins WHERE id = ?", (plugin_data['id'],))
    #         conn.commit()
    #     raise e  # 抛出异常供调用方处理
    #
    # finally:
    #     # 关闭数据库连接
    #     conn.close()

# 安装插件-安装进程-插件蓝图注册
def setup_plugin_blueprint(plugdir):
    app = current_app
    #app = current_app._get_current_object()
    success_count = 0
    failure_count = 0

    for dirpath, dirnames, filenames in os.walk(plugdir):
        for filename in filenames:
            if filename.endswith('.py') and not filename.startswith('__'):
                module_path = os.path.join(dirpath, filename[:-3]).replace('/', '.').replace('\\', '.')
                print(module_path)
                try:
                    mod = importlib.import_module(module_path)
                    if hasattr(mod, 'blueprint'):
                        app.register_blueprint(mod.blueprint)
                        success_count += 1
                        print(f"成功注册蓝图: {module_path}")
                    else:
                        print(f"模块中未找到蓝图: {module_path}")
                except Exception as e:
                    print(f"注册蓝图失败: {module_path}, 错误: {e}")
                    failure_count += 1
    print(app.url_map)
    return success_count, failure_count

"""<其它数据显示>"""
# 我的开发列表数据显示
def fetch_exp_myplugins_list(db_path=db_path):
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 获取所有已安装的插件目录
    cursor.execute("SELECT PlugDir FROM MyPlugins")
    installed_plugins = set(row[0] for row in cursor.fetchall())  # 现在是插件目录名的集合

    plugins_list = []
    # 遍历 PLUGINS_DIR 目录下的所有子目录
    for root, dirs, files in os.walk(PLUGINS_DIR):
        for dir in dirs:
            json_path = os.path.join(root, dir, 'ThePlugin.json')
            # 检查是否存在 ThePlugin.json 文件
            if os.path.isfile(json_path):
                # 读取 JSON 文件并解析数据
                with open(json_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    # 判断当前插件是否已安装
                    is_installed = dir in installed_plugins  # 使用目录名而非完整路径进行比较
                    plugins_list.append({
                        "ID": data.get("ID", ""),
                        "PlugName": data.get("PlugName", ""),
                        "PlugDir": os.path.join(root, dir),
                        "Ver": data.get("Ver", ""),
                        "PlugDes": data.get("PlugDes", ""),
                        "CreDate": data.get("CreDate", ""),
                        "PlugHTML": data.get("PlugHTML", ""),
                        "isInstalled": is_installed  # 添加是否安装的标识
                    })

    cursor.close()
    conn.close()

    return {"code": 0, "msg": "", "count": len(plugins_list), "data": plugins_list}


# 删除我的插件ThePlugin.json
def delete_plugin(plugdir):
    try:
        if plugdir:
            # 构建ThePlugin.json文件的完整路径
            json_file_path = os.path.join(get_base_path('plugins'),plugdir,'ThePlugin.json')
            # 检查文件是否存在，并删除
            if os.path.exists(json_file_path):
                os.remove(json_file_path)
            print(json_file_path)
            return True
        else:
            print(f"找不到注册信息json文件")
            return False
    except Exception as e:
        print(f"删除注册信息错误: {e}")
        return False


# 读取指定插件信息（已安装）
def read_plugins(plugin_id):
    """根据插件ID读取插件信息"""
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 执行查询
    try:
        cursor.execute("SELECT * FROM MyPlugins WHERE ID = ?", (plugin_id,))
        plugin_data = cursor.fetchone()
        if plugin_data:
            # 将查询结果转换为字典
            keys = [description[0] for description in cursor.description]
            plugin_info = dict(zip(keys, plugin_data))
            return jsonify(plugin_info), 200
        else:
            return jsonify({"error": "Plugin not found"}), 404
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # 关闭数据库连接
        conn.close()

# 读取指定插件注册信息
def read_reg_plugins(plugdir):
    # 完整路径到 ThePlugin.json 文件
    json_file_path = os.path.join(get_base_path('plugins'),plugdir, 'ThePlugin.json')

    # 检查文件是否存在
    if os.path.exists(json_file_path):
        # 打开并读取 JSON 文件
        with open(json_file_path, 'r', encoding='utf-8') as file:
            plugin_data = json.load(file)
            print(plugin_data)
            return plugin_data
    else:
        # 如果文件不存在，返回一个错误消息
        return {"error": "ThePlugin.json 文件不存在."}


# 打包插件为zip
def zip_plugins(plugdir):
    # 获取插件目录路径
    print(plugdir)
    #plugins_directory = os.path.abspath('plugins',plugdir)  # 确保路径是绝对路径
    plugins_directory = get_base_path(f'plugins\\{plugdir}')
    print(plugins_directory)
    # 检查插件目录是否存在
    if not os.path.exists(plugins_directory):
        return f"找不到插件路径：{plugins_directory}", None, None

    # 创建内存中的文件
    memory_file = io.BytesIO()

    # 打包插件目录
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(plugins_directory):
            for file in files:
                file_path = os.path.join(root, file)
                # 计算存储在zip文件中的相对路径
                relative_path = os.path.relpath(file_path, start=os.path.dirname(plugins_directory))
                zipf.write(file_path, relative_path)

    memory_file.seek(0)

    # 插件目录名作为文件名
    directory_name = os.path.basename(plugins_directory)
    zip_filename = directory_name + '.zip'

    return "Successfully zipped the plugin", memory_file, zip_filename

# 扫描所有有注册插件，并返回json格式的列表
def read_plugin_info():
    plugins = []
    for dirname in os.listdir(PLUGINS_DIR):
        dir_path = os.path.join(PLUGINS_DIR, dirname)
        if os.path.isdir(dir_path):
            json_path = os.path.join(dir_path, 'ThePlugin.json')
            if os.path.exists(json_path):
                with open(json_path, 'r',encoding='utf-8') as file:
                    plugin_data = json.load(file)
                    plugin_data['PlugDir'] = dirname  # 添加目录名为字段
                    plugins.append(plugin_data)
    return plugins

# 查询数据库看是否插件已经安装
def check_installed_plugins(plugins):
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT PlugDir FROM MyPlugins')
    installed_dirs = {row[0] for row in cursor.fetchall()}
    # 更新插件安装状态
    for plugin in plugins:
        plugin['Installed'] = plugin['PlugDir'] in installed_dirs
    cursor.close()
    conn.close()
    return plugins

# 卸载插件
def unplugins(plug_dir):
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 查询需要删除的目录
        cursor.execute('SELECT uploadDir FROM MyPlugins WHERE PlugDir = ?', (plug_dir,))
        row = cursor.fetchone()
        if row:
            # 获取临时目录列表
            temp_dirs = row[0].split(',')
            # 遍历临时目录并删除
            for dir in temp_dirs:
                if dir:  # 确保dir不为空
                    temp_path = os.path.join(PLUGINS_DIR, plug_dir, dir.strip())  # 使用strip去除可能的空白字符
                    if os.path.exists(temp_path):
                        shutil.rmtree(temp_path)
                    else:
                        print(f"Directory not found: {temp_path}")
                else:
                    print("Empty directory name in database.")

            # 从数据库中删除插件记录
            cursor.execute('DELETE FROM MyPlugins WHERE PlugDir = ?', (plug_dir,))
            conn.commit()

            return jsonify({"code": 0, "msg": "Plugin uninstalled successfully"})
        else:
            return jsonify({"code": 1, "msg": "Plugin directory not found"})
    except Exception as e:
        conn.rollback()  # 发生异常时回滚
        print(f"Error occurred: {str(e)}")
        return jsonify({"code": 2, "msg": "Error occurred during uninstallation"})
    finally:
        cursor.close()
        conn.close()



"""<plugins插件路由交互执行>"""
#注册插件的交互
@plugins_blueprint.route('/reg_plugin', methods=['POST'])
def handle_register_plugins_Execution():
    if request.is_json:  # 确保请求包含 JSON 数据
        data = request.get_json()
        action = data.get('action')
        url = data.get('url')
        id = data.get('id')
        plugdir = data.get('plugdir')
        print(f'当前于plugins/reg_plugin路由action状态码：{action}')
        match action:
            case 'plugin_dir':  # 检测插件目录内容
                dir_name = data['dirName']
                base_path = 'plugins'
                full_path = os.path.join(base_path, dir_name)
                directory_structure = plugin_dir(full_path)
                return jsonify(directory_structure)

            case 'add_myplugin':#提交插件数据
                #dir_name = data['PlugDir']
                base_path = 'plugins'
                full_path = os.path.join(base_path, 'myplugin_temp.json')
                #file_name = 'myplugin_temp.json'
                #file_path = os.path.join(full_path, file_name)
                # 序列化data为JSON字符串并保存到文件
                with open(full_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                return jsonify({'status': 'success', 'message': '插件添加成功'})

            case 'exp_myplugins_list':  # 刷新插件列表
                response_data = fetch_exp_myplugins_list()
                return jsonify(response_data)

            case 'del_reg_plugins':  # 处理删除插件操作
                plugdir = plugdir.replace('plugins/', '')  # 移除 'plugins/' 前缀
                print(f'即将删除：{plugdir} 中的注册信息')
                if is_myplugins_DB('PlugDir', plugdir):
                    return jsonify({"status": "error", "message": "删除失败：因为插件已经安装，若要删除须先卸载"}), 200
                else:
                    if delete_plugin(plugdir):  # 调用之前定义的删除函数
                        return jsonify({"status": "success", "message": "插件信息删除成功"})
                    else:
                        return jsonify({"status": "error", "message": "删除插件信息失败"}), 500

            case 'read_reg_plugins':#读取指定插件信息
                print(plugdir)
                if plugdir:
                    return read_reg_plugins(plugdir)
                else:
                    return jsonify({"error": "读不到目录"}), 400

            case 'zip_plugins':#自研插件打包
                print(plugdir)
                message, memory_file, filename = zip_plugins(plugdir)
                print(f'message:{message}')
                print(f'memory_file:{memory_file}')
                print(f'filename:{filename}')
                if memory_file:
                    memory_file.seek(0)  # 确保指针回到文件开头
                    return send_file(
                        memory_file,
                        mimetype='application/zip',
                        as_attachment=True,
                        download_name=filename
                    )
                else:
                    return jsonify({"message": message}), 400


            case _:
                return jsonify({"error": "Invalid action or request method"}), 400
    else:
        return jsonify({'error': 'Invalid Content-Type'}), 400


# 用户应用插件中心交互
@plugins_blueprint.route('/user_plugins', methods=['POST'])
def handle_user_plugins_Execution():
    if request.is_json:  # 确保请求包含 JSON 数据
        data = request.get_json()
        action = data.get('action')
        url = data.get('url')
        id = data.get('id')
        print(f'当前于plugins/user_plugins路由action状态码：{action}')
        match action:
            case 'pluglist':  # 读取我的插件中心
                plugins = Plugins.query.all()
                return render_template('pluglist.html', plugins=plugins)

            case 'setup_plugins_list':  # 安装/卸载插件列表
                plugins = read_plugin_info()
                plugins = check_installed_plugins(plugins)
                print(plugins)
                return jsonify({
                    "code": 0,  # 成功的状态码为0
                    "msg": "",  # 可选的消息
                    "data": plugins  # 实际的数据
                })


            case 'unplugins':  # 卸载插件
                print('卸载插件')
                return unplugins(data['PlugDir'])

            case 'open_plugins_dir':
                directory_path = get_base_path('plugins\\')
                print(directory_path)
                return open_folder(directory_path)

            case 'read_plugins':#读取指定插件信息
                if id:
                    return read_plugins(id)
                else:
                    return jsonify({"error": "Missing plugin ID"}), 400

            case _:
                jsonify({"error": "Invalid action or request method"}), 400

    else:
        return jsonify({'error': 'Invalid Content-Type'}), 400


# 注册我的插件任务数
regplug_tasks = {
    'total': 9,  # 初始总任务数
    'completed': 0  # 初始已完成任务数
}
# 安装我的插件任务数
setupplug_tasks = {
    'total': 2,  # 初始总任务数
    'completed': 0  # 初始已完成任务数
}
def setup_socket_events(socketio):
    @socketio.on('reg_myplugin')
    def handle_reg_plugin(data):
        action = data.get('action')
        regplug_tasks['completed'] = 0
        if action == 'reg_myplugin':
            plugin_data = load_plugin_info()
            plugdir = plugin_data.get('PlugDir')
            plugname = plugin_data.get('PlugName')
            if plugin_data:
                # 1正在加载插件信息
                emit('reg_progress', {'message': '正在加载插件信息...'})
                regplug_tasks['completed'] += 1  # 递增已完成任务数
                progress = (regplug_tasks['completed'] / regplug_tasks['total']) * 100
                emit('reg_progress', {'message': '加载插件信息完毕！', 'progress': progress})

                # 2目录合法性检查
                emit('reg_progress', {'message': '正在进行目录合法性检查...'})
                time.sleep(1)
                check_result = check_plugin_directory(plugin_data)
                if check_result['status'] == 'success':
                    regplug_tasks['completed'] += 1  # 递增已完成任务数
                    progress = (regplug_tasks['completed'] / regplug_tasks['total']) * 100
                    # 目录合法性检查成功
                    emit('reg_progress', {'message': check_result['message'], 'progress': progress})
                else:
                    # 目录合法性检查失败，返回错误消息
                    emit('reg_progress', {'message': check_result['message'], 'status': 'error'})
                    return

                # 3检测插件名称
                emit('reg_progress', {'message': '检测插件名称...'})
                time.sleep(1)
                new_plug_name = check_and_rename_plug_name(plugname)

                regplug_tasks['completed'] += 1  # 递增已完成任务数
                progress = (regplug_tasks['completed'] / regplug_tasks['total']) * 100

                if new_plug_name != plugname:
                    plugin_data['PlugName'] = new_plug_name  # 更新插件名称
                    emit('reg_progress', {'message': f'插件名称重复，已改名为{new_plug_name}', 'progress': progress})
                else:
                    emit('reg_progress', {'message': '插件名称通过！', 'progress': progress})

                # 4检测ICO图标
                emit('reg_progress', {'message': '正在装载ICO图标...'})
                time.sleep(1)
                ico_path = load_icon(plugdir)

                plugin_data['ICO'] = ico_path.replace('\\', '/')

                regplug_tasks['completed'] += 1  # 递增已完成任务数
                progress = (regplug_tasks['completed'] / regplug_tasks['total']) * 100

                emit('reg_progress', {'message': '完成ICO图标装载！', 'progress': progress})

                # 5定义HTML主页
                emit('reg_progress', {'message': '正在定义HTML主页...'})
                time.sleep(1)
                plug_html = plugin_data.get('PlugHTML')

                if not plug_html.endswith('.html'):  # 如果PlugHTML未包含.html后缀，则添加
                    plug_html += '.html'
                    plugin_data['PlugHTML'] = plug_html  # 更新plugin_data中的PlugHTML

                check_html_result = check_html_main_page(plugdir, plug_html)

                if 'Error' in check_html_result:  # 根据check_html_main_page的返回结果决定是否继续执行
                    # 直接向前端发送错误消息，并停止执行
                    emit('reg_progress', {'message': check_html_result, 'progress': progress, 'status': 'error'})
                    return  # 早期返回，停止执行后续操作

                regplug_tasks['completed'] += 1  # 递增已完成任务数
                progress = (regplug_tasks['completed'] / regplug_tasks['total']) * 100
                emit('reg_progress', {'message': check_html_result, 'progress': progress})

                # 6修改HTML样式路径
                emit('reg_progress', {'message': '正在修改HTML样式路径...'})
                time.sleep(1)
                try:
                    update_resource_paths(plugdir)

                    regplug_tasks['completed'] += 1  # 递增已完成任务数
                    progress = (regplug_tasks['completed'] / regplug_tasks['total']) * 100

                    emit('reg_progress', {'message': 'HTML样式路径已修改！', 'progress': progress})
                except Exception as e:
                    # 发生异常，向前端发送失败消息
                    emit('reg_progress', {'message': f'修改HTML样式路径失败，异常原因是：{str(e)}', 'status': 'error'})
                    return

                # 7生成32位密钥
                emit('reg_progress', {'message': '正在生成32位密钥...'})
                time.sleep(1)
                try:
                    Keypass = generate_keypass()
                    plugin_data['Keypass'] = Keypass

                    regplug_tasks['completed'] += 1  # 递增已完成任务数
                    progress = (regplug_tasks['completed'] / regplug_tasks['total']) * 100

                    emit('reg_progress', {'message': f'生成32位密钥已经生成：{Keypass}', 'progress': progress})
                except Exception as e:
                    # 发生异常，向前端发送失败消息
                    emit('reg_progress', {'message': f'密钥生成失败，异常原因是：{str(e)}', 'status': 'error'})
                    return


                # 8保存插件信息
                emit('reg_progress', {'message': '正在注册插件信息...'})
                time.sleep(1)
                try:
                    # 尝试保存作者信息
                    save_author_info(plugin_data)

                    regplug_tasks['completed'] += 1  # 递增已完成任务数
                    progress = (regplug_tasks['completed'] / regplug_tasks['total']) * 100

                    emit('reg_progress', {'message': '插件信息已保存！', 'progress': progress})
                except Exception as e:
                    # 发生异常，向前端发送失败消息
                    emit('reg_progress', {'message': f'保存插件信息失败，异常原因是：{str(e)}', 'status': 'error'})
                    return

                # 9：最后删除Json文件
                emit('reg_progress', {'message': '安装即将完成...正在删除临时文件'})
                time.sleep(1)
                success, message = delete_temp_file()  # 调用删除临时文件的函数

                if success:
                    emit('reg_progress', {'message': message, 'progress': 100, 'status': 'success'})  # 发送安装完成的消息
                else:
                    emit('reg_progress', {'message': message, 'status': 'error'})  # 发送删除临时文件失败的消息
                    return

                if regplug_tasks['completed'] == regplug_tasks['total']:
                    emit('reg_progress', {'message': '插件安装完成！', 'progress': 100})

            else:
                # 加载插件信息失败，返回错误消息
                emit('reg_progress', {'message': '加载插件信息失败。', 'status': 'error'})
                return

    @socketio.on('setup_plugin')
    def handle_setup_plugin(data):
        action = data.get('action')
        plugdir = data.get('plugdir')
        if not plugdir.startswith('plugins\\'): plugdir = 'plugins\\' + plugdir
        plugins_dir = plugdir #带有plugins路径的值

        setupplug_tasks['completed'] = 0
        if action == 'setup_plugin':
            plugin_data = load_ThePlugin_json(plugdir)
            print(plugin_data)
            plugdir = plugin_data.get('PlugDir')
            plugname = plugin_data.get('PlugName')
            if plugin_data:

                # 1添加到数据库
                print("即将写入数据库")
                emit('setup_progress', {'message': '正在写入数据库（不要关闭窗口，否则会发生可怕的事）...'})
                time.sleep(1)
                try:
                    # 尝试写入数据库
                    result = write_to_database(plugin_data, db_path)
                    if result:
                        emit('setup_progress', {'message': result, 'status': 'error', 'progress': 100})
                        setupplug_tasks['completed'] = setupplug_tasks['total']  # 设置为完成状态
                        return  # 停止进一步执行

                    setupplug_tasks['completed'] += 1  # 递增已完成任务数
                    progress = (setupplug_tasks['completed'] / setupplug_tasks['total']) * 100
                    emit('setup_progress', {'message': '完成数据库写入操作！', 'progress': progress})
                    print("数据库写入成功")
                except Exception as e:
                    # 发生异常，向前端发送失败消息
                    emit('setup_progress', {'message': f'操作数据库失败，异常原因是：{str(e)}', 'status': 'error'})
                    print("数据库写入失败")
                    return

                # 2 注册蓝图
                print("即将注册蓝图")
                app = current_app
                emit('setup_progress', {'message': '正在注册插件蓝图...'})
                time.sleep(1)
                success, failure = setup_plugin_blueprint(plugdir)
                setupplug_tasks['completed'] += 1  # 递增已完成任务数
                progress = (setupplug_tasks['completed'] / setupplug_tasks['total']) * 100
                print(app.url_map)
                if failure > 0:
                    emit('setup_progress',
                         {'message': f'部分蓝图注册失败，但安装将继续进行！成功: {success}, 失败: {failure}',
                          'status': 'warning', 'progress': progress})
                    print("蓝图注册失败")
                else:
                    emit('setup_progress', {'message': f'所有蓝图注册成功！', 'status': 'success', 'progress': progress})
                    print("蓝图注册成功")



                # 3 依赖安装
                # print("正在检测并安装依赖...")
                # print("在虚拟环境中运行:", is_virtual_env())
                # print("推荐的 pip 路径:", get_pip_path())
                # emit('setup_progress', {'message': '正在检测并安装依赖...'})
                # dependencies = get_plugin_dependencies(plugins_dir)
                # installed_deps, failed_deps = install_dependencies(plugins_dir,dependencies)
                #
                # setupplug_tasks['completed'] += 1
                # progress = (setupplug_tasks['completed'] / setupplug_tasks['total']) * 100
                #
                # if installed_deps:
                #     emit('setup_progress',
                #          {'message': f'成功安装依赖: {", ".join(installed_deps)}', 'status': 'success', 'progress': progress})
                #
                # if failed_deps:
                #     failure_messages = "; ".join([f"{dep[0]}: {dep[1]}" for dep in failed_deps])
                #     emit('setup_progress',
                #          {'message': f'依赖安装失败: {failure_messages}', 'status': 'error', 'progress': progress})
                # else:
                #     emit('setup_progress', {'message': '所有依赖安装完成', 'status': 'success', 'progress': progress})

                # 写入HTML到数据库
                # emit('setup_progress', {'message': '正在操作HTML文件...'})
                # time.sleep(1)
                # try:
                #     result_messages = process_html_files(plugin_data, db_path)  # 获取操作结果和消息
                #     for msg in result_messages:
                #         emit('setup_progress', msg)  # 逐一发送消息
                #
                #     setupplug_tasks['completed'] += 1  # 递增已完成任务数
                #     progress = (setupplug_tasks['completed'] / setupplug_tasks['total']) * 100
                #
                #     emit('setup_progress', {'message': '完成对HTML的初始化！', 'progress': progress})
                # except Exception as e:
                #     emit('setup_progress', {'message': f'操作HTML文件失败，异常原因是：{str(e)}', 'status': 'error'})
                #     return


            else:
                # 加载插件信息失败，返回错误消息
                emit('setup_progress', {'message': '加载插件信息失败。', 'status': 'error'})
=======
from flask import jsonify, Flask, Blueprint, request, send_file, render_template,current_app
import sqlite3,os,json,requests,glob,random,string,re,zipfile,io,shutil,time,importlib,ast
from datetime import datetime
from flask_socketio import emit
from threading import Timer
from Ini_sys import *
from Ini_DB import *

plugins_blueprint = Blueprint('plugins', __name__)

PLUGINS_DIR = get_base_path('plugins')

"""<关于插件>"""
def install_plugin_dependencies():
    """遍历plugins目录并安装未注册插件的依赖"""
    print(f'正在准备扫描插件依赖，扫描目录：{PLUGINS_DIR}')
    print("pip 路径:", get_pip_path())
    for plugdir in os.listdir(PLUGINS_DIR):
        plugin_path = os.path.join(PLUGINS_DIR, plugdir)
        if plugdir in ['__pycache__', '__init__.py']:
            continue

        print(f'正在历遍并安装依赖：{plugin_path}')

        if os.path.isdir(plugin_path) and is_plugin_registered(plugdir):
            print(f"检查插件: {plugdir}")
            dependencies = get_plugin_dependencies(plugin_path)
            if dependencies:
                print(f"发现依赖项: {dependencies}, 正在安装...")
                installed_deps, failed_deps = install_dependencies(plugin_path, dependencies)
                if installed_deps:
                    print(f"成功安装依赖: {', '.join(installed_deps)}")
                if failed_deps:
                    print(f"安装失败的依赖: {', '.join([dep[0] for dep in failed_deps])}")
            else:
                print(f"插件 {plugdir} 没有依赖或依赖已安装。")
        else:
            print(f"插件 {plugdir} 未安装，跳过。")

# 加载插件的libs依赖目录
def load_plugin(plugin_name):
    plugin_dir = os.path.join(get_base_path('plugins'), plugin_name)
    libs_path = os.path.join(plugin_dir, 'libs')

    # 保存当前的 sys.path
    original_sys_path = sys.path.copy()
    try:
        # 将插件的目录和 libs 目录添加到 sys.path，前提是它们不在 sys.path 中
        if plugin_dir not in sys.path and os.path.exists(plugin_dir):
            sys.path.insert(0, plugin_dir)
            print(f'已添加插件{plugin_name}的目录：{plugin_dir}')
        if libs_path not in sys.path and os.path.exists(libs_path):
            sys.path.insert(0, libs_path)
            print(f'已添加插件{plugin_name}的依赖路径：{libs_path}')

        print(f'sys路径：{sys.path}')

        # 动态导入插件模块
        #module = importlib.import_module(plugin_name)
        #print(f'已成功导入插件{plugin_name}模块')

    except Exception as e:
        # 恢复原始的 sys.path
        sys.path = original_sys_path
        print(f"导入{plugin_name}插件时发生错误: {str(e)}")
    #return module
#若启动时不需要预先加载，以下是示例代码
# def handle_request(plugin_name, request_data):
#     plugin = load_plugin(plugin_name)
#     if plugin:
#         return plugin.handle(request_data)  # 假设插件有 handle 方法处理请求

#若要启动时自动扫描所有插件，则执行此函数
def load_all_plugins():
    plugin_dir = get_base_path('plugins')
    print(f'即将扫描插件依赖路径：{plugin_dir}')
    plugins = [name for name in os.listdir(plugin_dir) if os.path.isdir(os.path.join(plugin_dir, name))]
    for plugin_name in plugins:
        if is_plugin_registered(plugin_name):
            load_plugin(plugin_name)
        else:
            print(f'{plugin_name}该插件没有安装...跳过')

#历遍自定义插件里面的文件
def plugin_dir(path):
    """
    递归扫描指定路径下的所有文件和文件夹，并将其结构化为layui tree组件需要的格式。
    """
    path = get_base_path(path)
    tree = []
    if os.path.exists(path):
        for name in os.listdir(path):
            node_path = os.path.join(path, name)
            if os.path.isdir(node_path):
                tree.append({
                    "title": name,
                    "children": plugin_dir(node_path)
                })
            else:
                tree.append({"title": name})
    return tree

#提交我的插件-注册进程-加载myplugin_temp.json
def load_plugin_info():
    base_path = get_base_path('plugins')
    file_name = 'myplugin_temp.json'
    full_path = os.path.join(base_path, file_name)

    try:
        with open(full_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"Error:文件未找到: {full_path}")
    except json.JSONDecodeError:
        print(f"Error:JSON解析错误: {full_path}")
    except Exception as e:
        print(f"Error:加载插件信息时发生错误: {str(e)}")

    return None

#提交我的插件-安装进程-检测目录
def check_plugin_directory(plugin_data):
    base_path = get_base_path('plugins')
    plug_dir = plugin_data.get('PlugDir', '')

    # 构建插件目录的完整路径
    plugin_path = os.path.join(base_path, plug_dir)

    # 第一步：检查插件目录是否存在
    if not os.path.exists(plugin_path) or not os.path.isdir(plugin_path):
        return {'status': 'error', 'message': f"找不到插件目录：{plug_dir}"}

    # 第二步：检查main.py或main.exe是否存在
    # if not os.path.isfile(os.path.join(plugin_path, 'main.py')) and not os.path.isfile(os.path.join(plugin_path, 'main.exe')):
    #     return {'status': 'error', 'message': '找不到main主文件'}

    # 第三步：如果有main.py，检查是否有__init__.py
    if os.path.isfile(os.path.join(plugin_path, 'main.py')) and not os.path.isfile(os.path.join(plugin_path, '__init__.py')):
        return {'status': 'error', 'message': '缺少__init__.py文件'}

    # 第四步：检查是否有*.json文件，表示插件已注册
    if glob.glob(os.path.join(plugin_path, 'ThePlugin.json')):
        return {'status': 'error', 'message': '该插件已经注册'}

    # 第五步：检查indexpage目录及其下是否有html文件
    indexpage_path = os.path.join(plugin_path, 'static')
    if not os.path.exists(indexpage_path) or not any(fname.endswith('.html') for fname in os.listdir(indexpage_path)):
        return {'status': 'error', 'message': '找不到HTML主文件'}

    # 所有检查通过
    return {'status': 'success', 'message': '目录合法性检测成功！'}

#提交我的插件-安装进程-检测插件名称
def check_and_rename_plug_name(plug_name):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM MyPlugins WHERE PlugName = ?", (plug_name,))
    exists = cur.fetchone()[0] > 0

    if exists:
        # 如果名称存在，生成一个新的名称
        new_plug_name = plug_name + '_' + ''.join(random.choices(string.ascii_letters + string.digits, k=3))
        cur.close()
        conn.close()
        return new_plug_name
    else:
        cur.close()
        conn.close()
        return plug_name

#提交我的插件-安装进程-实时可保存myplugin_temp.json
def save_plugin_info(plugin_data):
    base_path = get_base_path('plugins')
    full_path = os.path.join(base_path, 'myplugin_temp.json')
    with open(full_path, 'w', encoding='utf-8') as f:
        json.dump(plugin_data, f, ensure_ascii=False, indent=4)

#提交我的插件-安装进程-装载ICO图标
def load_icon(plug_dir):
    base_path = get_base_path('plugins')
    target_path = os.path.join(base_path, plug_dir)

    plug_path = os.path.join(plug_dir)
    supported_formats = ('.jpg', '.png')
    icon_files = [f for f in os.listdir(target_path) if os.path.splitext(f)[1].lower() in supported_formats]

    if icon_files:
        # 随机选择一个ICO图标文件
        chosen_icon = random.choice(icon_files)
        icon_path = os.path.join(plug_path, chosen_icon)
    else:
        # 如果没有找到支持的文件格式，使用默认ICO图标
        icon_path = 'favicon.jpg'

    return icon_path

#提交我的插件-安装进程-定义HTML
def check_html_main_page(plug_dir, plug_html):
    base_path = get_base_path('plugins')
    indexpage_path = os.path.join(base_path, plug_dir, 'static')

    # 检查indexpage文件夹是否存在
    if not os.path.exists(indexpage_path):
        return 'Error:找不到HTML文件夹'

    # 确保plug_html以.html结尾
    if not plug_html.endswith('.html'):
        plug_html += '.html'

    # 检查指定的HTML文件是否存在
    html_file_path = os.path.join(indexpage_path, plug_html)
    if not os.path.isfile(html_file_path):
        return f'Error:找不到HTML主文件: {plug_html}'

    return '完成HTML主页定义！'

# 生成一个36位的随机密钥，包括大小写字母和数字
def generate_keypass(length=36):
    characters = string.ascii_letters + string.digits  # 包含大小写英文字母和数字
    return ''.join(random.choices(characters, k=length))



#提交我的插件-安装进程-保存开发信息
def save_author_info(plugin_data, base_path='plugins'):
    # 构造目标目录路径
    target_dir = os.path.join(get_base_path(base_path), plugin_data['PlugDir'])
    # 确保目标目录存在
    os.makedirs(target_dir, exist_ok=True)

    # 构造ThePlugin.json文件的完整路径
    json_file_path = os.path.join(target_dir, 'ThePlugin.json')

    # 准备保存的信息
    info_to_save = plugin_data.copy()  # 创建一个字典的副本，以避免修改原始数据

    # 添加创建日期
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    info_to_save['CreDate'] = now

    # 如果存在'action'键，并且其值为'add_myplugin'，则从字典中移除
    if info_to_save.get('action') == 'add_myplugin':
        del info_to_save['action']

    # 保存到ThePlugin.json文件
    with open(json_file_path, 'w', encoding='utf-8') as f:
        json.dump(info_to_save, f, ensure_ascii=False, indent=4)


    # # 构造目标目录路径
    # target_dir = os.path.join(base_path, plugin_data['PlugDir'])
    # # 确保目标目录存在
    # os.makedirs(target_dir, exist_ok=True)
    #
    # # 构造ThePlugin.json文件的完整路径
    # json_file_path = os.path.join(target_dir, 'ThePlugin.json')
    #
    # # 准备保存的信息
    # info_to_save = plugin_data.copy()  # 创建一个字典的副本，以避免修改原始数据
    #
    # # 如果存在'action'键，并且其值为'add_myplugin'，则从字典中移除
    # if info_to_save.get('action') == 'add_myplugin':
    #     del info_to_save['action']
    #
    # # 保存到ThePlugin.json文件
    # with open(json_file_path, 'w', encoding='utf-8') as f:
    #     json.dump(info_to_save, f, ensure_ascii=False, indent=4)

# 提交我的插件-安装进程-修改HTML样式路径
def update_resource_paths(plug_dir_name):
    # 构建完整的插件目录路径，加入了"plugins"上级目录
    plug_dir = os.path.join(get_base_path('plugins'), plug_dir_name)

    # 定义原路径和新路径的映射
    path_mappings = {
        r'layui\.css': '<link href="../../../static/res/layui/css/layui.css" rel="stylesheet">',
        r'admin\.css': '<link href="../../../static/res/adminui/dist/css/admin.css" rel="stylesheet">',
        r'jquery-3.6.0.min.js': '<script src="../../../static/res/jquery-3.6.0.min.js"></script>',
        r'layui.js': '<script src="../../../static/res/layui/layui.js"></script>',
        r'socket.io.js': '<script src="../../../static/res/socket.io.js"></script>'
    }

    # 构建搜索路径
    search_path = os.path.join(plug_dir, "static", "*.html")

    # 遍历所有HTML文件
    for file_path in glob.glob(search_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # 对每个路径进行检查和替换
        for original, new in path_mappings.items():
            # 构造正则表达式，捕获对应的文件引用
            pattern = re.compile(r'<.*?["\'].*?(' + original + r').*?["\'].*?>', re.IGNORECASE)
            # 如果找到匹配，则替换
            if pattern.search(content):
                content = pattern.sub(new, content)

        # 将修改后的内容写回文件
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)


# 提交我的插件-安装进程-写入HTML到数据库
def process_html_files(plugin_data, db_path):
    messages = []  # 用于存储操作结果和消息的列表
    base_path = get_base_path('plugins')
    plug_dir = plugin_data.get('PlugDir', '')
    dir_paths = {
        'static': os.path.join(base_path, plug_dir, 'static'),
        'templates': os.path.join(base_path, plug_dir, 'templates')
    }

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # 获取PlugID
        cur.execute("SELECT id FROM MyPlugins WHERE PlugDir = ?", (plug_dir,))
        plug_id_row = cur.fetchone()
        if plug_id_row:
            plug_id = plug_id_row[0]
        else:
            messages.append({'message': f'找不到{plug_dir}对应的插件ID', 'status': 'error'})
            return messages

        for dir_name, dir_path in dir_paths.items():
            if os.path.exists(dir_path):
                for file_name in os.listdir(dir_path):
                    if file_name.endswith('.html'):
                        file_path = os.path.join(dir_path, file_name)
                        with open(file_path, 'r', encoding='utf-8') as file:
                            code = file.read()

                            # 判断是否为IndexPage或Render
                            is_indexpage = (dir_name == 'static' and file_name == plugin_data.get('PlugHTML'))
                            is_render = (dir_name == 'templates')

                            # 写入数据库
                            cur.execute(
                                "INSERT INTO MyPlugins_HTML (HTMLDir, Code, IndexPage, Render, PlugID) VALUES (?, ?, ?, ?, ?)",
                                (file_path.replace(base_path, '').lstrip(os.sep), code, is_indexpage, is_render,
                                 plug_id))
            else:
                messages.append({'message': f'缺少{dir_name}文件夹', 'status': 'warning'})

        conn.commit()
    except Exception as e:
        conn.rollback()
        messages.append({'message': f'操作HTML文件失败，异常原因是：{str(e)}', 'status': 'error'})
    finally:
        conn.close()

    if not messages:  # 如果没有错误消息，表示操作成功
        messages.append({'message': '完成对HTML的初始化！', 'status': 'success'})

    return messages

# 提交我的插件-安装进程-最后一步，删除临时文件
def delete_temp_file(base_path='plugins', temp_file_name='myplugin_temp.json'):
    temp_file_path = os.path.join(get_base_path(base_path), temp_file_name)

    # 尝试删除文件
    try:
        os.remove(temp_file_path)
        return True, '安装完成！'  # 成功删除文件
    except OSError as e:
        return False, f'删除临时文件失败，异常原因是：{str(e)}'


"""<安装插件>"""
#安装插件-安装进程-加载ThePlugin.json.json
def load_ThePlugin_json(plugdir):
    base_path = get_base_path('plugins')
    file_name = 'ThePlugin.json'
    full_path = os.path.join(get_base_path(plugdir),file_name)
    print(full_path)
    try:
        with open(full_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"Error:文件未找到: {full_path}")
    except json.JSONDecodeError:
        print(f"Error:JSON解析错误: {full_path}")
    except Exception as e:
        print(f"Error:加载插件信息时发生错误: {str(e)}")

#安装插件-安装进程-写入数据库
def write_to_database(plugin_data, db_path):
    plugdir = plugin_data.get('PlugDir')

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # 检查数据库中是否已存在相同的 PlugDir
        cur.execute("SELECT COUNT(*) FROM MyPlugins WHERE PlugDir = ?", (plugdir,))
        if cur.fetchone()[0] > 0:
            return "该插件已经安装过了，无须再安装。"

        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        plugin_data.update({'UbDate': now})

        # 准备数据插入语句
        columns = ', '.join(plugin_data.keys())
        placeholders = ':' + ', :'.join(plugin_data.keys())
        sql = f"INSERT INTO MyPlugins ({columns}) VALUES ({placeholders})"
        cur.execute(sql, plugin_data)
        conn.commit()

    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

    return None  # 返回None表示无错误

    # data_to_insert = plugin_data.copy()
    # action = data_to_insert.pop('action', None)  # 移除action，但不修改原plugin_data
    #
    # try:
    #     conn = sqlite3.connect(db_path)
    #     cur = conn.cursor()
    #
    #     # 准备数据插入语句，注意不再包含action
    #     columns = ', '.join(data_to_insert.keys())
    #     placeholders = ':' + ', :'.join(data_to_insert.keys())
    #     sql = f"INSERT INTO MyPlugins ({columns}, CreDate, UbDate) VALUES ({placeholders}, :CreDate, :UbDate)"
    #
    #     now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #     data_to_insert.update({'CreDate': now, 'UbDate': now})
    #
    #     cur.execute(sql, data_to_insert)
    #     conn.commit()
    #
    # except Exception as e:
    #     # 回滚变更
    #     conn.rollback()
    #     # 使用id作为唯一标识进行数据删除
    #     if 'id' in plugin_data:
    #         cur.execute("DELETE FROM MyPlugins WHERE id = ?", (plugin_data['id'],))
    #         conn.commit()
    #     raise e  # 抛出异常供调用方处理
    #
    # finally:
    #     # 关闭数据库连接
    #     conn.close()

# 安装插件-安装进程-插件蓝图注册
def setup_plugin_blueprint(plugdir):
    app = current_app
    #app = current_app._get_current_object()
    success_count = 0
    failure_count = 0

    for dirpath, dirnames, filenames in os.walk(plugdir):
        for filename in filenames:
            if filename.endswith('.py') and not filename.startswith('__'):
                module_path = os.path.join(dirpath, filename[:-3]).replace('/', '.').replace('\\', '.')
                print(module_path)
                try:
                    mod = importlib.import_module(module_path)
                    if hasattr(mod, 'blueprint'):
                        app.register_blueprint(mod.blueprint)
                        success_count += 1
                        print(f"成功注册蓝图: {module_path}")
                    else:
                        print(f"模块中未找到蓝图: {module_path}")
                except Exception as e:
                    print(f"注册蓝图失败: {module_path}, 错误: {e}")
                    failure_count += 1
    print(app.url_map)
    return success_count, failure_count

"""<其它数据显示>"""
# 我的开发列表数据显示
def fetch_exp_myplugins_list(db_path=db_path):
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 获取所有已安装的插件目录
    cursor.execute("SELECT PlugDir FROM MyPlugins")
    installed_plugins = set(row[0] for row in cursor.fetchall())  # 现在是插件目录名的集合

    plugins_list = []
    # 遍历 PLUGINS_DIR 目录下的所有子目录
    for root, dirs, files in os.walk(PLUGINS_DIR):
        for dir in dirs:
            json_path = os.path.join(root, dir, 'ThePlugin.json')
            # 检查是否存在 ThePlugin.json 文件
            if os.path.isfile(json_path):
                # 读取 JSON 文件并解析数据
                with open(json_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                    # 判断当前插件是否已安装
                    is_installed = dir in installed_plugins  # 使用目录名而非完整路径进行比较
                    plugins_list.append({
                        "ID": data.get("ID", ""),
                        "PlugName": data.get("PlugName", ""),
                        "PlugDir": os.path.join(root, dir),
                        "Ver": data.get("Ver", ""),
                        "PlugDes": data.get("PlugDes", ""),
                        "CreDate": data.get("CreDate", ""),
                        "PlugHTML": data.get("PlugHTML", ""),
                        "isInstalled": is_installed  # 添加是否安装的标识
                    })

    cursor.close()
    conn.close()

    return {"code": 0, "msg": "", "count": len(plugins_list), "data": plugins_list}


# 删除我的插件ThePlugin.json
def delete_plugin(plugdir):
    try:
        if plugdir:
            # 构建ThePlugin.json文件的完整路径
            json_file_path = os.path.join(get_base_path('plugins'),plugdir,'ThePlugin.json')
            # 检查文件是否存在，并删除
            if os.path.exists(json_file_path):
                os.remove(json_file_path)
            print(json_file_path)
            return True
        else:
            print(f"找不到注册信息json文件")
            return False
    except Exception as e:
        print(f"删除注册信息错误: {e}")
        return False


# 读取指定插件信息（已安装）
def read_plugins(plugin_id):
    """根据插件ID读取插件信息"""
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 执行查询
    try:
        cursor.execute("SELECT * FROM MyPlugins WHERE ID = ?", (plugin_id,))
        plugin_data = cursor.fetchone()
        if plugin_data:
            # 将查询结果转换为字典
            keys = [description[0] for description in cursor.description]
            plugin_info = dict(zip(keys, plugin_data))
            return jsonify(plugin_info), 200
        else:
            return jsonify({"error": "Plugin not found"}), 404
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # 关闭数据库连接
        conn.close()

# 读取指定插件注册信息
def read_reg_plugins(plugdir):
    # 完整路径到 ThePlugin.json 文件
    json_file_path = os.path.join(get_base_path('plugins'),plugdir, 'ThePlugin.json')

    # 检查文件是否存在
    if os.path.exists(json_file_path):
        # 打开并读取 JSON 文件
        with open(json_file_path, 'r', encoding='utf-8') as file:
            plugin_data = json.load(file)
            print(plugin_data)
            return plugin_data
    else:
        # 如果文件不存在，返回一个错误消息
        return {"error": "ThePlugin.json 文件不存在."}


# 打包插件为zip
def zip_plugins(plugdir):
    # 获取插件目录路径
    print(plugdir)
    #plugins_directory = os.path.abspath('plugins',plugdir)  # 确保路径是绝对路径
    plugins_directory = get_base_path(f'plugins\\{plugdir}')
    print(plugins_directory)
    # 检查插件目录是否存在
    if not os.path.exists(plugins_directory):
        return f"找不到插件路径：{plugins_directory}", None, None

    # 创建内存中的文件
    memory_file = io.BytesIO()

    # 打包插件目录
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(plugins_directory):
            for file in files:
                file_path = os.path.join(root, file)
                # 计算存储在zip文件中的相对路径
                relative_path = os.path.relpath(file_path, start=os.path.dirname(plugins_directory))
                zipf.write(file_path, relative_path)

    memory_file.seek(0)

    # 插件目录名作为文件名
    directory_name = os.path.basename(plugins_directory)
    zip_filename = directory_name + '.zip'

    return "Successfully zipped the plugin", memory_file, zip_filename

# 扫描所有有注册插件，并返回json格式的列表
def read_plugin_info():
    plugins = []
    for dirname in os.listdir(PLUGINS_DIR):
        dir_path = os.path.join(PLUGINS_DIR, dirname)
        if os.path.isdir(dir_path):
            json_path = os.path.join(dir_path, 'ThePlugin.json')
            if os.path.exists(json_path):
                with open(json_path, 'r',encoding='utf-8') as file:
                    plugin_data = json.load(file)
                    plugin_data['PlugDir'] = dirname  # 添加目录名为字段
                    plugins.append(plugin_data)
    return plugins

# 查询数据库看是否插件已经安装
def check_installed_plugins(plugins):
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT PlugDir FROM MyPlugins')
    installed_dirs = {row[0] for row in cursor.fetchall()}
    # 更新插件安装状态
    for plugin in plugins:
        plugin['Installed'] = plugin['PlugDir'] in installed_dirs
    cursor.close()
    conn.close()
    return plugins

# 卸载插件
def unplugins(plug_dir):
    # 连接数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 查询需要删除的目录
        cursor.execute('SELECT uploadDir FROM MyPlugins WHERE PlugDir = ?', (plug_dir,))
        row = cursor.fetchone()
        if row:
            # 获取临时目录列表
            temp_dirs = row[0].split(',')
            # 遍历临时目录并删除
            for dir in temp_dirs:
                if dir:  # 确保dir不为空
                    temp_path = os.path.join(PLUGINS_DIR, plug_dir, dir.strip())  # 使用strip去除可能的空白字符
                    if os.path.exists(temp_path):
                        shutil.rmtree(temp_path)
                    else:
                        print(f"Directory not found: {temp_path}")
                else:
                    print("Empty directory name in database.")

            # 从数据库中删除插件记录
            cursor.execute('DELETE FROM MyPlugins WHERE PlugDir = ?', (plug_dir,))
            conn.commit()

            return jsonify({"code": 0, "msg": "Plugin uninstalled successfully"})
        else:
            return jsonify({"code": 1, "msg": "Plugin directory not found"})
    except Exception as e:
        conn.rollback()  # 发生异常时回滚
        print(f"Error occurred: {str(e)}")
        return jsonify({"code": 2, "msg": "Error occurred during uninstallation"})
    finally:
        cursor.close()
        conn.close()



"""<plugins插件路由交互执行>"""
#注册插件的交互
@plugins_blueprint.route('/reg_plugin', methods=['POST'])
def handle_register_plugins_Execution():
    if request.is_json:  # 确保请求包含 JSON 数据
        data = request.get_json()
        action = data.get('action')
        url = data.get('url')
        id = data.get('id')
        plugdir = data.get('plugdir')
        print(f'当前于plugins/reg_plugin路由action状态码：{action}')
        match action:
            case 'plugin_dir':  # 检测插件目录内容
                dir_name = data['dirName']
                base_path = 'plugins'
                full_path = os.path.join(base_path, dir_name)
                directory_structure = plugin_dir(full_path)
                return jsonify(directory_structure)

            case 'add_myplugin':#提交插件数据
                #dir_name = data['PlugDir']
                base_path = 'plugins'
                full_path = os.path.join(base_path, 'myplugin_temp.json')
                #file_name = 'myplugin_temp.json'
                #file_path = os.path.join(full_path, file_name)
                # 序列化data为JSON字符串并保存到文件
                with open(full_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
                return jsonify({'status': 'success', 'message': '插件添加成功'})

            case 'exp_myplugins_list':  # 刷新插件列表
                response_data = fetch_exp_myplugins_list()
                return jsonify(response_data)

            case 'del_reg_plugins':  # 处理删除插件操作
                plugdir = plugdir.replace('plugins/', '')  # 移除 'plugins/' 前缀
                print(f'即将删除：{plugdir} 中的注册信息')
                if is_myplugins_DB('PlugDir', plugdir):
                    return jsonify({"status": "error", "message": "删除失败：因为插件已经安装，若要删除须先卸载"}), 200
                else:
                    if delete_plugin(plugdir):  # 调用之前定义的删除函数
                        return jsonify({"status": "success", "message": "插件信息删除成功"})
                    else:
                        return jsonify({"status": "error", "message": "删除插件信息失败"}), 500

            case 'read_reg_plugins':#读取指定插件信息
                print(plugdir)
                if plugdir:
                    return read_reg_plugins(plugdir)
                else:
                    return jsonify({"error": "读不到目录"}), 400

            case 'zip_plugins':#自研插件打包
                print(plugdir)
                message, memory_file, filename = zip_plugins(plugdir)
                print(f'message:{message}')
                print(f'memory_file:{memory_file}')
                print(f'filename:{filename}')
                if memory_file:
                    memory_file.seek(0)  # 确保指针回到文件开头
                    return send_file(
                        memory_file,
                        mimetype='application/zip',
                        as_attachment=True,
                        download_name=filename
                    )
                else:
                    return jsonify({"message": message}), 400


            case _:
                return jsonify({"error": "Invalid action or request method"}), 400
    else:
        return jsonify({'error': 'Invalid Content-Type'}), 400


# 用户应用插件中心交互
@plugins_blueprint.route('/user_plugins', methods=['POST'])
def handle_user_plugins_Execution():
    if request.is_json:  # 确保请求包含 JSON 数据
        data = request.get_json()
        action = data.get('action')
        url = data.get('url')
        id = data.get('id')
        print(f'当前于plugins/user_plugins路由action状态码：{action}')
        match action:
            case 'pluglist':  # 读取我的插件中心
                plugins = Plugins.query.all()
                return render_template('pluglist.html', plugins=plugins)

            case 'setup_plugins_list':  # 安装/卸载插件列表
                plugins = read_plugin_info()
                plugins = check_installed_plugins(plugins)
                print(plugins)
                return jsonify({
                    "code": 0,  # 成功的状态码为0
                    "msg": "",  # 可选的消息
                    "data": plugins  # 实际的数据
                })


            case 'unplugins':  # 卸载插件
                print('卸载插件')
                return unplugins(data['PlugDir'])

            case 'open_plugins_dir':
                directory_path = get_base_path('plugins\\')
                print(directory_path)
                return open_folder(directory_path)

            case 'read_plugins':#读取指定插件信息
                if id:
                    return read_plugins(id)
                else:
                    return jsonify({"error": "Missing plugin ID"}), 400

            case _:
                jsonify({"error": "Invalid action or request method"}), 400

    else:
        return jsonify({'error': 'Invalid Content-Type'}), 400


# 注册我的插件任务数
regplug_tasks = {
    'total': 9,  # 初始总任务数
    'completed': 0  # 初始已完成任务数
}
# 安装我的插件任务数
setupplug_tasks = {
    'total': 2,  # 初始总任务数
    'completed': 0  # 初始已完成任务数
}
def setup_socket_events(socketio):
    @socketio.on('reg_myplugin')
    def handle_reg_plugin(data):
        action = data.get('action')
        regplug_tasks['completed'] = 0
        if action == 'reg_myplugin':
            plugin_data = load_plugin_info()
            plugdir = plugin_data.get('PlugDir')
            plugname = plugin_data.get('PlugName')
            if plugin_data:
                # 1正在加载插件信息
                emit('reg_progress', {'message': '正在加载插件信息...'})
                regplug_tasks['completed'] += 1  # 递增已完成任务数
                progress = (regplug_tasks['completed'] / regplug_tasks['total']) * 100
                emit('reg_progress', {'message': '加载插件信息完毕！', 'progress': progress})

                # 2目录合法性检查
                emit('reg_progress', {'message': '正在进行目录合法性检查...'})
                time.sleep(1)
                check_result = check_plugin_directory(plugin_data)
                if check_result['status'] == 'success':
                    regplug_tasks['completed'] += 1  # 递增已完成任务数
                    progress = (regplug_tasks['completed'] / regplug_tasks['total']) * 100
                    # 目录合法性检查成功
                    emit('reg_progress', {'message': check_result['message'], 'progress': progress})
                else:
                    # 目录合法性检查失败，返回错误消息
                    emit('reg_progress', {'message': check_result['message'], 'status': 'error'})
                    return

                # 3检测插件名称
                emit('reg_progress', {'message': '检测插件名称...'})
                time.sleep(1)
                new_plug_name = check_and_rename_plug_name(plugname)

                regplug_tasks['completed'] += 1  # 递增已完成任务数
                progress = (regplug_tasks['completed'] / regplug_tasks['total']) * 100

                if new_plug_name != plugname:
                    plugin_data['PlugName'] = new_plug_name  # 更新插件名称
                    emit('reg_progress', {'message': f'插件名称重复，已改名为{new_plug_name}', 'progress': progress})
                else:
                    emit('reg_progress', {'message': '插件名称通过！', 'progress': progress})

                # 4检测ICO图标
                emit('reg_progress', {'message': '正在装载ICO图标...'})
                time.sleep(1)
                ico_path = load_icon(plugdir)

                plugin_data['ICO'] = ico_path.replace('\\', '/')

                regplug_tasks['completed'] += 1  # 递增已完成任务数
                progress = (regplug_tasks['completed'] / regplug_tasks['total']) * 100

                emit('reg_progress', {'message': '完成ICO图标装载！', 'progress': progress})

                # 5定义HTML主页
                emit('reg_progress', {'message': '正在定义HTML主页...'})
                time.sleep(1)
                plug_html = plugin_data.get('PlugHTML')

                if not plug_html.endswith('.html'):  # 如果PlugHTML未包含.html后缀，则添加
                    plug_html += '.html'
                    plugin_data['PlugHTML'] = plug_html  # 更新plugin_data中的PlugHTML

                check_html_result = check_html_main_page(plugdir, plug_html)

                if 'Error' in check_html_result:  # 根据check_html_main_page的返回结果决定是否继续执行
                    # 直接向前端发送错误消息，并停止执行
                    emit('reg_progress', {'message': check_html_result, 'progress': progress, 'status': 'error'})
                    return  # 早期返回，停止执行后续操作

                regplug_tasks['completed'] += 1  # 递增已完成任务数
                progress = (regplug_tasks['completed'] / regplug_tasks['total']) * 100
                emit('reg_progress', {'message': check_html_result, 'progress': progress})

                # 6修改HTML样式路径
                emit('reg_progress', {'message': '正在修改HTML样式路径...'})
                time.sleep(1)
                try:
                    update_resource_paths(plugdir)

                    regplug_tasks['completed'] += 1  # 递增已完成任务数
                    progress = (regplug_tasks['completed'] / regplug_tasks['total']) * 100

                    emit('reg_progress', {'message': 'HTML样式路径已修改！', 'progress': progress})
                except Exception as e:
                    # 发生异常，向前端发送失败消息
                    emit('reg_progress', {'message': f'修改HTML样式路径失败，异常原因是：{str(e)}', 'status': 'error'})
                    return

                # 7生成32位密钥
                emit('reg_progress', {'message': '正在生成32位密钥...'})
                time.sleep(1)
                try:
                    Keypass = generate_keypass()
                    plugin_data['Keypass'] = Keypass

                    regplug_tasks['completed'] += 1  # 递增已完成任务数
                    progress = (regplug_tasks['completed'] / regplug_tasks['total']) * 100

                    emit('reg_progress', {'message': f'生成32位密钥已经生成：{Keypass}', 'progress': progress})
                except Exception as e:
                    # 发生异常，向前端发送失败消息
                    emit('reg_progress', {'message': f'密钥生成失败，异常原因是：{str(e)}', 'status': 'error'})
                    return


                # 8保存插件信息
                emit('reg_progress', {'message': '正在注册插件信息...'})
                time.sleep(1)
                try:
                    # 尝试保存作者信息
                    save_author_info(plugin_data)

                    regplug_tasks['completed'] += 1  # 递增已完成任务数
                    progress = (regplug_tasks['completed'] / regplug_tasks['total']) * 100

                    emit('reg_progress', {'message': '插件信息已保存！', 'progress': progress})
                except Exception as e:
                    # 发生异常，向前端发送失败消息
                    emit('reg_progress', {'message': f'保存插件信息失败，异常原因是：{str(e)}', 'status': 'error'})
                    return

                # 9：最后删除Json文件
                emit('reg_progress', {'message': '安装即将完成...正在删除临时文件'})
                time.sleep(1)
                success, message = delete_temp_file()  # 调用删除临时文件的函数

                if success:
                    emit('reg_progress', {'message': message, 'progress': 100, 'status': 'success'})  # 发送安装完成的消息
                else:
                    emit('reg_progress', {'message': message, 'status': 'error'})  # 发送删除临时文件失败的消息
                    return

                if regplug_tasks['completed'] == regplug_tasks['total']:
                    emit('reg_progress', {'message': '插件安装完成！', 'progress': 100})

            else:
                # 加载插件信息失败，返回错误消息
                emit('reg_progress', {'message': '加载插件信息失败。', 'status': 'error'})
                return

    @socketio.on('setup_plugin')
    def handle_setup_plugin(data):
        action = data.get('action')
        plugdir = data.get('plugdir')
        if not plugdir.startswith('plugins\\'): plugdir = 'plugins\\' + plugdir
        plugins_dir = plugdir #带有plugins路径的值

        setupplug_tasks['completed'] = 0
        if action == 'setup_plugin':
            plugin_data = load_ThePlugin_json(plugdir)
            print(plugin_data)
            plugdir = plugin_data.get('PlugDir')
            plugname = plugin_data.get('PlugName')
            if plugin_data:

                # 1添加到数据库
                print("即将写入数据库")
                emit('setup_progress', {'message': '正在写入数据库（不要关闭窗口，否则会发生可怕的事）...'})
                time.sleep(1)
                try:
                    # 尝试写入数据库
                    result = write_to_database(plugin_data, db_path)
                    if result:
                        emit('setup_progress', {'message': result, 'status': 'error', 'progress': 100})
                        setupplug_tasks['completed'] = setupplug_tasks['total']  # 设置为完成状态
                        return  # 停止进一步执行

                    setupplug_tasks['completed'] += 1  # 递增已完成任务数
                    progress = (setupplug_tasks['completed'] / setupplug_tasks['total']) * 100
                    emit('setup_progress', {'message': '完成数据库写入操作！', 'progress': progress})
                    print("数据库写入成功")
                except Exception as e:
                    # 发生异常，向前端发送失败消息
                    emit('setup_progress', {'message': f'操作数据库失败，异常原因是：{str(e)}', 'status': 'error'})
                    print("数据库写入失败")
                    return

                # 2 注册蓝图
                print("即将注册蓝图")
                app = current_app
                emit('setup_progress', {'message': '正在注册插件蓝图...'})
                time.sleep(1)
                success, failure = setup_plugin_blueprint(plugdir)
                setupplug_tasks['completed'] += 1  # 递增已完成任务数
                progress = (setupplug_tasks['completed'] / setupplug_tasks['total']) * 100
                print(app.url_map)
                if failure > 0:
                    emit('setup_progress',
                         {'message': f'部分蓝图注册失败，但安装将继续进行！成功: {success}, 失败: {failure}',
                          'status': 'warning', 'progress': progress})
                    print("蓝图注册失败")
                else:
                    emit('setup_progress', {'message': f'所有蓝图注册成功！', 'status': 'success', 'progress': progress})
                    print("蓝图注册成功")



                # 3 依赖安装
                # print("正在检测并安装依赖...")
                # print("在虚拟环境中运行:", is_virtual_env())
                # print("推荐的 pip 路径:", get_pip_path())
                # emit('setup_progress', {'message': '正在检测并安装依赖...'})
                # dependencies = get_plugin_dependencies(plugins_dir)
                # installed_deps, failed_deps = install_dependencies(plugins_dir,dependencies)
                #
                # setupplug_tasks['completed'] += 1
                # progress = (setupplug_tasks['completed'] / setupplug_tasks['total']) * 100
                #
                # if installed_deps:
                #     emit('setup_progress',
                #          {'message': f'成功安装依赖: {", ".join(installed_deps)}', 'status': 'success', 'progress': progress})
                #
                # if failed_deps:
                #     failure_messages = "; ".join([f"{dep[0]}: {dep[1]}" for dep in failed_deps])
                #     emit('setup_progress',
                #          {'message': f'依赖安装失败: {failure_messages}', 'status': 'error', 'progress': progress})
                # else:
                #     emit('setup_progress', {'message': '所有依赖安装完成', 'status': 'success', 'progress': progress})

                # 写入HTML到数据库
                # emit('setup_progress', {'message': '正在操作HTML文件...'})
                # time.sleep(1)
                # try:
                #     result_messages = process_html_files(plugin_data, db_path)  # 获取操作结果和消息
                #     for msg in result_messages:
                #         emit('setup_progress', msg)  # 逐一发送消息
                #
                #     setupplug_tasks['completed'] += 1  # 递增已完成任务数
                #     progress = (setupplug_tasks['completed'] / setupplug_tasks['total']) * 100
                #
                #     emit('setup_progress', {'message': '完成对HTML的初始化！', 'progress': progress})
                # except Exception as e:
                #     emit('setup_progress', {'message': f'操作HTML文件失败，异常原因是：{str(e)}', 'status': 'error'})
                #     return


            else:
                # 加载插件信息失败，返回错误消息
                emit('setup_progress', {'message': '加载插件信息失败。', 'status': 'error'})
>>>>>>> 33969d2a895ce8a09fca410185bb3cfa811bfe73
                return