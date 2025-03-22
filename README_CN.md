# NCU体育场地预约自动化脚本

中文文档 | [English Document](README.md)

这是一个用于自动预约羽毛球场地的Python脚本集合，专为南昌大学体育场地预约系统设计。脚本提供多种预约模式和功能，满足不同场景的预约需求。

## 功能特点

- **自动登录** 🔑: 使用学号密码自动登录体育场地预约系统
- **验证码识别** 👁️: 自动识别并处理预约系统的验证码
- **定时预约** ⏰: 支持在指定时间（如中午12点）自动触发预约流程
- **交互式预约** 💬: 提供用户交互界面，可自定义预约时间、场地和触发条件
- **错误重试** 🔄: 内置错误处理和重试机制，提高预约成功率
- **批量预约** 📋: 支持通过脚本同时预约多个场地和时间段
- **配置灵活** ⚙️: 支持通过配置文件或环境变量设置账号信息

## 安装依赖 🛠️

### 创建虚拟环境 🐍

强烈建议在虚拟环境中运行此项目，以避免依赖冲突：

```bash
# 安装virtualenv（如果尚未安装）
pip install virtualenv

# 创建虚拟环境
cd d:\GitHub_local\Sports-Court-Booking-Script
virtualenv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/MacOS:
# source venv/bin/activate
```

### 安装依赖包 📦

在激活的虚拟环境中，使用以下命令安装所需的Python库：

```bash
pip install -r requirements.txt
```

或者直接安装：

```bash
pip install ddddocr requests pycryptodome beautifulsoup4 configparser -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 脚本说明 📃

本项目包含多个脚本文件，适用于不同场景：

- **badminton_multi_you_need.py** 🌟: 功能最全面的多场地多时间段预约脚本，支持配置文件、交互式界面和定时预约
- **badminton_all_you_need** 🔹: 适用于单场单时间段预约，支持配置文件、交互式界面和定时预约

## 使用指南 🚀

### 1. 配置方式 ⚙️

badminton_multi_you_need.py支持两种配置方式：

- **环境变量**：设置BADMINTON_USERNAME和BADMINTON_PASSWORD环境变量
- **配置文件**：在同目录下创建config.ini文件，包含以下内容：
  ```ini
  [CONFIG]
  BADMINTON_USERNAME=你的学号
  BADMINTON_PASSWORD=你的密码
  DEBUG=True
  ```

如果不配置，脚本会在运行时提示输入。

### 2. 脚本使用方法（两种方式）🔧

#### 方式一：执行Python脚本 💻

1. 进入项目文件夹：
   ```bash
   cd d:\GitHub_local\Sports-Court-Booking-Script\badminton
   ```

2. 运行脚本：
   ```bash
   python badminton_multi_you_need.py
   ```

#### 方式二：使用打包好的可执行文件 📦

1. 可执行文件位置：
   ```
   d:\GitHub_local\Sports-Court-Booking-Script\badminton\dist\badminton_multi_you_need\badminton_multi_you_need.exe
   ```

2. 直接双击运行，或在命令行中执行：
   ```bash
   cd d:\GitHub_local\Sports-Court-Booking-Script\badminton\dist\badminton_multi_you_need
   badminton_multi_you_need.exe
   ```

### 3. 交互式配置 ⌨️

运行脚本后，按照提示进行操作：

1. **输入学号和密码**：直接回车将使用默认值或配置文件中的值
2. **选择预约日期**：格式为YYYY-MM-DD，直接回车默认预约后天的场地
3. **选择时间段**：输入时间段编号（如 1,2,3），多个时间段用英文逗号分隔
   - 可选时间段包括：08:00-09:00, 09:00-10:00, ..., 21:00-22:00
4. **选择场地**：输入场地编号（如 1,2,3），多个场地用英文逗号分隔
   - 可选场地编号为1-12，对应羽毛球1-12号场地
5. **设置预约触发时间**：输入开始预约的目标时间（24小时制，如12:00）
   - 系统将在指定时间开始执行预约任务

### 4. 预约流程 🔄

1. 脚本会等待直到达到设置的触发时间 ⏳
2. 自动登录系统并获取Token 🔐
3. 自动识别验证码 🧩
4. 按顺序尝试预约所有选定的场地和时间段 📋
5. 遇到错误会自动重试，每个预约任务最多尝试5次 🔁
6. 预约成功的任务会从队列中移除 ✅
7. 最终输出预约结果统计 📊

### 5. 注意事项 ⚠️

- 每次尝试预约后会有短暂等待，避免请求过于频繁
- 每5次尝试会自动刷新一次Token
- 脚本会自动清理生成的临时文件（如验证码图片）
- 预约成功或达到最大尝试次数后，程序会自动退出

## 其他脚本的使用 📝

### 1. 基本配置

其他脚本需要修改脚本中的用户名和密码：

```python
# 将 username 和 password 替换为自己的学号和密码
username = "你的学号"
password = "你的密码"
```

### 2. 预约信息配置

根据需要修改预约场地、时间等信息：

```python
date = "2025-03-20"          # 预约日期
startTime = "19:00-20:00"    # 预约时间段
areaName = "羽毛球1号场地"    # 场地名称
areaNickname = "hall1"       # 场地代码
```

## 故障排除 🔍

1. 验证码识别失败：检查是否正确安装了ddddocr库 🖼️
2. 登录失败：确认账号密码正确，检查网络连接 🔒
3. 预约失败：检查日期和时间是否有效，场地是否已被预约 📅
4. 其他错误：查看日志输出，根据错误信息进行调整 📋

## 免责声明 ⚖️

本脚本仅供学习和个人使用，请遵守相关规定和道德准则。开发者不对因使用本脚本造成的任何问题负责。
