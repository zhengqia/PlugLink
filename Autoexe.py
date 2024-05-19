from tinydb import TinyDB, Query
from subprocess import Popen, PIPE, STDOUT,STARTUPINFO, STARTF_USESHOWWINDOW
import threading,sys,os,io,atexit,chardet,subprocess,signal,importlib
import tkinter as tk
from tkinter import ttk
from flask import Blueprint,current_app
from Ini_sys import *
from Ini_DB import *
from Plugins_Actions import setup_plugin_blueprint

# os.environ['PYTHONUTF8'] = '1'
# os.environ['PYTHONIOENCODING'] = 'utf-8'
# sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
# sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

"""自动加载页，执行下载、运行及启动处理等"""

# 批量注册插件蓝图
def register_plugin_blueprints(app, plugin_folder='plugins'):
    # 遍历插件目录
    plugin_base_path = get_base_path(plugin_folder)

    for plugin_name in os.listdir(plugin_base_path):
        if plugin_name == '__pycache__' or not is_plugin_registered(plugin_name):
            continue

        plugin_path = os.path.join(plugin_base_path, plugin_name)

        if os.path.isdir(plugin_path):
            plugin_module = None
            try:
                plugin_module = importlib.import_module(f"{plugin_folder}.{plugin_name}.main")
            except ModuleNotFoundError as e:
                print(f"无法完全导入插件 {plugin_name}，因为缺少模块：{e}")
                continue  # 如果关键导入失败，跳过当前插件
            except Exception as e:
                print(f"加载插件 {plugin_name} 时出错：{e}")
                continue  # 类似处理其他错误

            if plugin_module:
                try:
                    for item in dir(plugin_module):
                        attr = getattr(plugin_module, item)
                        if isinstance(attr, Blueprint):
                            app.register_blueprint(attr, url_prefix=f'/{plugin_name}')
                            print(f"成功为插件 {plugin_name} 注册蓝图")
                except Exception as e:
                    print(f"注册插件 {plugin_name} 的蓝图失败：{e}")

# def register_plugin_blueprints(app, plugin_folder='plugins'):
#     # 遍历插件目录
#     plugin_base_path = get_base_path(plugin_folder)
#
#     for plugin_name in os.listdir(plugin_base_path):
#         if plugin_name == '__pycache__' or not is_plugin_registered(plugin_name):
#             continue
#
#         plugin_path = os.path.join(plugin_base_path, plugin_name)
#
#         if os.path.isdir(plugin_path):
#             # 尝试从每个插件目录中导入 main.py 模块
#             try:
#                 plugin_module = importlib.import_module(f"{plugin_folder}.{plugin_name}.main")
#                 #plugin_module.run()
#
#                 # 搜索并注册蓝图对象
#                 # for item in dir(plugin_module):
#                 #     if isinstance(getattr(plugin_module, item), Blueprint):
#                 #         blueprint = getattr(plugin_module, item)
#                 #         app.register_blueprint(blueprint, url_prefix=f'/{plugin_name}')
#                 #         print(f"成功为插件注册蓝图：{plugin_name}")
#                 for item in dir(plugin_module):
#                     attr = getattr(plugin_module, item)
#                     if isinstance(attr, Blueprint):
#                         app.register_blueprint(attr, url_prefix=f'/{plugin_name}')
#                         print(f"成功蓝图注册到插件：{plugin_name}")
#
#             except ModuleNotFoundError as e:
#                 print(f"插件导入错误 {plugin_name}: {e}")
#                 #package_name = str(e).split("'")[1]
#                 #install_and_import(package_name)
#             except Exception as e:
#                 print(f"导入插件 {plugin_name} 时发生错误：{e}")


# 全局变量定义
lock_file_path = get_base_path('app.lock')
process_holder = []

