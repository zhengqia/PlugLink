from moviepy.editor import VideoFileClip, concatenate_videoclips,CompositeVideoClip
import os,json,shutil,sys,threading
from flask import jsonify
from itertools import permutations,product
from moviepy.video.fx.fadein import fadein
from moviepy.video.fx.fadeout import fadeout
from collections import defaultdict


#绝对路径
def get_base_path(subdir=None):
    if getattr(sys, 'frozen', False):
        # 如果应用程序被打包成了单一文件
        base_path = sys._MEIPASS
        base_path = os.path.join(base_path, 'plugins','videosyn')
    else:
        # 正常执行时使用文件的当前路径
        base_path = os.path.dirname(os.path.abspath(__file__))
    # 如果指定了子目录，将其追加到基路径
    if subdir:
        base_path = os.path.normpath(os.path.join(base_path, subdir.replace("/", "\\")))

    return base_path
"""
前端函数
"""
#扫描总目录
def Dir_Scan(path):
    """
    扫描指定路径下的所有文件夹并返回结果。
    参数:
        path: 用户输入的路径
    返回:
        字典，包含扫描结果或错误信息
    """
    # 确保路径不为空且存在
    if not path or not os.path.exists(path):
        return {"error": "路径无效或不存在"}

    try:
        # 获取路径下所有项，筛选出文件夹，忽略文件
        dirs_full_path={}
        dirs = [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
        if len(dirs) < 2:
            return {"error": "目录数不能少于2个"}
        # 构建完整的目录路径列表返回
        dirs_full_path = [os.path.join(path, d) for d in dirs]
        print(dirs_full_path)

    except Exception as e:
        # 捕捉到异常时返回错误信息
        return {"error": str(e)}

# 定义上传的基础目录路径
#BASE_DIRECTORY = os.path.join(os.getcwd(), 'upload')
# def get_base_path():
#     if getattr(sys, 'frozen', False):
#         # 如果应用程序被打包成了单一文件，使用这个路径
#         base_path = sys._MEIPASS
#     else:
#         # 如果是正常执行，使用这个路径
#         base_path = os.path.dirname(os.path.abspath(__file__))
#
#     # 在基路径下添加 upload 目录
#     return os.path.join(base_path, "upload")


# 创建上传总目录和子目录
def create_directory(totalDirName, subdirName):
    base_dir = get_base_path('upload')

    # 确保 upload 总目录存在
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    totalDirPath = os.path.join(base_dir, totalDirName)
    subdir_path = os.path.join(totalDirPath, subdirName)

    # 确保总目录存在
    if not os.path.exists(totalDirPath):
        os.makedirs(totalDirPath)

    # 创建或检查子目录
    if not os.path.exists(subdir_path):
        os.makedirs(subdir_path)
        return jsonify({'message': '目录创建成功', 'exists': False}), 200
    else:
        return jsonify({'message': '目录已存在', 'exists': True}), 200




# 删除上传子目录或总目录
# def delete_directory(dirName):
#     base_dir = get_base_path('upload')
#     dirPath = os.path.join(base_dir, dirName)
#     #print(dirPath)
#     if os.path.exists(dirPath):
#         shutil.rmtree(dirPath)
#         return jsonify({'message': '目录删除成功'}), 200
#     else:
#         # 如果尝试删除的目录不存在
#         return jsonify({'message': '目录不存在'}), 400

def delete_directory(totalDirName,subdirName,lastOne):
    # 检查 totalDirName 和 subdirName 是否提供
    if not totalDirName or not subdirName:
        return jsonify({'message': '丢失目录名称'}), 400

    # 构建完整的目录路径并尝试删除
    dirPath = os.path.join(get_base_path('upload'), totalDirName, subdirName)
    if lastOne:
        dirPath = os.path.join(get_base_path('upload'), totalDirName)

    if os.path.exists(dirPath):
        shutil.rmtree(dirPath)
        return jsonify({'message': '子目录删除成功'}), 200
    else:
        return jsonify({'message': '目录不存在'}), 400
"""
表单分析函数
"""

API_Data = {}

#扫描本地视频目录及文件
def scan_directories(total_dir_name):
    directories = {}
    base_path = os.path.join(get_base_path('upload'), total_dir_name) # 修改为你的基础路径

    for subdir, dirs, files in os.walk(base_path):
        for dir in dirs:
            dir_path = os.path.join(subdir, dir)
            directories[dir] = [file for file in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, file))]
    #print(f"扫码保存至：{directories}")
    return directories

