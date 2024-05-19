<<<<<<< HEAD
from flask import Flask, request, jsonify,render_template,send_from_directory,redirect, url_for,Blueprint,send_file
from flask_socketio import SocketIO, emit
import Web_Actions,Plugins_Actions,WorkFlow_Actions,Ini_DB,Ini_sys,Autoexe
import threading,time
from multiprocessing import Process
from Web_Actions import web_blueprint
from Plugins_Actions import plugins_blueprint,setup_socket_events,install_plugin_dependencies,load_all_plugins
from WorkFlow_Actions import workflow_blueprint,start_workflow
from Ini_DB import Ini_Data
from Ini_sys import os,open_browser,plugins_directory
from Autoexe import register_plugin_blueprints,db_path,ini_plugins_db,mainpro,tk


"""<初始化>"""
plugins_directory()# 创建plugins目录
Ini_Data() # 初始化数据库

"""<路由及实施>"""
app = Flask(__name__)

app.register_blueprint(web_blueprint)
app.register_blueprint(plugins_blueprint)
app.register_blueprint(workflow_blueprint)

socketio = SocketIO(app) # ,async_mode='gevent',async_mode='eventlet'
setup_socket_events(socketio)  # 设置 Socket.IO 事件
start_workflow(socketio)

"""<依赖安装>"""
#install_plugin_dependencies()
load_all_plugins()

"""注册插件的路由"""
# 调用函数来注册所有插件的蓝图
register_plugin_blueprints(app)
print('路由列表：')
print(app.url_map)

"""<调用数据库中的 MyPlugins 表>"""
print(f'数据库位置：{db_path}')
ini_plugins_db(app)


@app.route('/plugins/<path:filename>')
def serve_plugins(filename):
    return send_from_directory('plugins', filename)

@app.route('/<path:filename>')
def serve_views(filename):
    return send_from_directory('static/', filename)

@app.route('/', methods=['GET'])
def index_page():
    return send_from_directory(app.static_folder, 'views/index.html')

# 程序时清空工作流缓存
should_clear_local_storage = True
@app.route('/should_clear_storage')
def should_clear_storage():
    global should_clear_local_storage
    # 返回当前的标志状态，并重置标志
    should_clear = should_clear_local_storage
    should_clear_local_storage = False  # 重置标志，防止后续的页面加载也清除状态
    return jsonify({"clear_storage": should_clear})


def run_tkinter():
    root = tk.Tk()
    root.title("PlugLink 程序运行窗口")
    mainpro(root)
    root.mainloop()
    #app.run(host='0.0.0.0', debug=True, port=5001, use_reloader=False)
    # socketio.run(app, debug=True)

def kill_existing_process_on_port(port):
    import psutil
    # 获取特定端口上运行的进程
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['pid'] != 0:  # 确保不是 PID 为 0 的进程
            try:
                # 在这里添加判断进程是否在特定端口上的逻辑
                proc.kill()
            except psutil.AccessDenied:
                print(f"无法结束进程 {proc.info['pid']}：权限不足")
            except Exception as e:
                print(f"无法结束进程 {proc.info['pid']}：{e}")

if __name__ == '__main__':

    # port = 8966
    # kill_existing_process_on_port(port)

    print(f"Environment 'RUN_FULL_GUI': {os.environ.get('RUN_FULL_GUI')}")
    #print("Current sys.path:", sys.path)

    if os.environ.get('RUN_FULL_GUI', '1') == '1':  # 只有当环境变量设置时才运行GUI
        #threading.Thread(target=run_tkinter).start()

        run_tkinter()

    open_browser('http://localhost:8966/')

    socketio.run(app, host='0.0.0.0', port=8966, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)

    # open_browser('http://localhost:8966/')
    #
    # #socketio.run(app, host='0.0.0.0', port=5001, debug=True, use_reloader=False)
    # socketio.run(app, host='0.0.0.0', port=8966, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)
    # #app.run(host='0.0.0.0', debug=True, port=5001, use_reloader=False)
    # # socketio.run(app, debug=True)



