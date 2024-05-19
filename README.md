# PlugLink

作者：心易

![LOGO横](https://github.com/zhengqia/PlugLink/assets/155066150/ddfd70b3-3c20-4bb1-b362-94425f902c85)

## 关于PlugLink
PlugLink顾名思义，插件的链接，您的自动化机器人。
- 前端：layui框架
- 后端：python
- 数据库：SQLite
- 适应操作系统：WINDOWS
- 开发工具：pycharm/VSCode

PlugLink用于链接各种脚本、API、AI大模型，实现全自动工作流程。它可以显著降低应用层开发周期，帮助企业实现自动化办公，降本增效。PlugLink每个插件均可自由无序链接成不同的工作流并自动化运作，适应多种复杂工作场景。

最重要的是：它是开源的。PlugLink可以部署在企业或个人计算机上，自由开发及使用，不受第三方平台规则的限制。

## 为什么要使用PlugLink？
- 大幅降低办公应用开发成本；
- 全自动化24小时无人运行工作流；
- 创造您的商业模式；
- 自产自销，不受第三方影响；
- 技术门槛极低，易上手；
- 开源：自由和开放；
- 共赢生态；
- 为您的创造力提供无限可能。

即将准备：
- [链接AI大模型接口](#)
- [自动化编写代码](#)
- [自动化文案、配音合成视频](#)
- [AI自动合成无限产品视频（用于引流）](#)

## 下载PlugLink及相关信息
- PlugLink官方网址：www.pluglink.cn www.pluglink.ai www.pluglink.dev （网站均未开放）
- 我的飞书主页： [飞书主页](https://drgphlxsfa.feishu.cn/wiki/GeuMwglQdi65BbkclgLcBUCFnRf)

当前发布的是PlugLink 1.0.0 bate 个人学习版，实际是测试版，不确定正式版发布时间，视开发情况而定。

应用版下载地址：
- [应用版下载](https://pan.baidu.com/s/19tinAQNFDxs-041Zn7YwcQ?pwd=PLUG) 提取码：PLUG


## PlugLink的作者
我是心易，一个喜欢搞技术的商人。我并不是技术大佬，但喜欢通过软件技术实现商业构思。

PlugLink虽然是服务于商业，但希望与技术人员一起实现一些创新的想法。

可加我微信交流：aixzxinyi8

## PlugLink商业合作
开放的合作模式：
- 开放合作的生态系统，鼓励不同领域的企业和个人加入，共同开发和利用这个平台。
- 提供了一个平台，让开发者、企业、教育机构和爱好者能够分享他们的脚本、API集成方案、AI模型和其他创新技术。

合作模式：
- 开发者合作
- 软件厂商合作
- 投资者合作
- 企业服务

## PlugLink基本操作

### 基本界面

打开软件后，首先会显示一个运行过程界面，显示程序运行状态，对开发者非常友好。接着会弹出一个网页界面，所有的操作界面都在网页上进行。

<img width="760" alt="图片 1" src="https://github.com/zhengqia/PlugLink/assets/155066150/62db262b-603e-4692-84d3-e41c9f89e1e8">

<img width="760" alt="图片 2" src="https://github.com/zhengqia/PlugLink/assets/155066150/23ae0bc2-fcf3-409d-ae0a-9ae2519a151c">


### 开始

#### 办公

这是日常工作的快捷导航区，可以添加常用的插件和网址。


#### AI工具大全/学习中心

收集了各大好用的AI相关网站，未来会不断更新资源，让PlugLink成为你的工作伙伴。




### 应用

#### 我的插件中心

成功安装的所有插件都会显示在这里，当前版本提供两个始发插件：视频合成工具、视频相似度检测工具。

- **查看信息**：查看开发者信息及帮助文档。
- **立即使用**：使用该插件，但不是工作流。
- **添加到快捷方式**：将插件添加到“办公”首页中。

#### 添加/卸载插件
<img width="1081" alt="图片 3" src="https://github.com/zhengqia/PlugLink/assets/155066150/5fa09c72-4021-439b-b1ff-8c50502fa1a5">


将插件放置到`plugins`目录下（必须先解压），会自动扫描并加载到本页。使用插件前需先安装。

#### 临时文件管理
一些插件会产生大量文件，例如视频合成工具，可以在这里批量清理无用文件。

#### 应用商店
可以下载新的插件，当前版本没有线上自动更新功能，仅能从飞书中获取下载链接并手动安装。



## PlugLink开发者手册
开发者手册分为两个部分：编程的标准方法和部署到PlugLink。

### 编程的标准方法
插件开发示例文件包包含以下文件：
- python文件：main.py, api.py, \_\_init\_\_.py
- HTML文件夹：static, templates
- 插件文件夹：plugins，目前有两个始发插件供参考，需要自行下载依赖包到libs文件夹下
- 插件开发标准示例在：pluginDEMO文件夹中

- `main.py`：基本代码结构已经写好，按注释操作实现功能。文件名必须为`main.py`。
- `\_\_init\_\_.py`：插件初始化文件，若不需要初始化可留空。
- `api.py`：用于接受嵌入工作流的插件，按注释操作实现功能。文件名不可修改。

文件夹结构：
- `static`：存放静态文件，如CSS和JS。
- `templates`：存放Jinja2模板文件。

注意事项：
1. 每个插件都在虚拟环境下使用独立依赖包，需将依赖包放置于插件的`libs`目录下。
2. 使用`get_base_path`函数获取路径。
3. 插件目录下放置`requirements.txt`文件，方便新版本使用。

### 部署到PlugLink
<img width="377" alt="图片 4" src="https://github.com/zhengqia/PlugLink/assets/155066150/78e1058b-81bd-4c25-acf0-49936d359be1">

开发好的插件放到`plugins`目录下，然后进入“部署我的插件”进行注册。注册后可以导出插件，分享给其他用户。


#### 插件开发：部署我的插件
<img alt="图片 4" src="https://github.com/zhengqia/PlugLink/assets/155066150/bc1d61cf-358e-41db-8c3f-7dc8e560633a">

插件放置后需进入“部署我的插件”进行注册，注册后会生成一个`ThePlugin.json`文件。


#### 插件开发：我的开发列表
可以查看所有已注册的插件，进行安装/卸载操作。注册好插件后可以导出为zip格式，分享给其他用户。


#### 工作流：创建工作流
<img width="829" alt="图片 6" src="https://github.com/zhengqia/PlugLink/assets/155066150/70088d53-5b81-4eff-950d-67b3bf5d7980">
<img width="773" alt="图片 9" src="https://github.com/zhengqia/PlugLink/assets/155066150/edf60fa7-5057-4904-b053-33a58278e500">

在这里可以创建全自动化工作流，将所有插件链接在一起，实现自动化运行。配置完成后，点击“测试工作流”，测试成功后即可运行。

配置工作流的步骤：
1. **添加插件到工作流**：至少两个任务才能启动运行，插件可以重复添加。
2. **配置任务**：每个任务有一排按钮，分别用于配置执行脚本、保存配置、删除任务、排序等。
3. **保存配置**：将配置保存到工作流，确保任务能正确执行。


#### 工作流列表
![图片 13](https://github.com/zhengqia/PlugLink/assets/155066150/63c41075-39c6-4c83-8367-13172d27a86e)

随时可以重新配置或运行已创建的工作流。运行工作流时，可以切换页面，但不能关闭程序或同时运行多个工作流。

“清理本地存储”按钮可清理所有进度信息，解决进度卡死等问题。