# 统一重命名
def rename_files(filename):
    # 遍历指定目录下的所有子目录
    for subdir, _, _ in os.walk(filename):
        # 忽略根目录
        if subdir == filename:
            continue
        print(f"初始路径：{filename}")
        # 获取子目录中所有文件，并按文件名排序
        files = [f for f in os.listdir(subdir) if os.path.isfile(os.path.join(subdir, f))]
        files.sort()  # 可以根据需要调整排序逻辑

        # 检查是否需要重命名该子目录下的文件
        rename_needed = False
        for file in files:
            _, file_extension = os.path.splitext(file)
            # 如果文件名不是以数字开头，则需要重命名
            #if not file[0].isdigit():
            if not file.isdigit():
                rename_needed = True
                break

        # 如果不需要重命名，则跳过该子目录
        if not rename_needed:
            continue

        # 初始化文件序号
        file_number = 1

        # 遍历并重命名每个文件
        for file in files:
            file_path = os.path.join(subdir, file)
            # 获取文件扩展名
            _, file_extension = os.path.splitext(file)
            # 构建新的文件名
            new_filename = f"{file_number}{file_extension}"
            new_file_path = os.path.join(subdir, new_filename)

            # 重命名文件
            os.rename(file_path, new_file_path)

            # 序号递增
            file_number += 1

#添加表单数据
def add_videos_info(uploadedVideosInfo,
                               custom_order,
                               directories_order,
                               total_dir_name,
                               head_dir,
                               tail_dir,
                               enable_transitions,
                               transition_duration,
                               output_extension,
                               output_dir):
    global API_Data
    API_Data = {}
    # 假设存储JSON文件的目录
    #dir = os.getcwd()
    dir = get_base_path()  # 获取基础路径
    filename=dir + '\\upload\\'+total_dir_name
    str_list = []
    # 重命名分组视频名称
    rename_files(filename)
    #添加视频目录数据
    # for key, value in uploadedVideosInfo.items():
    #     folder_name = key
    #     for video_name in value:
    #         str_list.append(f"{filename}\\{folder_name}\\{video_name}")
    for key in uploadedVideosInfo.keys():
        folder_path = os.path.join(filename, key)

        # 使用 os.walk 遍历文件夹及其子文件夹
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                str_list.append(file_path)

    API_Data['vid'] = str_list
    API_Data['totalDirName'] = total_dir_name
    API_Data['totalfilename'] = filename

    #是否按目录顺序合并
    API_Data['custom_order'] = []  # 初始化一个空列表
    if custom_order == "True" and directories_order is not None:
        # 如果用户选择了"是的"，处理目录顺序
        for dir_name in directories_order:
            path = f'{filename}/{dir_name}'
            path = path.replace('/', '\\')  # 将 / 替换为 \\
            API_Data['custom_order'].append(path)
    else:
        # 如果用户选择了"不要"
        API_Data['custom_order'] = None

    #处理片头片尾
    API_Data['head_dir'] = []
    API_Data['tail_dir'] = []
    if head_dir:
        head_dir_path = os.path.join(filename, head_dir)
        if os.path.exists(head_dir_path):
            path = head_dir_path.replace('/', '\\')
            API_Data['head_dir'].append(path)


    # 检查并处理“片尾指定”目录
    if tail_dir:
        tail_dir_path = os.path.join(filename, tail_dir)
        if os.path.exists(tail_dir_path):
            path = tail_dir_path.replace('/', '\\')
            API_Data['tail_dir'].append(path)


    #传递三项参数：渐变转场状态、转场时长、输出格式
    API_Data['enable_transitions'] = []
    API_Data['transition_duration'] = []
    API_Data['output_extension'] = []
    transition_duration = float(transition_duration)
    if transition_duration <= 0:
        raise ValueError('值不能小于 0.')

    # 保存数据到API_Data
    API_Data['enable_transitions'].append(enable_transitions)
    API_Data['transition_duration'].append(transition_duration)
    API_Data['output_extension'].append(output_extension)

    # 保存输出路径
    API_Data['output_dir'] = []
    if not output_dir:# 如果用户没有提供输出目录，使用默认路径
        output_dir = dir + '\\output\\'+total_dir_name
    elif not os.path.isabs(output_dir):# 如果提供的路径不是绝对路径，构造一个新的路径
        output_dir = os.path.join(dir, output_dir)

    API_Data['output_dir'].append(output_dir)

    #保存API接口
    #print(API_Data)
    save_API(API_Data)
    vcnum = cp_viddata(API_Data)
    ets='不要'
    if API_Data['enable_transitions']:ets = '是的'
    if API_Data['custom_order'] == None: custom_order = '不要'
    print(f"合并数：{vcnum}")
    description = (f"\n"
                   f"  本次信息保存到插件根目录下api.json，有需要可以根据此接口调用执行。\n"
                   f"  如需要修改，则直接修改后再保存即可\n"
                   f"===================本次保存的信息==================\n"
                   f"  视频可合并数：{vcnum}个\n"
                   f"  是否按目录顺序合并：{custom_order}\n"
                   f"  指定片头目录：\n"
                   f"  {API_Data['head_dir']}\n"
                   f"  指定片尾目录：\n"
                   f"  是否转场：{ets}\n"
                   f"  转场时长：{API_Data['transition_duration']}\n"
                   f"  输出格式：{API_Data['output_extension']}\n"
                   f"  输出目录：{API_Data['output_dir']}\n"
                   f"\n")


    return description