# def read_output(pipe, text_widget):
#     try:
#         while True:
#             line = pipe.readline()
#             if not line:
#                 break
#             text_widget.insert(tk.END, line)
#             text_widget.see(tk.END)
#             text_widget.update_idletasks()
#     except Exception as e:
#         text_widget.insert(tk.END, f"发生错误: {str(e)}\n")
#     finally:
#         pipe.close()


def read_output(pipe, text_widget):
    try:
        for line in pipe:
            # 尝试使用默认系统编码解码，无法解码的部分将被替换
            text_widget.insert(tk.END, line.decode('utf-8', errors='replace'))
            text_widget.see(tk.END)
            text_widget.update_idletasks()
    except Exception as e:
        text_widget.insert(tk.END, f"发生错误: {str(e)}\n")
    finally:
        pipe.close()


def run_script(text_widget, process_holder):
    script_path = get_base_path()
    python_executable = sys.executable
    env = os.environ.copy()
    env['RUN_FULL_GUI'] = '0'  # 确保子进程不会运行完整的GUI
    cmd = [python_executable, os.path.join(script_path, 'main.py')]
    #process = Popen(cmd, stdout=PIPE, stderr=STDOUT, text=True, encoding='utf-8', bufsize=1, env=env)
    #process = Popen(cmd, stdout=PIPE, stderr=STDOUT, text=True, encoding='cp437', bufsize=1, env=env)
    #process = Popen(cmd, stdout=PIPE, stderr=STDOUT, text=False, bufsize=1, env=env)  # 注意 text=False，因为我们将处理字节流
    process = Popen(cmd, stdout=PIPE, stderr=STDOUT, text=False, bufsize=-1, env=env)

    process_holder.append(process)
    read_output(process.stdout, text_widget)
    process.wait()

def start_auto(text_widget, process_holder):
    thread = threading.Thread(target=run_script, args=(text_widget, process_holder))
    thread.setDaemon(True)
    thread.start()

def on_exit():
    global lock_file_path
    try:
        if os.path.exists(lock_file_path):
            os.remove(lock_file_path)
    except Exception as e:
        print(f"无法删除锁文件 {lock_file_path}: {e}")


