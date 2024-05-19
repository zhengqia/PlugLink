from flask import Blueprint,Flask, request
"""
引用示例：
from .Web_Actions import *
"""

"""
默认插件样本
此文件名必须为main.py
在插件目录下必须要有__init__.py文件，该文件可以为空
升级文件请自行安排自己的升级服务器
get_base_path函数：获取当前插件目录路径的，需要修改参数，可以移动到其它文件
sys.path.insert：添加您的libs目录到sys，不要修改，注意要将依赖安装在此目录
"""
#注册插件蓝图-自定义名字，尽量个性化，避免与其它插件冲突
plugin_blueprint = Blueprint('your_blueprint_name', __name__)

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
#@app.route('/your_route/', methods=['POST','GET']) #测试时可使用这个
def handle_yourfunction():
    pass

#@app.route('/videosyn/upload', methods=['POST'])
@plugin_blueprint.route('/upload', methods=['POST'])
def upload_file():
    pass


#绝对路径，直接引用这个函数就好，可以放置到您其它的.py文件中
def get_base_path(subdir=None):
    if getattr(sys, 'frozen', False):
        # 如果应用程序被打包成了单一文件
        base_path = sys._MEIPASS
        base_path = os.path.join(base_path, 'plugins','your_plugin_name')#此处改成您的插件名
    else:
        # 正常执行时使用文件的当前路径
        base_path = os.path.dirname(os.path.abspath(__file__))
    # 如果指定了子目录，将其追加到基路径
    if subdir:
        base_path = os.path.normpath(os.path.join(base_path, subdir.replace("/", "\\")))

    return base_path


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

