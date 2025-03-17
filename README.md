# 体育场地预约自动化脚本

这是一个用于自动预约羽毛球场地的Python脚本集合，专为南昌大学体育场地预约系统设计。脚本提供多种预约模式和功能，满足不同场景的预约需求。

## 功能特点

- **自动登录**: 使用学号密码自动登录体育场地预约系统
- **验证码识别**: 自动识别并处理预约系统的验证码
- **定时预约**: 支持在指定时间（如中午12点）自动触发预约流程
- **交互式预约**: 提供用户交互界面，可自定义预约时间、场地和触发条件
- **错误重试**: 内置错误处理和重试机制，提高预约成功率
- **批量预约**: 支持通过脚本同时预约多个场地

## 安装依赖

使用以下命令安装所需的Python库:

```bash
pip install ddddocr requests pycryptodome beautifulsoup4 configparser -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 脚本说明

本项目包含多个脚本文件，适用于不同场景：

- **badminton_while_verification.py**: 带验证码处理的定时预约脚本，在指定时间（默认12点）自动预约
- **badminton_noWhile.py**: 无定时功能的直接预约脚本，运行后立即进行预约
- **badminton_while_noVerification1.py**: 交互式预约脚本，提供用户界面自定义预约信息
- **badminton_while_noVerification2.py**: 简化版定时预约脚本，硬编码预约信息（无需用户输入）
- **run.sh**: Linux/Mac下批量运行多个预约脚本的Shell脚本

## 使用指南

### 1. 基本配置

在使用脚本前，需要修改脚本中的用户名和密码：

```python
# 将 username 和 password 替换为自己的学号和密码
username = "你的学号"
password = "你的密码"
```

### 2. 预约信息配置

根据需要修改预约场地、时间等信息：

```python
date = "2024-03-20"          # 预约日期
startTime = "19:00-20:00"    # 预约时间段
areaName = "羽毛球1号场地"    # 场地名称
areaNickname = "hall1"       # 场地代码
```

### 3. 运行脚本

#### 交互式预约
```bash
python badminton_while_noVerification1.py
```
按照提示输入预约信息和目标触发时间。

#### 自动定时预约
```bash
python badminton_while_verification.py
```
或
```bash
python badminton_while_noVerification2.py
```

#### 批量预约（Linux/Mac）
```bash
chmod +x run.sh
./run.sh
```

## 注意事项

1. 请合理使用脚本，不要过度占用公共资源
2. 预约成功后请按时使用场地，避免浪费
3. 脚本默认配置可能需要根据最新的预约系统进行调整
4. 建议提前测试脚本功能，确保在正式预约时能够正常运行

## 免责声明

本脚本仅供学习和个人使用，请遵守相关规定和道德准则。开发者不对因使用本脚本造成的任何问题负责。
