import sys,os,time
from Web_Actions import running_merge_videos

"""
插件环境下要采用绝对路径：
from plugins.videosyn.Web_Actions import running_merge_videos

plugins：为PlugLink框架默认插件集中路径；
videosyn（示例）：这是当前插件的文件夹名；
Web_Actions（示例）：这是你调用的文件。
"""

"""
以下部分不要修改，否则可能会导致无法在大框架中实现api
在此代码块下写入您的函数即可，尽量仅用函数，最好不要写入太长的代码，养成良好的代码习惯。
print_messages函数是测试函数，不需要用到注释掉就好。
"""

# 事件测试
def test_connection(pluginname):
    result = f"{pluginname} （来自API:{pluginname}消息）Testing connection..."
    return result

# 这是测试函数
def print_messages():
    for i in range(5):  # 假设我们要打印5条信息
        print(f"信息{i}: 这是第 {i} 条信息")
        time.sleep(1)  # 暂停1秒

"""
Runconn是工作流插件API运行函数，只须把 #这里输入您的函数 此处替换成您的主运行函数即可
不要在此函数上直接使用多线程，会造成工作流无法按顺序进行
"""
def Runconn(plugin_name,Bfun=True):
    try:
        if Bfun:
            print(f'（来自API:{plugin_name}消息）Executing test_connection().')
            result = test_connection(plugin_name)
            print(result)
            return True, f'{plugin_name}测试脚本执行成功'
        else:
            #这里运行插件的代码（输入你的主函数即可）
            print(f'（来自API:{plugin_name}消息）Executing 【您的函数名称】.')
            #这里输入您的函数
            #print_messages()
            return True, f'{plugin_name}脚本执行完成'

    except Exception as e:
        return False, f"执行过程中出现异常：{str(e)}"
