import sys,os,time
from plugins.vidsimdtion.main import start_vidsimdtion

def get_base_path(subdir=None):
    if getattr(sys, 'frozen', False):
        # 如果应用程序被打包成了单一文件
        base_path = sys._MEIPASS
        base_path = os.path.join(base_path, 'plugins','vidsimdtion')#此处第3个值要修改
    else:
        # 正常执行时使用文件的当前路径
        base_path = os.path.dirname(os.path.abspath(__file__))
    # 如果指定了子目录，将其追加到基路径
    if subdir:
        base_path = os.path.join(base_path, subdir)

    return base_path

# 事件测试
def test_connection(pluginname):
    result = f"{pluginname} （来自API:{pluginname}消息）脚本测试..."
    return result

# 这是测试函数
def print_messages():
    for i in range(5):  # 假设我们要打印5条信息
        print(f"信息{i}: 这是第 {i} 条信息")
        time.sleep(1)  # 暂停1秒

def Runconn(plugin_name,Bfun=True):
    try:
        if Bfun:
            print(f'（来自API:{plugin_name}消息）Executing test_connection().')
            result = test_connection(plugin_name)
            print(result)
            return True, f'{plugin_name}测试脚本执行成功'
        else:
            #这里运行插件的代码（输入你的主函数即可）
            print(f'（来自API:{plugin_name}消息）Executing start_vidsimdtion(True).')
            start_vidsimdtion(True)
            #print_messages()
            return True, f'{plugin_name}脚本执行完成'

    except Exception as e:
        return False, f"执行过程中出现异常：{str(e)}"

