import os,sys,platform,subprocess,webbrowser,ast,json,stdlib_list,re,time
from importlib.metadata import distribution, PackageNotFoundError


"""
本页为所有通用性操作函数
ini_开头的均用于配置或通用，不要from任何_Actions的文件
"""


"""<依赖综合应用函数>"""
# 提取依赖
def scan_dependencies_in_file(file_path):
    """从 Python 文件中扫描导入语句以提取依赖"""
    standard_libs = stdlib_list.stdlib_list("3.10")  # 使用Python 3.10的标准库列表
    dependencies = set()

    with open(file_path, 'r', encoding='utf-8') as file:
        tree = ast.parse(file.read(), filename=file_path)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    dep_name = name.name.split('.')[0]
                    if dep_name not in standard_libs and not dep_name.startswith("plugins"):
                        dependencies.add(dep_name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    dep_name = node.module.split('.')[0]
                    if dep_name not in standard_libs and not dep_name.startswith("plugins"):
                        dependencies.add(dep_name)

    return list(dependencies)

#子依赖也同样检测
# def scan_dependencies_in_file(file_path):
#     """从 Python 文件中扫描导入语句以提取依赖，包括子模块"""
#     standard_libs = stdlib_list.stdlib_list("3.10")  # 使用Python 3.10的标准库列表
#     dependencies = set()
#
#     with open(file_path, 'r', encoding='utf-8') as file:
#         tree = ast.parse(file.read(), filename=file_path)
#
#         for node in ast.walk(tree):
#             if isinstance(node, ast.Import):
#                 for name in node.names:
#                     dep_name = name.name
#                     if dep_name.split('.')[0] not in standard_libs and not dep_name.startswith("plugins"):
#                         dependencies.add(dep_name)
#             elif isinstance(node, ast.ImportFrom):
#                 if node.module:
#                     dep_name = node.module
#                     if dep_name.split('.')[0] not in standard_libs and not dep_name.startswith("plugins"):
#                         dependencies.add(dep_name)
#
#     return list(dependencies)



# 依赖安装路径-虚拟环境
def is_virtual_env():
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
def get_pip_path():
    """确定pip的正确路径。"""
    if hasattr(sys, 'frozen'):
        # 在 PyInstaller 环境下运行，使用 sys.executable
        return [sys.executable, '-m', 'pip']
    elif is_virtual_env():
        # 在虚拟环境中，我们可以假设 pip 位于虚拟环境的 'Scripts' 目录下
        return os.path.join(sys.prefix, 'Scripts', 'pip.exe')
    else:
        # 不在虚拟环境中，直接调用系统的 pip
        return 'pip'

def get_standard_library_list():
    # 这只是一个示例，可能需要根据Python版本进行调整
    if sys.version_info.major == 3 and sys.version_info.minor >= 8:
        from stdlib_list import stdlib_list
        return stdlib_list("3.8")
    else:
        # 对于不同的Python版本，可能需要不同的处理
        return []

standard_libs = get_standard_library_list()

# 扫描子目录-依赖检测
def get_plugin_dependencies(plugin_dir):
    """遍历插件目录，扫描所有 Python 文件来确定依赖"""
    dependencies = set()
    for dirpath, _, filenames in os.walk(plugin_dir):
        for filename in filenames:
            if filename.endswith('.py'):
                file_path = os.path.join(dirpath, filename)
                file_dependencies = scan_dependencies_in_file(file_path)
                # 过滤掉Python标准库和非第三方库的依赖
                filtered_deps = [dep for dep in file_dependencies if dep not in standard_libs]
                dependencies.update(filtered_deps)
    return list(dependencies)

# 获取.py文件列表
def get_plugin_files(plugin_dir):
    """获取插件目录中的所有Python文件名（无扩展名）。"""
    plugin_files = set()
    for root, dirs, files in os.walk(plugin_dir):
        for file in files:
            if file.endswith('.py'):
                plugin_files.add(os.path.splitext(file)[0])
    return plugin_files

def is_package_installed(package_name):
    """检查指定的包是否已安装"""
    try:
        dist = distribution(package_name)
        return True
    except PackageNotFoundError:
        return False

# 下载依赖
def install_dependencies(plugin_dir, dependencies,timeout=300):
    plugin_files = get_plugin_files(plugin_dir)

    pip_path = get_pip_path()
    # 使用 sys.executable 调用 pip
    #pip_command = [sys.executable, '-m', 'pip']

    mirrors = [
        "https://pypi.tuna.tsinghua.edu.cn/simple",
        "http://mirrors.aliyun.com/pypi/simple",
        "http://pypi.douban.com/simple/",
        "https://pypi.mirrors.ustc.edu.cn/simple/",
        "http://pypi.hustunique.com/",
        "http://pypi.sdutlinux.org/",
        "http://mirrors.163.com"
    ]

    all_installed = True  # 布尔变量，跟踪是否所有依赖都成功安装了
    success = []
    failures = []

    for dependency in dependencies:
        print(f"准备安装依赖...{dependency}")
        if dependency in plugin_files:
            continue
        elif is_package_installed(dependency):
            print(f"{dependency} 依赖已经安装.")
            success.append(dependency)
            continue

        installed = False
        for mirror in mirrors:
            try:
                result = subprocess.run(
                    pip_path + ["install", dependency, "-i", mirror, "--trusted-host",
                     mirror.split('//')[1].split('/')[0]],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )
                if result.returncode == 0:
                    success.append(dependency)
                    installed = True
                    print(f"成功安装 {dependency}，使用镜像 {mirror}。")
                    break

            except subprocess.CalledProcessError as e:
                #print(f"使用 {mirror} 安装 {dependency} 时出现异常，异常信息：{e.stderr}")
                print(f"使用 {mirror} 安装 {dependency} 时出现异常，异常信息：{e.stderr.encode('utf-8', 'replace').decode('utf-8')}")

                # 从错误信息中尝试找到建议的包名
                match = re.search(r"use 'pip install ([^']+)'", e.stderr)
                if match:
                    suggested_package = match.group(1)
                    print(f"尝试安装建议的包名 {suggested_package}...")
                    dependency = suggested_package  # 更新为建议的包名
                    continue  # 继续当前的安装尝试

                if "No matching distribution found" in e.stderr:
                    break  # 如果包不存在，则停止尝试其他镜像

        if not installed:
            print(f"所有镜像尝试失败，未能安装 {dependency}...自动跳过")
            failures.append(dependency)
            all_installed = False

    # 检查并尝试安装requirements.txt中的依赖
    requirements_path = os.path.join(plugin_dir, 'requirements.txt')
    if os.path.exists(requirements_path):#not all_installed and
        print("继续从 requirements.txt 安装依赖...")
        for mirror in mirrors:
            try:
                result = subprocess.run(
                    #[pip_path, "install", "-r", requirements_path],
                     [pip_path,"install", "-r", requirements_path, "-i", mirror, "--trusted-host",
                     mirror.split('//')[1].split('/')[0]],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    timeout=timeout
                )
                if result.returncode == 0:
                    print(f"从 {mirror} 成功安装 requirements.txt 中的依赖。")
                    success.extend(dependencies)  # 假设所有的依赖都在 requirements.txt 中并且都安装成功
                    failures = []  # 清空之前的失败记录
                    break
                else:
                    print(result.stderr)

            except subprocess.TimeoutExpired:
                print("安装超时，请检查网络连接或联系插件开发厂商。")
                break
            except subprocess.CalledProcessError as e:
                print(e.stderr)

    if failures:
        print("该插件依赖包尝试用多种方式安装失败，请联系插件开发厂商客服。")
    else:
        print("所有依赖包均安装成功。")

    return success, failures

# 添加了错包修复
# def install_dependencies(plugin_dir, dependencies):
#     plugin_files = get_plugin_files(plugin_dir)
#     pip_path = get_pip_path()
#     mirrors = [
#         "https://pypi.tuna.tsinghua.edu.cn/simple",
#         "http://mirrors.aliyun.com/pypi/simple",
#         "http://pypi.douban.com/simple/",
#         "https://pypi.mirrors.ustc.edu.cn/simple/",
#         "http://pypi.hustunique.com/",
#         "http://pypi.sdutlinux.org/",
#         "http://mirrors.163.com"
#     ]
#
#     success = []
#     failures = []
#
#     for dependency in dependencies:
#         print(f"准备安装依赖...{dependency}")
#         if dependency in plugin_files:
#             #print(f"跳过 {dependency} 。")
#             continue
#         elif is_package_installed(dependency):
#             print(f"{dependency} 依赖已经安装.")
#             continue
#
#         installed = False
#         for mirror in mirrors:
#             try:
#                 # 配置pip命令以使用指定镜像和信任该镜像的主机名
#                 result = subprocess.run(
#                     [pip_path, "install", dependency, "-i", mirror, "--trusted-host",
#                      mirror.split('//')[1].split('/')[0]],
#                     check=True,
#                     stdout=subprocess.PIPE,
#                     stderr=subprocess.PIPE,
#                     text=True,
#                     encoding='utf-8',
#                     errors='replace'
#                 )
#                 if result.returncode == 0:
#                     success.append(dependency)
#                     installed = True
#                     print(f"成功安装 {dependency}，使用镜像 {mirror}。")
#                     break
#                 # else:
#                 #     print(f"尝试使用 {mirror} 安装 {dependency} 失败，错误信息：{result.stderr}")
#             # except subprocess.CalledProcessError as e:
#             #     print(f"使用 {mirror} 安装 {dependency} 时出现异常，异常信息：{e.stderr}")
#
#             except subprocess.CalledProcessError as e:
#                 error_message = e.stderr
#                 # 正则表达式匹配错误输出中的建议使用的正确包名
#                 match = re.search(r"use 'pip install ([^']+)'", error_message)
#                 if match:
#                     new_dependency = match.group(1)
#                     print(f"检测到建议使用 {new_dependency} 替代 {dependency}，尝试安装...")
#                     dependency = new_dependency  # 更新依赖为建议的包名
#                     continue  # 使用更新后的依赖重试安装过程
#
#                 print(f"尝试使用 {mirror} 安装 {dependency} 失败，错误信息：{error_message}")
#
#
#         if not installed:
#             print(f"所有镜像尝试失败，未能安装 {dependency}...自动跳过")
#             failures.append(dependency)
#
#     return success, failures

# 最早期的代码
# def install_dependencies(plugin_dir, dependencies):
#     plugin_files = get_plugin_files(plugin_dir)
#     pip_path = get_pip_path()
#     mirrors = [
#         "https://pypi.tuna.tsinghua.edu.cn/simple",
#         "http://mirrors.aliyun.com/pypi/simple",
#         "http://pypi.douban.com/simple/",
#         "https://pypi.mirrors.ustc.edu.cn/simple/",
#         "http://pypi.hustunique.com/",
#         "http://pypi.sdutlinux.org/",
#         "http://mirrors.163.com"
#     ]
#
#     success = []
#     failures = []
#
#     for dependency in dependencies:
#         print(f"准备安装依赖...{dependency}")
#         if dependency in plugin_files:
#             #print(f"跳过 {dependency} 。")
#             continue
#         elif is_package_installed(dependency):
#             print(f"{dependency} 依赖已经安装.")
#             continue
#
#         installed = False
#         for mirror in mirrors:
#             try:
#                 # 配置pip命令以使用指定镜像和信任该镜像的主机名
#                 result = subprocess.run(
#                     [pip_path, "install", dependency, "-i", mirror, "--trusted-host",
#                      mirror.split('//')[1].split('/')[0]],
#                     check=True,
#                     stdout=subprocess.PIPE,
#                     stderr=subprocess.PIPE,
#                     text=True,
#                     encoding='utf-8',
#                     errors='replace'
#                 )
#                 if result.returncode == 0:
#                     success.append(dependency)
#                     installed = True
#                     print(f"成功安装 {dependency}，使用镜像 {mirror}。")
#                     break
#                 else:
#                     print(f"尝试使用 {mirror} 安装 {dependency} 失败，错误信息：{result.stderr}")
#             except subprocess.CalledProcessError as e:
#                 print(f"使用 {mirror} 安装 {dependency} 时出现异常，异常信息：{e.stderr}")
#
#         if not installed:
#             print(f"所有镜像尝试失败，未能安装 {dependency}...自动跳过")
#             failures.append(dependency)
#
#     return success, failures

"""<其它常用类函数>"""
#绝对路径
def get_base_path(subdir=None):
    """
    获取基础路径，可选地附加一个子目录。
    :param subdir: 可选的子目录名。
    :return: 根据是否打包以及是否指定子目录返回相应的路径。
    """
    if getattr(sys, 'frozen', False):
        # 如果应用程序被打包成了单一文件
        base_path = sys._MEIPASS
    else:
        # 正常执行时使用文件的当前路径
        base_path = os.path.dirname(os.path.abspath(__file__))

    # 如果指定了子目录，将其追加到基路径
    if subdir:
        #base_path = os.path.join(base_path, subdir)
        base_path = os.path.normpath(os.path.join(base_path, subdir.replace("/", "\\")))

    return base_path

#搜索指定目录下是否有某文件名，如果有则返回True
def find_file_name(base_path, prefix, suffix):
    for filename in os.listdir(base_path):
        if filename.startswith(prefix) and filename.endswith(suffix):
            return True
    return False


# 打开文件夹
def open_folder(path):
    try:
        if not os.path.exists(path):
            raise FileNotFoundError(f"找不到该路径 {path} ")

        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", path])
        else:  # Linux and other Unix-like systems
            subprocess.run(["xdg-open", path])
        return f"Success: The folder '{path}' was opened."
    except Exception as e:
        return f"Error: Failed to open the folder '{path}'. {str(e)}"


# 自动安装依赖（官方）
def install_and_import(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return __import__(package)
    except subprocess.CalledProcessError:
        print(f"Failed to install {package}.")

# 检测JSON格式是否正确
def is_json_valid(json_data):
    """
    验证 JSON 字符串格式是否正确
    """
    try:
        data = json.loads(json_data)
        # 确保 JSON 数据是字典或列表
        if isinstance(data, (dict, list)):
            return True
        return False
    except json.JSONDecodeError:  # 专门捕获 JSON 解码错误
        return False
    except TypeError:  # 捕获非字符串类型错误，例如直接传递非序列化对象
        return False

#打开网页
def open_browser(website):
    webbrowser.open(website)

#创建plugins目录
def plugins_directory():
    base_path = get_base_path()
    plugins_path = os.path.join(base_path, 'plugins')

    if not os.path.exists(plugins_path):
        os.makedirs(plugins_path)