def kill_process_and_children(pid):
    """使用taskkill终止指定的进程及其所有子进程"""
    try:
        #subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)], check=True)
        #subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)], check=True, encoding='gbk')
        subprocess.run(
            ['taskkill', '/F', '/T', '/PID', str(pid)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    except subprocess.CalledProcessError as e:
        print(f"无法终止进程 {pid}: {e}")

def close_app(root, process_holder):
    """尝试终止所有后台进程，并强制关闭应用程序"""
    try:
        if process_holder:
            for proc in process_holder:
                kill_process_and_children(proc.pid)  # 终止进程及其子进程
    finally:
        on_exit()
        root.destroy()
        os._exit(0)  # 强制退出程序

#窗体样式设置
def center_window(root, width=1000, height=700):
    """将窗口居中放置到屏幕上"""
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # 计算 x 和 y 坐标以使窗口居中
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    root.geometry(f'{width}x{height}+{x}+{y}')

#“关闭程序”的按钮
def create_styled_button(parent, text, command):
    """创建一个有样式的按钮"""
    return tk.Button(
        parent,
        text=text,
        command=command,
        font=('Microsoft YaHei', 12),
        bg='#4E5D6C',  # 按钮背景颜色
        fg='white',  # 字体颜色
        padx=10,  # 按钮内左右填充
        pady=5,  # 按钮内上下填充
        bd=3,  # 边框宽度
        relief=tk.RAISED  # 边框样式
    )

# def text_widget_Scrollbar(root):
#     # 创建一个框架，用于放置文本框和滚动条
#     text_frame = tk.Frame(root)
#     text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
#
#     # 创建文本框并放在框架的左侧，让它填充框架的大部分空间
#     output_text = tk.Text(text_frame, bg='black', fg='white', font=('Microsoft YaHei', 14))
#     output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
#
#     # 创建滚动条并放在框架的右侧，与文本框垂直对齐
#     scrollbar = tk.Scrollbar(text_frame, orient="vertical", command=output_text.yview)
#     scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
#
#     # 配置文本框使用滚动条
#     output_text.config(yscrollcommand=scrollbar.set)
#
#     return output_text

#进度条
def setup_status_bar(root):
    """设置状态栏，包含一条进度条和一段状态文本"""
    status_frame = tk.Frame(root, relief=tk.SUNKEN, bd=2)
    status_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=2)  # 放在顶部，添加一些内边距

    # 状态文本
    status_label = tk.Label(status_frame, text='准备就绪', anchor=tk.W, bg='#e1e4e8', fg='#333', font=('Microsoft YaHei', 12))
    status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

    # 进度条
    progress = ttk.Progressbar(status_frame, orient=tk.HORIZONTAL, length=300, mode='determinate')
    progress.pack(side=tk.RIGHT, padx=2)

    # 修改进度条的样式
    style = ttk.Style(root)
    style.theme_use('clam')  # 使用 clam 主题，这通常比默认的外观好看
    style.configure('Horizontal.TProgressbar', troughcolor='#e1e4e8', bordercolor='#333', background='#4E9F3D', lightcolor='#4E9F3D', darkcolor='#4E9F3D')

    return status_label, progress

def update_status(status_label, text, progress=None, value=None, maximum=None):
    """更新状态栏文本和进度条"""
    status_label.config(text=text)
    if progress is not None:
        if value is not None:
            progress['value'] = value
        if maximum is not None:
            progress['maximum'] = maximum
        progress.update_idletasks()
    status_label.update_idletasks()

# 按钮
def setup_buttons(root, process_holder):
    """设置按钮栏，包括关闭程序和打开网页的按钮"""
    button_frame = tk.Frame(root)
    button_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

    # 使用之前创建的 create_styled_button 函数来创建样式化的按钮
    close_button = create_styled_button(button_frame, '关闭程序', lambda: close_app(root, process_holder))
    close_button.pack(side=tk.RIGHT, padx=8)

    # 使用已有的 open_browser 函数打开网页
    open_web_button = create_styled_button(button_frame, '打开网页', lambda:open_browser('http://localhost:8966/'))
    open_web_button.pack(side=tk.RIGHT, padx=8)

    return button_frame

#主程序窗体
def mainpro(root):
    # 锁定只能打开1次
    if os.path.exists(lock_file_path):
        print("程序已在运行。")
        return

    with open(lock_file_path, 'w') as f:
        f.write('lock')

    atexit.register(on_exit)

    # 设置文本框样式
    output_text = tk.Text(root, bg='black', fg='white', font=('Microsoft YaHei', 12))
    output_text.pack(side=tk.TOP, expand=True, fill='both')

    # 创建滚动条
    scrollbar = tk.Scrollbar(root)
    scrollbar.pack(side=tk.RIGHT, fill='y')  # 滚动条放在界面右侧，并填充垂直方向

    # 将滚动条与文本框关联
    output_text.config(yscrollcommand=scrollbar.set)
    scrollbar.config(command=output_text.yview)

    # 开始执行显示文本信息
    start_auto(output_text, process_holder)

    # 添加窗体图标
    root.iconbitmap(get_base_path('favicon.ico'))

    # 居中窗口并设置一个较大的尺寸
    center_window(root, width=1000, height=700)

    # 设置状态栏和进度条
    #status_label, progress_bar = setup_status_bar(root)
    # 在需要时更新状态信息和进度
    # 例如，update_status(status_label, '正在安装依赖...', progress_bar, 50)

    # 设置按钮栏
    button_frame = setup_buttons(root, process_holder)

    root.protocol("WM_DELETE_WINDOW", lambda: close_app(root, process_holder))

#返回数据json
def readjson_is_AIxlx():
    db = TinyDB('AI.json')
    print(db.all())
    return db.all()