# 运算目录下视频数据
def cp_viddata(API_Data):
    # 解析视频路径以分组
    parent_dir = API_Data['totalfilename']
    # 调用get_subdirectories函数获取所有子目录
    dirs = get_subdirectories(parent_dir)

    head_dir = ''.join(API_Data['head_dir'])
    tail_dir = ''.join(API_Data['tail_dir'])

    custom_order = API_Data['custom_order']
    print(f"检查head_dir值:{head_dir}")
    print(f"检查tail_dir值:{tail_dir}")
    all_videos = {dir_path: get_video_files(dir_path) for dir_path in dirs}
    print(f"检查all_videos值:{all_videos}")
    dir_sequences = process_custom_order(custom_order, dirs)
    print(f"检查dir_sequences值:{dir_sequences}")

    filtered_combinations = []
    for seq in dir_sequences:
        # 根据当前序列生成视频组合
        current_combinations = list(product(*[all_videos[dir_path] for dir_path in seq]))
        # 如果指定了head_dir或tail_dir，则进行筛选
        if head_dir or tail_dir:
            current_combinations = [comb for comb in current_combinations if
                                    (not head_dir or comb[0].startswith(head_dir)) and
                                    (not tail_dir or comb[-1].startswith(tail_dir))]
        filtered_combinations.extend(current_combinations)

    return len(filtered_combinations)



#保存API数据
def save_API(API_Data):
    base_path = get_base_path()  # 获取基础路径
    api_path = os.path.join(base_path, 'api.json')  # 构建完整的文件路径

    with open(api_path, 'w', encoding='utf-8') as json_file:
        json.dump(API_Data, json_file, ensure_ascii=False, indent=4)
    return True

"""
执行视频合并过程函数
"""
#加载本地api.json
def load_api_data():
    global API_Data
    api_file_path = os.path.join(get_base_path(), 'api.json')  # 获取api.json文件的完整路径

    with open(api_file_path, 'r', encoding='utf-8') as file:
        API_Data = json.load(file)

#打开目录位置
def get_output_dir():
    return API_Data.get('output_dir', '')  # 如果不存在output_dir键，则返回空字符串

"""
视频合并函数
"""
#全局变量用于中止任务
is_task_running = True

# 全局变量，用于存储进度信息
global_progress = {'completed': 0, 'total': 0}

def get_video_files(dir_path):
    """获取指定目录下所有视频文件的路径列表"""
    supported_formats = ('.mp4', '.avi', '.mov', '.mkv')
    return [os.path.join(dir_path, f) for f in os.listdir(dir_path) if f.endswith(supported_formats)]


