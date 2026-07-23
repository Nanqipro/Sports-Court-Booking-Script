<p align="center">
  <img src="docs/readme-assets/readme-hero.svg" alt="NCU Court Booking：南昌大学羽毛球场地预约助手" width="100%">
</p>

<p align="center">
  <strong>中文</strong> · <a href="README_EN.md">English</a>
</p>

# NCU Court Booking

一个面向南昌大学羽毛球场地预约流程的交互式 Python 命令行工具：安全读取账号、定时启动、组合多个时间段与场地，并对临时失败进行有限重试。

> [!IMPORTANT]
> 项目目前是实验性工具，并未在当前线上预约系统完成端到端验证。学校接口、开放时间和使用规则可能变化；请先运行 <code>--dry-run</code>，并遵守学校规定，避免高频请求。

## 为什么重新整理

原仓库包含多份近似脚本、个人账号默认值、IDE 文件和约 200 MiB 的 PyInstaller 构建产物。当前结构将功能合并为一个入口，并重点解决：

- **凭据安全**：不再提供硬编码账号或密码；密码输入默认不回显。
- **可维护性**：配置、领域模型、网络客户端和交互流程分开组织。
- **可预演**：<code>--dry-run</code> 只展示预约计划，不读取账号、不登录、不发送网络请求。
- **有限重试**：每个任务有明确的最大次数、请求超时和会话刷新间隔。
- **仓库轻量化**：二进制构建产物不进入 Git，需要时可由 spec 文件重新生成。

## 工作流程

<p align="center">
  <img src="docs/readme-assets/booking-workflow.svg" alt="从配置预约计划到登录、识别验证码、提交预约和汇总结果的六步流程" width="100%">
</p>

一次运行会把所选“时间段 × 场地”展开为独立任务。成功任务立即退出队列，失败任务只在配置的次数内重试；程序不会无限刷接口。

## 快速开始

### 1. 准备环境

需要 Python 3.9 或更高版本。依赖中的 OCR/ONNX 组件能否安装取决于操作系统与 Python 版本，请优先使用主流的 64 位 Python。

~~~bash
git clone https://github.com/Nanqipro/Sports-Court-Booking-Script.git
cd Sports-Court-Booking-Script

python -m venv .venv
~~~

激活虚拟环境：

~~~bash
# macOS / Linux
source .venv/bin/activate

# Windows PowerShell
.\.venv\Scripts\Activate.ps1
~~~

安装依赖：

~~~bash
python -m pip install -r requirements.txt
~~~

### 2. 先做一次演练

~~~bash
python -m ncu_booking --dry-run
~~~

演练模式会让你选择日期、时间段、场地与触发时间，但不会要求账号或访问预约系统。

### 3. 正式运行

~~~bash
python -m ncu_booking
~~~

程序默认等待到你设置的触发时间再开始。若已确认时机并希望立即运行：

~~~bash
python -m ncu_booking --run-now
~~~

也可以使用兼容入口：

~~~bash
python run.py
~~~

## 账号与配置

最安全的方式是不保存密码：运行时输入学号和密码，密码不会在终端回显。

如果希望预填非敏感设置，可以复制示例文件：

~~~bash
cp config.example.ini config.ini
~~~

Windows PowerShell 可使用：

~~~powershell
Copy-Item config.example.ini config.ini
~~~

<code>config.ini</code> 已被 <code>.gitignore</code> 忽略。环境变量的优先级高于配置文件；也可以通过 <code>--config PATH</code> 指定其他 INI 文件。

| 配置项 | 默认值 | 用途 |
| --- | ---: | --- |
| <code>BADMINTON_USERNAME</code> | 空 | 学号；为空时交互输入 |
| <code>BADMINTON_PASSWORD</code> | 空 | 密码；建议保持为空并在运行时输入 |
| <code>DEBUG</code> | <code>false</code> | 输出调试日志，但不会打印密码或 Token |
| <code>REQUEST_TIMEOUT</code> | <code>10</code> | 单次 HTTP 请求超时秒数 |
| <code>MAX_ATTEMPTS</code> | <code>5</code> | 每个预约任务最多尝试次数 |
| <code>RETRY_DELAY</code> | <code>1</code> | 失败任务再次尝试前的等待秒数 |
| <code>TOKEN_REFRESH_INTERVAL</code> | <code>5</code> | 每多少次预约请求刷新登录会话 |

只设置学号的示例：

~~~bash
# macOS / Linux
export BADMINTON_USERNAME="你的学号"
python -m ncu_booking
~~~

~~~powershell
# Windows PowerShell
$env:BADMINTON_USERNAME = "你的学号"
python -m ncu_booking
~~~

## 命令行参数

~~~text
--config PATH  指定本地 INI 配置
--run-now      跳过定时等待，立即执行
--dry-run      只生成计划，不登录或发送请求
--debug        输出调试日志
~~~

查看完整帮助：

~~~bash
python -m ncu_booking --help
~~~

## 项目结构

~~~text
.
├── ncu_booking/
│   ├── cli.py          # 交互输入、定时、重试和结果汇总
│   ├── client.py       # CAS 登录、验证码识别和预约请求
│   ├── config.py       # 环境变量与本地 INI 配置
│   └── models.py       # 预约计划、场地和任务模型
├── tests/              # 不访问网络的单元测试
├── packaging/          # 可选的 PyInstaller 构建配置
├── docs/readme-assets/ # README 自有视觉素材
├── config.example.ini  # 可公开复制的配置模板
└── requirements.txt
~~~

## 测试与可选打包

单元测试不会访问学校系统：

~~~bash
python -m unittest discover -s tests -v
~~~

可选的 PyInstaller 构建方式：

~~~bash
python -m pip install -r requirements-dev.txt
pyinstaller --clean packaging/ncu-court-booking.spec
~~~

构建结果会进入 <code>dist/</code>，不会被 Git 跟踪。当前 spec 尚未在 Windows 上重新验证，因此发布 EXE 前请在干净的 Windows 环境完成实际运行测试。

## 安全与隐私

- 账号密码只用于南昌大学 CAS 登录请求，验证码由本地 <code>ddddocr</code> 处理。
- 程序不会记录密码或完整 Token，也不会把验证码图片写入仓库。
- 不要把 <code>config.ini</code>、真实请求响应、学号、Token 或报错截图中的个人信息提交到 Issue。
- 仓库旧历史曾包含硬编码凭据；在公开现有 Git 历史前，必须轮换相关密码并清理历史，或创建一个不带旧历史的全新公开仓库。

## 已知限制

- 目前只覆盖南昌大学羽毛球预约接口和代码中列出的 12 个场地。
- 时间段、场地标识、CAS 页面字段和验证码协议都可能随校方系统更新而失效。
- OCR 结果与预约成功率均不受保证；程序不会绕过权限、支付或校方规则。
- 自动化请求可能受到服务条款、频率限制或临时维护影响，使用者需自行确认合规性。

## 参与贡献

欢迎提交小而清晰的修复。开始前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)，并确保测试不使用真实账号、不访问生产预约接口。

## 许可证

**许可证尚未确定。** 仓库公开可见不等于获得开源授权；在权利人添加 <code>LICENSE</code> 前，请勿复制、分发或再授权本项目。仓库所有者可在发布前选择 MIT、Apache-2.0、GPL-3.0 等合适许可证。

---

本项目与南昌大学官方无隶属或背书关系，仅作为个人学习与流程自动化实验使用。