=======
from flask import Flask, request, jsonify,render_template,send_from_directory,redirect, url_for,Blueprint,send_file
from flask_socketio import SocketIO, emit
import Web_Actions,Plugins_Actions,WorkFlow_Actions,Ini_DB,Ini_sys,Autoexe
import threading,time
from multiprocessing import Process
from Web_Actions import web_blueprint
from Plugins_Actions import plugins_blueprint,setup_socket_events,install_plugin_dependencies,load_all_plugins
from WorkFlow_Actions import workflow_blueprint,start_workflow
from Ini_DB import Ini_Data
from Ini_sys import os,open_browser,plugins_directory
from Autoexe import register_plugin_blueprints,db_path,ini_plugins_db,mainpro,tk


"""<初始化>"""
plugins_directory()# 创建plugins目录
Ini_Data() # 初始化数据库

"""<路由及实施>"""
app = Flask(__name__)

app.register_blueprint(web_blueprint)
app.register_blueprint(plugins_blueprint)
app.register_blueprint(workflow_blueprint)

socketio = SocketIO(app) # ,async_mode='gevent',async_mode='eventlet'
setup_socket_events(socketio)  # 设置 Socket.IO 事件
start_workflow(socketio)

"""<依赖安装>"""
#install_plugin_dependencies()
load_all_plugins()

"""注册插件的路由"""
# 调用函数来注册所有插件的蓝图
register_plugin_blueprints(app)
print('路由列表：')
print(app.url_map)

"""<调用数据库中的 MyPlugins 表>"""
print(f'数据库位置：{db_path}')
ini_plugins_db(app)


@app.route('/plugins/<path:filename>')
def serve_plugins(filename):
    return send_from_directory('plugins', filename)

@app.route('/<path:filename>')
def serve_views(filename):
    return send_from_directory('static/', filename)

@app.route('/', methods=['GET'])
def index_page():
    return send_from_directory(app.static_folder, 'views/index.html')

# 程序时清空工作流缓存
should_clear_local_storage = True
@app.route('/should_clear_storage')
def should_clear_storage():
    global should_clear_local_storage
    # 返回当前的标志状态，并重置标志
    should_clear = should_clear_local_storage
    should_clear_local_storage = False  # 重置标志，防止后续的页面加载也清除状态
    return jsonify({"clear_storage": should_clear})


def run_tkinter():
    root = tk.Tk()
    root.title("PlugLink 程序运行窗口")
    mainpro(root)
    root.mainloop()
    #app.run(host='0.0.0.0', debug=True, port=5001, use_reloader=False)
    # socketio.run(app, debug=True)

def kill_existing_process_on_port(port):
    import psutil
    # 获取特定端口上运行的进程
    for proc in psutil.process_iter(['pid', 'name']):
        if proc.info['pid'] != 0:  # 确保不是 PID 为 0 的进程
            try:
                # 在这里添加判断进程是否在特定端口上的逻辑
                proc.kill()
            except psutil.AccessDenied:
                print(f"无法结束进程 {proc.info['pid']}：权限不足")
            except Exception as e:
                print(f"无法结束进程 {proc.info['pid']}：{e}")

if __name__ == '__main__':

    # port = 8966
    # kill_existing_process_on_port(port)

    print(f"Environment 'RUN_FULL_GUI': {os.environ.get('RUN_FULL_GUI')}")
    #print("Current sys.path:", sys.path)

    if os.environ.get('RUN_FULL_GUI', '1') == '1':  # 只有当环境变量设置时才运行GUI
        #threading.Thread(target=run_tkinter).start()

        run_tkinter()

    open_browser('http://localhost:8966/')

    socketio.run(app, host='0.0.0.0', port=8966, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)

    # open_browser('http://localhost:8966/')
    #
    # #socketio.run(app, host='0.0.0.0', port=5001, debug=True, use_reloader=False)
    # socketio.run(app, host='0.0.0.0', port=8966, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)
    # #app.run(host='0.0.0.0', debug=True, port=5001, use_reloader=False)
    # # socketio.run(app, debug=True)



>>>>>>> 33969d2a895ce8a09fca410185bb3cfa811bfe73