def adjust_combinations(dirs, combinations, head_dir, tail_dir):
    """根据head_dir和tail_dir调整组合"""
    if head_dir or tail_dir:
        adjusted = []
        for combination in combinations:
            if head_dir and not combination[0].startswith(head_dir):
                continue
            if tail_dir and not combination[-1].startswith(tail_dir):
                continue
            adjusted.append(combination)
        return adjusted
    return combinations


def generate_output_filename(combination, output_extension):
    """生成符合规定格式的文件名"""
    name_parts = [os.path.basename(os.path.dirname(f)) + "_" + os.path.splitext(os.path.basename(f))[0] for f in
                  combination]
    return "_and_".join(name_parts) + output_extension


def apply_transitions(clips, transition_duration=0.5, apply_to_start=False):
    """为视频片段列表添加淡入淡出转场效果，可选是否在视频开头应用转场"""
    transitioned_clips = []
    for i, clip in enumerate(clips):
        # 如果不在视频开头应用转场效果，跳过第一个片段的转场处理
        if i == 0 and not apply_to_start:
            transitioned_clips.append(clip)
            continue
        clip_with_transition = fadein(clip, transition_duration).fadeout(transition_duration)
        transitioned_clips.append(clip_with_transition)
    return transitioned_clips


def process_custom_order(custom_order, dirs):
    """
    处理自定义顺序，将自定义顺序中的条目转换为绝对路径，并确保它们存在于 dirs 中。
    返回一个列表，包含按 custom_order 指定顺序的 dirs 中的条目。
    """
    if not custom_order:
        return list(permutations(dirs))

    processed_order = []
    for item in custom_order:
        # 转换为绝对路径
        abs_path = item if os.path.isabs(item) else os.path.join(os.getcwd(), item)
        # 检查路径是否在 dirs 中
        if abs_path in dirs:
            processed_order.append(abs_path)

    # 如果处理后的顺序为空，或者不完全匹配 dirs，则返回所有可能的排列
    if not processed_order or set(processed_order) != set(dirs):
        return list(permutations(dirs))

    # 返回处理后的自定义顺序（只有一个顺序）
    return [processed_order]

def get_subdirectories(parent_dir):
    """获取指定目录下所有直接子目录的完整路径列表"""
    return [os.path.join(parent_dir, name) for name in os.listdir(parent_dir)
            if os.path.isdir(os.path.join(parent_dir, name))]

# 任务中止
def stop_task():
    global is_task_running
    is_task_running = False
    print('任务被中止')

# 调用-主执行函数
def running_merge_videos():
    load_api_data()
    # thread = threading.Thread(target=call_merge_videos)
    # thread.start()
    call_merge_videos()
    output_dir = get_output_dir()

    return {'output_dir': output_dir}

# 主执行函数
def call_merge_videos():
    global is_task_running  # 为False强制中止任务
    is_task_running = True
    # 从API_Data获取totalfilename，这是包含视频子目录的父目录
    parent_dir = API_Data['totalfilename']

    # 调用get_subdirectories函数获取所有子目录
    dirs = get_subdirectories(parent_dir)


    try:
        print("开始执行 call_merge_videos...")
        #dirs = [API_Data['totalfilename']]  # dirs 应为目录列表，但这里我们使用单一目录
        output_dir = API_Data['output_dir'][0] if API_Data['output_dir'] else ""

        head_dir = API_Data.get('head_dir', [])[0] if API_Data.get('head_dir', []) else ""
        tail_dir = API_Data.get('tail_dir', [])[0] if API_Data.get('tail_dir', []) else ""
        custom_order = API_Data.get('custom_order', None)
        enable_transitions = API_Data['enable_transitions'][0] if API_Data['enable_transitions'] else False
        transition_duration = API_Data['transition_duration'][0] if API_Data['transition_duration'] else 0.5
        output_extension = API_Data['output_extension'][0] if API_Data['output_extension'] else ".mp4"

        # 调用 merge_videos 函数
        merge_videos(
            dirs=dirs,
            output_dir=output_dir,
            head_dir=head_dir,
            tail_dir=tail_dir,
            custom_order=custom_order,
            enable_transitions=enable_transitions,
            transition_duration=transition_duration,
            output_extension=output_extension
        )
        print("完成视频合成，更新全局进度...")
    except Exception as e:
        print(f"call_merge_videos 函数执行出错：{e}")

