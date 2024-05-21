# PlugLink

[中文](README.md) | [English](README_US.md)

Author: Xin Yi

![LOGO Horizontal](https://github.com/zhengqia/PlugLink/assets/155066150/ddfd70b3-3c20-4bb1-b362-94425f902c85)

# Author's Preface
## May 20, 2024
Recently, I wrote a program called PlugLink. It's a framework for automated workflows, where any plugin can be integrated to form different workflows, enabling various complex application scenarios.

The initial purpose of creating this framework was to set up a development environment for myself. Although I've been in the IT industry for over 20 years, I'm not a professional developer. If I have to rebuild a framework every time I provide services to a company, it would waste a lot of time. More importantly, developing independently each time prevents companies from forming systematic processes. I needed a more general framework.

Thus, the PlugLink platform was born. PlugLink focuses on reducing development thresholds and costs. In the long run, it also has the feasibility of ecological management, so I want to open source it, believing that some people will benefit from it.

The current beta version includes two plugins: video synthesis and video detection. These meet specific needs of a company I serve and haven't yet formed a complete workflow. I'm working on other features, such as AI-generated content, automatic voiceover, and video editing. These will be automated, producing and publishing videos in bulk to various channels daily.

Beyond PlugLink, I hope to find like-minded partners, whether in technology, business, or strategy. I look forward to connecting with you...

# About PlugLink
PlugLink, as the name suggests, is the link of plugins, your automation robot.
- **Frontend:** Layui framework
- **Backend:** Python
- **Database:** SQLite
- **Operating System:** Windows
- **Development Tools:** PyCharm/VSCode

PlugLink links various scripts, APIs, and AI models to achieve fully automated workflows. It significantly reduces application development cycles and helps businesses achieve automated operations, reducing costs and increasing efficiency. Each PlugLink plugin can be freely linked in different workflows and run automatically, adapting to various complex work scenarios.

Most importantly: it is open source. PlugLink can be deployed on enterprise or personal computers, developed and used freely, without the constraints of third-party platform rules.

# Why Use PlugLink?
- Significantly reduce the cost of office application development;
- Fully automated workflows running 24/7 without human intervention;
- Create your business model;
- Self-produced and self-sold, without third-party influence;
- Very low technical threshold, easy to use;
- Open source: freedom and openness;
- Win-win ecosystem;
- Provide unlimited possibilities for your creativity.

Upcoming Features:
- [Link AI model interfaces](#)
- [Automated code writing](#)
- [Automated content creation, voiceover, and video synthesis](#)
- [AI-generated infinite product videos (for traffic generation)](#)

# Download PlugLink and Related Information
- PlugLink Official Website: www.pluglink.cn www.pluglink.ai www.pluglink.dev (websites not yet open)
- My Feishu Homepage: [Feishu Homepage](https://drgphlxsfa.feishu.cn/wiki/GeuMwglQdi65BbkclgLcBUCFnRf)

Currently, PlugLink 1.0.0 beta personal learning edition is released. It is essentially a test version, and the release date of the official version depends on the development progress.

Application Download Link:
- [Application Download](https://pan.baidu.com/s/19tinAQNFDxs-041Zn7YwcQ?pwd=PLUG) Code: PLUG

# PlugLink Author
I am Xin Yi, a businessman who likes technology. I'm not a tech expert but enjoy using software technology to realize business ideas.

Although PlugLink serves commercial purposes, I hope to achieve some innovative ideas with technical personnel.

Feel free to add me on WeChat for communication: aixzxinyi8

# PlugLink Business Cooperation
Open Cooperation Model:
- An open cooperative ecosystem encourages companies and individuals from different fields to join, develop, and utilize this platform together.
- Provides a platform for developers, enterprises, educational institutions, and enthusiasts to share their scripts, API integration solutions, AI models, and other innovative technologies.

Cooperation Models:
- Developer cooperation
- Software vendor cooperation
- Investor cooperation
- Enterprise services

# Basic Operation of PlugLink

## Basic Interface

After opening the software, a running process interface first appears, showing the program's running status, which is very developer-friendly. Then a webpage interface pops up, where all operations are conducted.

![Image 1](https://github.com/zhengqia/PlugLink/assets/155066150/62db262b-603e-4692-84d3-e41c9f89e1e8)
![Image 2](https://github.com/zhengqia/PlugLink/assets/155066150/23ae0bc2-fcf3-409d-ae0a-9ae2519a151c)

## Getting Started

### Office

This is the quick navigation area for daily work, where you can add frequently used plugins and websites.

### AI Tools & Learning Center

Collects various useful AI-related websites, which will be continuously updated in the future, making PlugLink your work partner.

## Applications

### My Plugin Center

All successfully installed plugins will be displayed here. The current version offers two initial plugins: video synthesis tool and video similarity detection tool.

- **View Info:** View developer information and help documentation.
- **Use Now:** Use the plugin, but not in a workflow.
- **Add to Shortcuts:** Add the plugin to the "Office" homepage.

### Add/Uninstall Plugins
![Image 3](https://github.com/zhengqia/PlugLink/assets/155066150/5fa09c72-4021-439b-b1ff-8c50502fa1a5)

Place the plugin in the `plugins` directory (must be unzipped first), it will be automatically scanned and loaded on this page. You need to install the plugin before using it.

### Temporary File Management
Some plugins generate a large number of files, such as the video synthesis tool. You can batch clean up unnecessary files here.

### App Store
You can download new plugins. The current version does not have an online automatic update function. You can only get download links from Feishu and manually install them.

# PlugLink Developer Manual
The developer manual is divided into two parts: standard programming methods and deployment to PlugLink.

## Standard Programming Methods
The plugin development example package contains the following files:
- Python files: `main.py`, `api.py`, `__init__.py`
- HTML folders: `static`, `templates`
- Plugin folders: `plugins`, currently with two initial plugins for reference, you need to download dependencies into the `libs` folder
- Plugin development standard example in: `pluginDEMO` folder

- `main.py`: The basic code structure is already written, follow the comments to implement functions. The file name must be `main.py`.
- `__init__.py`: Plugin initialization file, can be left empty if no initialization is needed.
- `api.py`: Used to accept plugins embedded in the workflow, follow the comments to implement functions. The file name cannot be changed.

Folder structure:
- `static`: Store static files such as CSS and JS.
- `templates`: Store Jinja2 template files.

Notes:
1. Each plugin uses independent dependencies in a virtual environment, which need to be placed in the plugin's `libs` directory.
2. Use the `get_base_path` function to get the path.
3. Place a `requirements.txt` file in the plugin directory for easy use in new versions.

## Deploying to PlugLink
![Image 4](https://github.com/zhengqia/PlugLink/assets/155066150/78e1058b-81bd-4c25-acf0-49936d359be1)

Place the developed plugin in the `plugins` directory, then enter "Deploy My Plugin" for registration. After registration, you can export the plugin and share it with other users.

### Plugin Development: Deploy My Plugin
![Image 5](https://github.com/zhengqia/PlugLink/assets/155066150/bc1d61cf-358e-41db-8c3f-7dc8e560633a)

After placing the plugin, enter "Deploy My Plugin" for registration. Registration generates a `ThePlugin.json` file.

### Plugin Development: My Development List
You can view all registered plugins and perform install/uninstall operations. After registering the plugin, it can be exported as a zip file and shared with other users.

### Workflow: Create Workflow
![Image 6](https://github.com/zhengqia/PlugLink/assets/155066150/70088d53-5b81-4eff-950d-67b3bf5d7980)
![Image 7](https://github.com/zhengqia/PlugLink/assets/155066150/edf60fa7-5057-4904-b053-33a58278e500)

Here you can create fully automated workflows by linking all plugins together for automatic operation. After configuration, click "Test Workflow." If the test is successful, you can run it.

Steps to configure the workflow:
1. **Add Plugins to Workflow:** At least two tasks are required to start running. Plugins can be added repeatedly.
2. **Configure Tasks:** Each task has a row of buttons for configuring execution scripts, saving configurations, deleting tasks, sorting, etc.
3. **Save Configuration:** Save the configuration to the workflow to ensure tasks execute correctly.

### Workflow List
![Image 8](https://github.com/zhengqia/PlugLink/assets/155066150/63c41075-39c6-4c83-8367-13172d27a86e)

You can reconfigure or run created workflows at any time. When running a workflow, you can switch pages, but you cannot close the program or run multiple workflows simultaneously.

The "Clear Local Storage" button clears all progress information, solving issues like progress freezing.
