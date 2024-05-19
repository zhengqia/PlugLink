from flask import jsonify, Flask, Blueprint, request, send_file, render_template
import json,subprocess,locale,importlib.util
from Ini_sys import *
from Ini_DB import *
from flask_socketio import emit

workflow_blueprint = Blueprint('workflow', __name__)

# 假设的工作流状态存储
workflow_status = {}
WF_list = {}
# 检测api.py文件是否存在
def does_api_file_exist(plugin_dir):
    # 构建 api.py 文件的完整路径
    api_file_path = os.path.join(get_base_path('plugins'), plugin_dir, 'api.py')
    # 检查 api.py 文件是否存在
    return os.path.isfile(api_file_path)

# 加载插件api
def load_plugin_module(plugin_path,plugin_name):
    plugin_path = get_base_path(plugin_path)
    #spec = importlib.util.spec_from_file_location(module_path)
    print(f"Loading module from: {plugin_path}")  # 调试信息

    spec = importlib.util.spec_from_file_location(plugin_name,plugin_path)
    if spec is None:
        raise ImportError(f"Could not load spec for {plugin_path}")

    module = importlib.util.module_from_spec(spec)
    if spec.loader is None:
        raise ImportError(f"No loader found for {plugin_path}")

    spec.loader.exec_module(module)
    return module

# 创建工作流
def Creation_workflow(WFName,WFDes):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 检查工作流名称是否已存在
    cursor.execute("SELECT * FROM WorkFlow WHERE WorkFlowName=?", (WFName,))
    existing_workflow = cursor.fetchone()
    if existing_workflow:
        return jsonify({'error': '不能使用已有名称'}), 400

    # 插入新工作流并获取新创建的工作流的ID
    cursor.execute("INSERT INTO WorkFlow (WorkFlowName, WorkFlowDes) VALUES (?,?)", (WFName, WFDes))
    conn.commit()
    # 获取新插入行的ID
    new_workflow_id = cursor.lastrowid

    # 关闭数据库连接
    cursor.close()
    conn.close()

    # 返回成功信息以及新创建的工作流ID
    return jsonify({'id': new_workflow_id, 'message': '工作流创建成功！'})