def merge_videos(dirs,
                 output_dir,
                 head_dir='',
                 tail_dir='',
                 output_extension='.mp4',
                 custom_order=None,
                 enable_transitions=False,
                 transition_duration=0.5,
                 apply_to_start=False):

    try:
        # 处理 output_dir
        if not os.path.isabs(output_dir):
            output_dir = os.path.join(os.getcwd(), output_dir)
        # 确保输出目录存在
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # 处理 head_dir 和 tail_dir
        head_dir = os.path.join(os.getcwd(), head_dir) if head_dir and not os.path.isabs(head_dir) else head_dir
        tail_dir = os.path.join(os.getcwd(), tail_dir) if tail_dir and not os.path.isabs(tail_dir) else tail_dir
        print(f"检查head_dir值:{head_dir}")
        print(f"检查tail_dir值:{tail_dir}")
        all_videos = {dir_path: get_video_files(dir_path) for dir_path in dirs}
        print(f"检查all_videos值:{all_videos}")
        # 处理 custom_order
        # if custom_order:
        #     custom_order = [os.path.join(os.getcwd(), dir) if not os.path.isabs(dir) else dir for dir in custom_order]
        #     dir_sequences = [custom_order] if all(dir in dirs for dir in custom_order) else []
        # else:
        #     dir_sequences = list(permutations(dirs))
        dir_sequences = process_custom_order(custom_order, dirs)
        print(f"检查dir_sequences值:{dir_sequences}")

        filtered_combinations = []
        for seq in dir_sequences:
            # 根据当前序列生成视频组合
            current_combinations = list(product(*[all_videos[dir_path] for dir_path in seq]))
            # 如果指定了head_dir或tail_dir，则进行筛选
            if head_dir or tail_dir:
                current_combinations = [comb for comb in current_combinations if
                                        (not head_dir or comb[0].startswith(head_dir)) and
                                        (not tail_dir or comb[-1].startswith(tail_dir))]
            filtered_combinations.extend(current_combinations)

        total_combinations = len(filtered_combinations)
        completed_videos = 0

        global_progress['total'] = total_combinations
        global_progress['completed'] = 0  # 重置已完成视频数

        print(f"检查filtered_combinations值:{filtered_combinations}")
        global is_task_running #为False强制中止任务

        for combination in filtered_combinations:
            if not is_task_running:
                print(f'任务被中止{is_task_running}')# 如果任务被中止，跳出循环
                break
            try:
                print(f'{completed_videos}/{total_combinations}')

                clips = [VideoFileClip(f) for f in combination]

                # 根据 enable_transitions 参数决定是否应用转场效果
                transition_duration = float(transition_duration)
                if enable_transitions:
                    clips = apply_transitions(clips, transition_duration, apply_to_start)

                final_clip = concatenate_videoclips(clips, method="compose")
                output_filename = generate_output_filename(combination, output_extension)
                output_path = os.path.join(output_dir, output_filename)
                final_clip.write_videofile(output_path, codec="libx264", bitrate="8000k")

                completed_videos += 1
                global_progress['completed'] = completed_videos  # 更新全局进度

            except Exception as e:
                print(f"发生错误： {combination}: {e}")
                continue
        print('检测点2')
    except Exception as e:
        print(f"merge_videos 函数执行出错：{e}")

    return total_combinations, completed_videos


"""其它"""
# 设计命名规则
def get_next_filename(existing_filenames):
    # 检查文件名是否都是数字
    all_numeric = all(filename.isdigit() for filename in existing_filenames)

    # 如果文件名都是数字，则从最大数字递增1
    if all_numeric:
        next_number = max(map(int, existing_filenames)) + 1
        return str(next_number)
    else:
        # 否则从1开始命名，直到找到一个未被占用的数字
        i = 1
        while str(i) in existing_filenames:
            i += 1
        return str(i)

