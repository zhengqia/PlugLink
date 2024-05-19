import webbrowser,os,json,time,importlib,subprocess,sys,threading,shutil,secrets,socketio
from flask_socketio import SocketIO, emit
from flask import Blueprint,Flask, request, jsonify,render_template,send_from_directory,redirect, url_for
from werkzeug.utils import secure_filename
from .Web_Actions import *

"""
默认插件样本
此文件名必须为main.py
在插件目录下必须要有__init__.py文件，该文件可以为空
升级文件请自行安排自己的升级服务器
get_base_path函数：获取当前插件目录路径的，需要修改参数，可以移动到其它文件
sys.path.insert：添加您的libs目录到sys，不要修改，注意要将依赖安装在此目录
"""
#注册插件蓝图-自定义名字，尽量个性化，避免与其它插件冲突
plugin_blueprint = Blueprint('videosyn', __name__)


libs_path = os.path.join(get_base_path('libs'))
if libs_path not in sys.path:
    sys.path.insert(0, libs_path)


"""
以下代码仅为方便您前端网页调试的示例，在正式安装插件的环境下必须删除

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/<path:filename>')
def serve_views(filename):
    return send_from_directory('static/', filename)

@app.route('/', methods=['GET'])
def index_page():
    return send_from_directory(app.static_folder, 'index.html')
"""

@plugin_blueprint.route('/', methods=['POST','GET'])  #蓝图环境不需要加路由器名称
#@app.route('/videosyn/', methods=['POST','GET']) #测试时可使用这个
def handle_videosyn():
    data = request.get_json()
    action = data.get('action')
    path = data.get('path')
    url = data.get('url')
    id = data.get('id')
    # 创建及删除目录专用
    totalDirName = str(data.get('totalDirName'))
    subdirName = str(data.get('subdirName'))
    lastOne = data.get('lastOne')
    print(f'当前于【videosyn插件】/路由action状态码：{action}')
    match action:
        case "MateDir":#扫描总目录
            result = Dir_Scan(path)
            # 将结果以JSON格式返回给前端
            return jsonify(result)
        case "createDir":#创建目录
            result = create_directory(totalDirName, subdirName)
            return result
        case "deleteDir":#删除目录
            result = delete_directory(totalDirName, subdirName, lastOne)
            return result

        case "scanDirectories":#扫描所有目录
            total_dir_name = data.get('totalDirName')
            directories = scan_directories(total_dir_name)
            return {'directories': directories}

        case "saveVideosInfo":#保存视频上传目录信息
            uploadedVideosInfo = data.get('uploadedVideosInfo')
            total_dir_name = data.get('totalDirName')
            custom_order = data.get('customOrder')
            directories_order = data.get('directoriesOrder')
            head_dir = data.get('headDir')
            tail_dir = data.get('tailDir')
            enable_transitions = data.get('enableTransitions')
            transition_duration = data.get('transitionDuration')
            output_extension = data.get('outputExtension')
            output_dir = data.get('outputDir')
            description = add_videos_info(uploadedVideosInfo,
                               custom_order,
                               directories_order,
                               total_dir_name,
                               head_dir,
                               tail_dir,
                               enable_transitions,
                               transition_duration,
                               output_extension,
                               output_dir)
            return description
        case 'exevid':#调用主执行函数
            return running_merge_videos()
        case 'stoptask':#终止线程
            stop_task()
            return jsonify({'message': '线程中止'}), 200
        case 'progress':#执行进度
            return jsonify(global_progress)
        case 'opendir':#打开目录
            directory_path = data.get('output_dir')
            #print(directory_path)
            if isinstance(directory_path, list):
                directory_path = directory_path[0] if directory_path else None
                # 根据操作系统选择不同的命令
                if sys.platform == 'win32':  # Windows
                    subprocess.Popen(['explorer', directory_path])
                elif sys.platform == 'darwin':  # macOS
                    subprocess.Popen(['open', directory_path])
                else:  # Linux
                    subprocess.Popen(['xdg-open', directory_path])

                return jsonify({'message': 'Directory opened successfully.'}), 200
            else:
                return jsonify({'message': 'Directory not found.'}), 404

        case _:
            return jsonify({"error": "未知的操作请求"})

#@app.route('/videosyn/upload', methods=['POST'])
@plugin_blueprint.route('/upload', methods=['POST'])
def upload_file():
    totalDirName = request.form.get('totalDirName')
    tabTitle = request.form.get('tabTitle')
    uploaded_files = request.files.getlist("file")  # 获取多文件上传的文件列表

    # 构建保存文件的路径
    #save_path = os.path.join('upload', totalDirName, tabTitle)
    base_dir = get_base_path('upload') # 获取基础路径
    save_path = os.path.join(base_dir, totalDirName, tabTitle)  # 构建保存文件的路径

    if not os.path.exists(save_path):
        os.makedirs(save_path)

    temp_filenames = []  # 存储临时文件名和原始文件扩展名

    for file in uploaded_files:
        if file:
            # 生成一个临时文件名，这里使用了 secrets.token_hex(8) 生成16字符的随机字符串
            temp_filename = secrets.token_hex(8) + os.path.splitext(file.filename)[1]
            temp_filenames.append((temp_filename, file.filename))  # 保存临时文件名和原始文件名
            file.save(os.path.join(save_path, temp_filename))

    return jsonify({'success': True, 'message': '文件暂时上传成功，等待重命名'})


"""
插件独立测试专用，应用于PlugLink插件环境要注释

def open_browser():
    webbrowser.open('http://localhost:8966/') 


if __name__ == '__main__':
    #在此处调用函数，其它部分可以删除
    open_browser()
    #app.run(host='0.0.0.0', debug=True, port=8966, use_reloader=False)
    socketio.run(app, host='0.0.0.0', port=8966, debug=True, use_reloader=False, allow_unsafe_werkzeug=True)
"""