# 加载子流数据
def load_sub_workflow(workflow_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    if workflow_id:
        cursor.execute("SELECT WorkFlowName, PlugName, Sort, PlugDes FROM sub_WorkFlow WHERE WorkFlowID = ?",
                       (workflow_id,))
        rows = cursor.fetchall()
        conn.close()

        if cursor.rowcount == 0:
            return jsonify({'error': 'No data found for the given ID.'}), 404

        result = []
        for row in rows:
            result.append({
                'WorkFlowName': row[0],
                'PlugName': row[1],
                'Sort': row[2],
                'PlugDes': row[3]
            })

        return jsonify({'data': result})
    else:
        return jsonify({'error': 'Missing ID parameter.'}), 400


# 在工作流中添加插件
def add_plugin_to_workflow(workflow_name, workflow_id, plug_name, plug_dir, plug_des, plug_id):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    try:
        # Check the current maximum sort value for the given workflow ID
        cursor.execute("SELECT MAX(Sort) FROM sub_WorkFlow WHERE WorkFlowID = ?", (workflow_id,))
        max_sort = cursor.fetchone()[0]
        new_sort = max_sort + 1 if max_sort is not None else 1

        # Insert the new plugin into the sub_WorkFlow table
        cursor.execute("""
            INSERT INTO sub_WorkFlow (WorkFlowName, WorkFlowID, PlugName, PlugDir, PlugDes, PlugID, Sort)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (workflow_name, workflow_id, plug_name, plug_dir, plug_des, plug_id, new_sort))

        connection.commit()
        return True, "Plugin added successfully"
    except sqlite3.Error as e:
        return False, str(e)
    finally:
        cursor.close()
        connection.close()

# 修改排序
def move_sub_workflow(sub_workflow_id, action):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT ID, Sort, WorkFlowID FROM sub_WorkFlow WHERE ID = ?', (sub_workflow_id,))
    item = cursor.fetchone()

    if not item:
        conn.close()
        return jsonify({'status': 'error', 'message': 'Item not found'})

    current_sort = item['Sort']
    target_sort = current_sort - 1 if action == 'up_sub_WF' else current_sort + 1

    cursor.execute('SELECT MIN(Sort) AS min_sort, MAX(Sort) AS max_sort FROM sub_WorkFlow WHERE WorkFlowID = ?',
                   (item['WorkFlowID'],))
    bounds = cursor.fetchone()
    if (action == 'up_sub_WF' and current_sort <= bounds['min_sort']) or (
            action == 'down_sub_WF' and current_sort >= bounds['max_sort']):
        conn.close()
        return jsonify({'status': 'error', 'message': 'No more moves available'})

    cursor.execute('UPDATE sub_WorkFlow SET Sort = ? WHERE Sort = ? AND WorkFlowID = ?',
                   (current_sort, target_sort, item['WorkFlowID']))
    cursor.execute('UPDATE sub_WorkFlow SET Sort = ? WHERE ID = ?', (target_sort, sub_workflow_id))
    conn.commit()

    cursor.execute('SELECT ID FROM sub_WorkFlow WHERE WorkFlowID = ? ORDER BY Sort', (item['WorkFlowID'],))
    sub_workflows = cursor.fetchall()
    for i, sub_workflow in enumerate(sub_workflows, start=1):
        cursor.execute('UPDATE sub_WorkFlow SET Sort = ? WHERE ID = ?', (i, sub_workflow['ID']))

    conn.commit()
    conn.close()

    return jsonify({'status': 'success', 'message': 'Sort order updated successfully'})


# 获取插件HTML首页
def check_plugin_existence(plug_dir):
    conn = get_db_connection()
    cur = conn.cursor()
    print(plug_dir)
    cur.execute('SELECT PlugHTML FROM MyPlugins WHERE PlugDir = ?', (plug_dir,))
    plugin = cur.fetchone()
    conn.close()

    if plugin:
        print("Database returned:", plugin)
        plug_html = plugin['PlugHTML'] if 'PlugHTML' in plugin.keys() else None
        if plug_html:
            return jsonify({'exists': True, 'PlugHTML': plug_html})
        else:
            print("PlusHTML is missing or empty")
            return jsonify({'exists': False})

    else:
        print("No database entry found for PlugDir:", plug_dir)
        return jsonify({'exists': False})

# 加载插件中的json文件
def load_plugjson(dir):
    """ Load JSON data from the specified directory """
    try:
        path = os.path.join('plugins', dir, 'api.json')
        with open(path, 'r', encoding='utf-8') as file:
            content = json.load(file)
        return jsonify(content)
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 保存插件json文件
def save_plugjson(dir, json_content):
    try:
        if not json_content:
            return jsonify({'error': '找不到json数据'}), 400
        # 尝试解析 JSON 数据
        data = json.loads(json_content)

        # 验证 JSON 数据是否有效
        if not is_json_valid(json.dumps(data)):
            return jsonify({'error': 'JSON格式不正确，无法保存'}), 400

        # 遍历数据，并确保所有科学计数法的数字被视为字符串
        def stringify_scientific_notation(obj):
            if isinstance(obj, dict):
                for key in obj:
                    obj[key] = stringify_scientific_notation(obj[key])
            elif isinstance(obj, list):
                return [stringify_scientific_notation(item) for item in obj]
            elif isinstance(obj, float):
                if obj.is_integer():
                    return int(obj)
                else:
                    return '{:.15g}'.format(obj)
            return obj

        data = stringify_scientific_notation(data)

        # 构建文件路径并保存 JSON 文件
        path = os.path.join('plugins', dir, 'api.json')
        path = get_base_path(path)
        print(f'保存json文件：{path}')
        with open(path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4)
        return jsonify({'success': 'Data saved successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 更改工作流模块json数据库文件
def update_workflow_json(wf_id, json_content):
    # 这里需要写数据库操作的代码
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE sub_WorkFlow SET JSON = ? WHERE ID = ?', (json_content, wf_id))
        conn.commit()
        if cursor.rowcount == 0:
            return False, "找不到数据，检查该ID是否存在."
        return True, "JSON 记录更新成功."
    except sqlite3.Error as e:
        return False, str(e)
    finally:
        conn.close()

# 加载插件JSON-数据库
def load_json_data(workflow_id):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT JSON FROM sub_WorkFlow WHERE id = ?', (workflow_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            # 确保正确解码中文
            data = json.loads(row[0])
            formatted_json = json.dumps(data, indent=4, ensure_ascii=False)
            return jsonify({'JSON': formatted_json, 'status': 'success'})
        else:
            return jsonify({'JSON': '', 'status': 'error', 'message': 'No data found'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# 保存插件JSON-数据库
def save_json_data(workflow_id, json_data):
    try:
        # 确保数据是字符串并且是格式化的 JSON
        data = json.loads(json_data)
        if not is_json_valid(json.dumps(data)):
            return jsonify({'status': 'error', 'message': 'JSON格式不正确，无法保存'})

        json_string = json.dumps(data, indent=4, ensure_ascii=False)

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE sub_WorkFlow SET JSON = ? WHERE id = ?', (json_string, workflow_id))
        conn.commit()
        conn.close()
        return jsonify({'status': 'success', 'message': 'JSON数据保存成功'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

# 加载工作流所有脚本
def load_config(WorkFlowID,Bfun=True):
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute('''
        SELECT ID, PlugDir, Sort, JSON FROM sub_WorkFlow WHERE WorkFlowID = ? ORDER BY Sort ASC
    ''', (WorkFlowID,))
    rows = cursor.fetchall()
    connection.close()

    # Sfun = ''
    # if Bfun:
    #     Sfun = 'test_connection'

    scripts = []
    for index, row in enumerate(rows):
        id, plug_dir, sort, json_field = row
        script_name = f"plugins/{plug_dir}/api.py"
        dependencies = [r[0] for r in rows[:index]]  # 选择之前所有脚本的ID
        script = {
            "id": id,
            "name": script_name,
            #"function": Sfun,
            "dependencies": dependencies,# 上级依赖关系
            "json": json_field  # 存储 JSON 字段
        }
        scripts.append(script)

    if Bfun:
        print(f'带参数流集：{scripts}')
    else:
        print(f'无参数流集：{scripts}')

    return {"scripts": scripts}

# 在插件目录下生成json文件，以便插件调用
def WF_save_json(path, jsonfilename,json_data):
    path = get_base_path(path)
    # 确保路径存在
    os.makedirs(path, exist_ok=True)

    # 完整的文件路径
    full_path = os.path.join(path, jsonfilename)
    print(f'保存api文件：{full_path}')
    print(f'api文件内容：{json_data}')

    if isinstance(json_data, dict):
        for key, value in json_data.items():
            if isinstance(value, str):
                json_data[key] = value.replace('\\', '/')
            elif isinstance(value, list):
                json_data[key] = [v.replace('\\', '/') if isinstance(v, str) else v for v in value]

    # 打开文件并写入JSON数据
    with open(full_path, 'w', encoding='utf-8') as file:
        json.dump(json_data, file, ensure_ascii=False, indent=4)


# 在插件目录下删除json文件，以便插件调用
def WF_delphi_json(path, jsonfilename):
    # 完整的文件路径
    full_path = os.path.join(get_base_path(path), jsonfilename)

    # 检查文件是否存在并删除
    if os.path.exists(full_path):
        os.remove(full_path)


# 检查依赖并执行脚本-用于测试
def test_run_script(script, script_dependencies, completed_scripts):
    """
    检查依赖并执行脚本
    script：总脚本
    script_dependencies：上级依赖
    completed_scripts：已经成功执行的脚本
    """
    # 检查 JSON 字段
    if not script['json']:
        return False, f"{script['name']} 插件还未配置，请先配置后再测试。ID：{script['id']}"

    # 检查 JSON 格式
    if not is_json_valid(script['json']):
        return False, f"{script['name']} 插件JSON配置格式错误，无法继续。ID：{script['id']}"

    for dependency in script_dependencies:
        if dependency not in completed_scripts:
            return False, f"{script['name']} 正在等待执行上级脚本 {dependency}"

    script_path = os.path.dirname(script['name'])
    script_name = os.path.basename(script_path)
    script_file = os.path.basename(script['name'])
    script_json = script['json']

    print(f'script_path:{script_path}')
    print(f'script_name:{script_name}')
    print(f'script_file:{script_file}')

    script_full_path = get_base_path(script['name'])  # 获取脚本的绝对路径
    print(script_full_path)
    script_path = os.path.dirname(script_full_path)
    print(script_path)
    python_executable = sys.executable  # 获取当前Python解释器的路径
    print(f'当前Python解释器的路径:{python_executable}')

    # 设置环境变量
    env = os.environ.copy()
    env['PYTHONPATH'] = script_path + os.pathsep + env.get('PYTHONPATH', '')

    try:
        #WF_save_json(script_path, 'api.json', script_json)
        print(f'即将保存{script_name}的{script_json}数据')
        save_plugjson(script_name, script_json)
        # 组装命令
        command = [python_executable, script_file]
        sfun = script.get('function')
        itime=120
        if sfun:
            print(f'工作流函数命令：{sfun}')
            command.append(script['function'])
            itime = 10

        def get_system_encoding():
            # 尝试获取系统默认的区域设置编码
            encoding = locale.getpreferredencoding()
            if not encoding:
                # 如果无法获取，则使用一个兜底的编码
                encoding = 'utf-8'
            return encoding

        encoding = get_system_encoding()

        print(f'正在执行命令：{command}')
        print(f'请稍候……')
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=script_path,#cwd=os.path.dirname(script['name']),#cwd=os.path.dirname(os.path.dirname(script_path)),
            env=env,  # 使用更新后的环境变量
            encoding=encoding,  # 确保正确的编码方式
        )
        stdout, stderr = process.communicate(timeout=itime)
        if process.returncode != 0 or "Success" not in stdout:
            error_detail = stderr.strip() or "可能是格式不合法，请参考开发文档"
            return False, f"{script['name']} 脚本测试失败，{error_detail}"
        return True, stdout.strip()
    except subprocess.TimeoutExpired:
        process.kill()
        return False, f"脚本执行超时：{script['name']}"
    except Exception as e:
        return False, f"执行过程中出现异常：{str(e)}"
    # finally:
    #     WF_delphi_json(script_path, jsonfilename)  # 删除临时文件

# 数据库状态码
def status_conn(script_id, status):
    """
    更新数据库中特定脚本的连接状态
    script_id: 脚本的ID
    status: 脚本的状态（1: 成功, -1: 失败, 0: 跳过）
    """
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    cursor.execute('''
        UPDATE sub_WorkFlow SET conn = ? WHERE ID = ?
    ''', (status, script_id))
    connection.commit()
    connection.close()

# 将conn字段重置为0
def clear_db_conn(WorkFlowID,allrecord=True):
    """
    重置指定工作流中所有脚本的连接状态
    WorkFlowID: 要重置的工作流ID
    """
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    if allrecord:
        cursor.execute('''
            UPDATE sub_WorkFlow SET conn = 0 WHERE WorkFlowID = ?
        ''', (WorkFlowID,))
    else:
        cursor.execute('''
            UPDATE sub_WorkFlow SET conn = 0 WHERE ID = ?
        ''', (WorkFlowID,))

    connection.commit()
    connection.close()
    print(f"All connection statuses for Workflow ID {WorkFlowID} have been reset to 0.")

# 主工作流运行_用于测试
def test_conn_workflow(WorkFlowID, Bfun=True,progress_callback=None):
    clear_db_conn(WorkFlowID)
    config = load_config(WorkFlowID,Bfun)
    completed_scripts = set()
    executed_scripts = set()  # 用于记录尝试执行的脚本ID
    total_scripts = len(config['scripts'])
    current_script_index = 0  # 初始化当前脚本索引

    try:
        for script in config['scripts']:
            dependencies_met = all(dep in completed_scripts for dep in script['dependencies'])
            if not dependencies_met:
                print(f"{script['name']} 正在等待执行上级脚本")
                continue

            current_script_index += 1  # 更新脚本索引
            if progress_callback:
                progress_callback(current_script_index, total_scripts)  # 调用回调函数更新前端进度

            executed_scripts.add(script['id'])  # 记录尝试执行的脚本
            success, message = test_run_script(script, script['dependencies'], completed_scripts)

            if success:
                completed_scripts.add(script['id'])  # 使用脚本的ID标识完成

                print(f"Output from {script['name']}: {message.strip()}")
                status_conn(script['id'], 1)  # 更新数据库状态为成功

                print(f'成功执行：{completed_scripts}')
            else:
                print(message)
                status_conn(script['id'], -1)  # 更新数据库状态为失败
                return {'success': False, 'message': message}

        # 标记未执行的脚本
        skipped_scripts = {script['id'] for script in config['scripts']} - executed_scripts
        for script_id in skipped_scripts:
            status_conn(script_id, 0)  # 更新数据库状态为跳过

        if len(completed_scripts) < len(config['scripts']):
            print(f'没有成功执行：{completed_scripts}')
            return {'success': False, 'message': '部分脚本执行失败'}

    except Exception as e:
        return {'success': False, 'message': str(e)}

    print('所有脚本成功执行')
    return {'success': True, 'message': '所有脚本成功执行'}

# 工作流子运行
def run_script(script,script_dependencies, completed_scripts,Bfun):
    try:
        # 检查 JSON 字段
        if not script['json']:
            return False, f"{script['name']} 插件还未配置，请先配置后再测试。ID：{script['id']}"

        # 检查 JSON 格式
        if not is_json_valid(script['json']):
            return False, f"{script['name']} 插件JSON配置格式错误，无法继续。ID：{script['id']}"

        for dependency in script_dependencies:
            if dependency not in completed_scripts:
                return False, f"{script['name']} 正在等待执行上级脚本 {dependency}"

        script_path = os.path.dirname(script['name']) # 去掉文件名
        script_name = os.path.basename(script_path)  # 获得插件名称
        script_json = script['json']

        print(f'plugin_path:{script_path}')
        print(f'plugin_name:{script_name}')

        print(f'即将保存{script_name}的{script_json}数据')
        save_plugjson(script_name, script_json) # 保存到插件json


        module = load_plugin_module(script['name'], script_name)
        success, message = module.Runconn(script_name, Bfun)

        return success,message
    except Exception as e:
        return False, f"脚本执行过程中出现异常：{str(e)}"

# 工作流主执行
def conn_workflow(WorkFlowID, Bfun=True,progress_callback=None):
    clear_db_conn(WorkFlowID) # 将工作流插件状态重置为0
    config = load_config(WorkFlowID,Bfun) # 加载所有的工作流插件列表
    completed_scripts = set()
    executed_scripts = set()  # 用于记录尝试执行的脚本ID
    total_scripts = len(config['scripts'])
    current_script_index = 0  # 初始化当前脚本索引

    try:
        for script in config['scripts']:
            dependencies_met = all(dep in completed_scripts for dep in script['dependencies'])
            if not dependencies_met:
                print(f"{script['name']} 正在等待执行上级脚本")
                continue

            current_script_index += 1  # 更新脚本索引
            if progress_callback:
                progress_callback(current_script_index, total_scripts)  # 调用回调函数更新前端进度

            executed_scripts.add(script['id'])  # 记录尝试执行的脚本

            # plugin_path = os.path.dirname(script['name']) # 去掉文件名
            # plugin_name = os.path.basename(plugin_path)  # 获得插件名称

            success, message = run_script(script, script['dependencies'], completed_scripts,Bfun)

            # module = load_plugin_module(script['name'],plugin_name)
            # success, message = module.Runconn_test(plugin_name,Bfun)

            if success:
                completed_scripts.add(script['id'])  # 使用脚本的ID标识完成

                print(f"Output from {script['name']}: {message.strip()}")
                status_conn(script['id'], 1)  # 更新数据库状态为成功

                print(f'成功执行：{completed_scripts}')
            else:
                print(message)
                status_conn(script['id'], -1)  # 更新数据库状态为失败
                return {'success': False, 'message': message}

        # 标记未执行的脚本
        skipped_scripts = {script['id'] for script in config['scripts']} - executed_scripts
        for script_id in skipped_scripts:
            status_conn(script_id, 0)  # 更新数据库状态为跳过

        if len(completed_scripts) < len(config['scripts']):
            print(f'没有成功执行：{completed_scripts}')
            return {'success': False, 'message': '部分脚本执行失败'}

            #return jsonify(result)

    except Exception as e:
        return {'success': False, 'message': str(e)}

    print('所有脚本成功执行')
    return {'success': True, 'message': '所有脚本成功执行'}


# 删除工作流
def delete_workflow(workflow_id):
    # 确保数据库路径和工作流ID不为空
    if not db_path or not workflow_id:
        raise ValueError("Database path and workflow ID must be provided.")

    # 连接到数据库
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 在sub_WorkFlow表中删除对应的记录
        cursor.execute("DELETE FROM sub_WorkFlow WHERE WorkFlowID = ?", (workflow_id,))
        # 在WorkFlow表中删除对应的记录
        cursor.execute("DELETE FROM WorkFlow WHERE ID = ?", (workflow_id,))
        # 提交事务
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return False
    finally:
        # 关闭游标和连接
        cursor.close()
        conn.close()

#实时更新表格状态
def update_progress(socketio, workflow_id, current, total):
    global WF_list
    # 使用列表推导式找到第一个匹配的ID的索引
    index = next(i for i, item in enumerate(WF_list) if item['ID'] == workflow_id)
    progress_message = f"正在执行工作流…【{current}/{total}】"
    WF_list[index]['WorkFlowstatus'] = progress_message
    socketio.emit('status', {'message': progress_message, 'workflow_id': workflow_id})

@workflow_blueprint.route('/workflow', methods=['POST'])
def handle_workflow_Execution():
    if request.is_json:  # 确保请求包含 JSON 数据
        global WF_list
        data = request.get_json()
        action = data.get('action')
        WFName = data.get('WFName')
        WFDes = data.get('WFDes')
        #workflow_id = data.get('id')
        id = data.get('id')
        dir = data.get('dir')
        print(f'当前于/workflow路由action状态码：{action}')

        match action:
            case 'clear_WF_list':  # 清空WF_list字典
                print(f'即将清空字典：{WF_list}')
                WF_list.clear()
                print('清空WF_list字典')
                return jsonify({'status': 'success', 'message': '已清除'}), 200

            case 'CreWF_sub_list': # 加载工作流子页-已选插件
                return render_template('CreWF_sub_list.html',workflow_id=id)

            case 'CreWF_sub_list_read':# 加载工作流子页-已选插件-jinja2页面
                sub_workflow_data = query_db('sub_WorkFlow', f'WorkFlowID = {id}')
                sorted_sub_workflow_data = sorted(sub_workflow_data, key=lambda x: x['Sort'])
                return jsonify(sorted_sub_workflow_data)

            case 'load_plugins_page': # 加载工作流子页-插件选择
                # 临时传参
                WorkFlowName = data.get('WorkFlowName')
                WorkFlowID = data.get('WorkFlowID')
                print(WorkFlowName)
                print(WorkFlowID)
                return render_template('WF_pluglist_select.html',WorkFlowName=WorkFlowName, WorkFlowID=WorkFlowID)

            case 'load_plugins': # 在工作流中选择插件
                try:
                    plugins_list = query_db('MyPlugins')

                    # 遍历插件列表，检查 api.py 文件是否存在，并添加 api 字段
                    for plugin in plugins_list:
                        plugin_dir = plugin.get('PlugDir')
                        # 确保 plugin_dir 不为空
                        if plugin_dir:
                            plugin['api'] = does_api_file_exist(plugin_dir)
                        else:
                            plugin['api'] = False  # 这里将 api 设置为 False

                    print("Plugins List:", plugins_list)

                    return jsonify({
                        "code": 0,  # 成功的状态码为0
                        "msg": "success",
                        "data": plugins_list
                    })

                except sqlite3.Error as e:
                    return jsonify({"error": str(e)}), 500

            case 'Creation_workflow': # 创建工作流
                return Creation_workflow(WFName,WFDes)

            case 'WF_list': # 工作流总表
                # 从数据库查询最新的工作流列表
                fresh_wf_list = query_db('WorkFlow')
                for workflow in fresh_wf_list:
                    workflow['WorkFlowstatus'] = '待命中'
                    id = workflow['ID']
                    taskCount = len(query_db('sub_WorkFlow',f'WorkFlowID = {id}'))
                    workflow['taskCount'] = taskCount

                # 如果WF_list不为空，更新WorkFlowstatus字段为现有的值
                if WF_list:
                    for workflow_db in fresh_wf_list:
                        for workflow_list in WF_list:
                            if workflow_db['ID'] == workflow_list['ID']:
                                workflow_db['WorkFlowstatus'] = workflow_list['WorkFlowstatus']


                WF_list = fresh_wf_list

                print(WF_list)
                return jsonify({
                        "code": 0,  # 成功的状态码为0
                        "msg": "success",
                        "data": WF_list
                    })

            case 'load_workflow_id':# 在创建工作流主页中获取主表数据
                workflow_data = query_db('WorkFlow',f'ID = {id}')
                print(f'工作流主数据：{workflow_data}')
                sub_workflow_data = query_db('sub_WorkFlow',f'WorkFlowID = {id}')
                print(f'工作流子集数据：{sub_workflow_data}')
                response_data = {
                    'workflowData': workflow_data,
                    'count': len(sub_workflow_data)  # 添加数据数量
                }

                return jsonify(response_data)

            case 'load_sub_workflow': # 加载工作流子表
                sub_workflow_list = query_db('sub_WorkFlow',f'WorkFlowID = {id}')
                #sub_workflow = load_sub_workflow(workflow_id)
                print(sub_workflow_list)
                # 检查 sub_workflow_list 是否为空
                if not sub_workflow_list:
                    # 如果为空，返回错误信息和状态码 404
                    return jsonify({
                        "code": 404,
                        "msg": "No data found for the given ID.",
                        "data": []
                    }), 404
                else:
                    # 如果不为空，返回成功信息和数据
                    return jsonify({
                        "code": 0,  # 成功的状态码为0
                        "msg": "success",
                        "data": sub_workflow_list
                    })

            case 'add_plugtoWF':#添加插件到工作流
                success, message = add_plugin_to_workflow(
                    data['WorkFlowName'], data['WorkFlowID'], data['PlugName'], data['PlugDir'],
                    data['PlugDes'], data['PlugID']
                )
                if success:
                    return jsonify({'status': 'success', 'message': message})
                else:
                    return jsonify({'status': 'error', 'message': message}), 500

            case 'del_sub_WF':#在工作流中删除插件
                success, message = delete_data_from_table('sub_WorkFlow',f'ID={id}')
                if success:
                    return jsonify({'status': 'success', 'message': message})
                else:
                    return jsonify({'status': 'error', 'message': message}), 500

            case 'up_sub_WF' | 'down_sub_WF':#修改排序
                clear_db_conn(id, False)
                return move_sub_workflow(id, action)

            case 'cfg_plugin_WF':# 获取插件HTML首页
                return check_plugin_existence(data['PlugDir'])

            case 'CreWF_plugjson':# 渲染JSON加载页
                return render_template('CreWF_plugjson.html', dir=dir)

            case 'load_plugjson':# 加载JSON页
                return load_plugjson(dir)

            case 'save_plugjson':# 保存JSON页
                return save_plugjson(dir, data.get('jsonContent'))

            case 'save_json':# 保存插件目录下的 api.json 文件到数据库
                try:
                    api_path = os.path.join('plugins', dir, 'api.json')
                    api_path = get_base_path(api_path)
                    with open(api_path, 'r',encoding='utf-8') as file:
                        json_content = json.load(file)
                    # 将 JSON 转换为字符串以存储
                    json_content_str = json.dumps(json_content)
                    print(json_content_str)
                    # 尝试更新数据库
                    update_status, message = update_workflow_json(id, json_content_str)
                    if update_status:
                        return jsonify({'status': 'success', 'message': '配置已保存到工作流'})
                    else:
                        return jsonify({'status': 'error', 'message': message})

                except FileNotFoundError:
                    return jsonify({'status': 'error', 'message': '找不到指定的 api.json 文件'})
                except Exception as e:
                    return jsonify({'status': 'error', 'message': str(e)})

            case 'code_sub_WF':# 渲染JSON加载页-数据库版
                workflow_id = data.get('id')
                return render_template('CreWF_plugjson_data.html', workflow_id=workflow_id)

            case 'code_sub_WF_loaddatajson': # 加载插件JSON-数据库
                return load_json_data(id)

            case 'code_sub_WF_savedatajson': # 保存插件JSON-数据库
                clear_db_conn(id,False)
                json_data = data.get('jsonData')
                return save_json_data(id, json_data)

            case 'test_conn_workflow':#测试工作流
                WorkFlowID = data.get('WorkFlowID')
                result = conn_workflow(WorkFlowID)
                print(result)
                return jsonify(result)

            case 'del_WF':#删除工作流
                WorkFlowID = data.get('WorkFlowID')
                success = delete_workflow(WorkFlowID)
                if success:
                    return jsonify({'success': True, 'message': '工作流删除成功'})
                else:
                    return jsonify({'success': False, 'message': '删除工作流失败'})

            case _:
                return jsonify({"error": "Invalid action or request method"}), 400


    else:
        return jsonify({'error': 'Invalid Content-Type'}), 400

def start_workflow(socketio):
    global WF_list
    @socketio.on('start_workflow')
    def handle_start_workflow(data):
        workflow_id = data.get('id')

        # 使用列表推导式找到第一个匹配的ID的索引
        index = next(i for i, item in enumerate(WF_list) if item['ID'] == workflow_id)

        emit('status', {'message': '正在测试工作流', 'workflow_id': workflow_id})
        WF_list[index]['WorkFlowstatus'] = '正在测试工作流'
        print(f'正在测试工作流:{WF_list}')
        test_result = conn_workflow(workflow_id, True)  # 第一次测试工作流

        if test_result['success']:
            WF_list[index]['WorkFlowstatus'] = '正在执行工作流'
            emit('status', {'message': '正在执行工作流', 'workflow_id': workflow_id})
            # 执行工作流，捕获进度
            #result = conn_workflow(workflow_id, False)  # 实际执行工作流
            result = conn_workflow(workflow_id, False,
                                        lambda current, total: update_progress(socketio, workflow_id, current,
                                                                               total))  # 添加回调函数
            #result = {'success': True, 'message': '所有脚本成功执行'}
            if result['success']:
                print('任务已经完成')
                WF_list[index]['WorkFlowstatus'] = '任务已经完成'
                emit('status', {'message': '任务已经完成', 'workflow_id': workflow_id})
            else:
                print('执行工作流失败')
                WF_list[index]['WorkFlowstatus'] = '执行工作流失败'
                emit('status', {'message': '执行工作流失败', 'details': result['message'], 'workflow_id': workflow_id})
        else:
            print('测试工作流失败')
            WF_list[index]['WorkFlowstatus'] = '测试工作流失败'
            emit('status', {'message': '测试工作流失败', 'details': test_result['message'], 'workflow_id': workflow_id})

