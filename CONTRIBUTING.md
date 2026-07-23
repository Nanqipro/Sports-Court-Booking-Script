# 参与贡献

感谢你愿意改进 NCU Court Booking。这个项目直接处理账号登录与线上预约请求，因此安全和可验证性比功能数量更重要。

## 开始开发

~~~bash
python -m venv .venv
source .venv/bin/activate  # Windows 请使用 .\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
~~~

## 提交建议

1. 每个 Pull Request 只解决一个明确问题。
2. 新增纯逻辑时同时补充不访问网络的单元测试。
3. 不提交真实学号、密码、Token、Cookie、验证码、接口完整响应或含个人信息的截图。
4. 不用自动化测试访问生产预约系统；网络行为请通过 mock、fixture 或本地替身验证。
5. 修改接口字段、时间段或场地映射时，在说明中写明证据来源和验证日期。
6. 不提交 <code>build/</code>、<code>dist/</code>、本地配置或 IDE 元数据。

## 提交前检查

~~~bash
python -m unittest discover -s tests -v
python -m compileall -q ncu_booking run.py tests
git diff --check
~~~

若问题涉及凭据泄漏，请立即轮换凭据，不要在公开 Issue 中粘贴敏感内容。

