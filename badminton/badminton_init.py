# pip install ddddocr requests pycryptodome beautifulsoup4 configparser -i https://pypi.tuna.tsinghua.edu.cn/simple
import ddddocr
import requests
import os
import time
from configparser import ConfigParser
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import base64
from Crypto.Cipher import AES  
from Crypto.Util.Padding import pad, unpad 
from typing import Dict, Any, Optional, Union, Tuple

def getEnv(env: str, default: Any = "", required: bool = False) -> str:
    """
    从配置文件或环境变量获取配置参数
    
    Parameters
    ----------
    env : str
        环境变量名称
    default : Any
        默认值
    required : bool
        是否必须
        
    Returns
    -------
    str
        配置值
    """
    if os.path.exists("config.ini"):
        config = ConfigParser()
        config.read("config.ini", encoding="utf-8")
        if config.has_option("CONFIG", env):
            return config["CONFIG"][env]
    if os.environ.get(env):
        return os.getenv(env)
    if required:
        raise Exception(f"Env {env} is required")
    return default

# 从环境变量获取调试模式设置
debug = getEnv("DEBUG", True)

# 系统域名配置
ndyy = "ndyy.ncu.edu.cn"
cas = "cas.ncu.edu.cn"
loginUrl = (
    f"https://{cas}:8443/cas/login?service=http%3A%2F%2F{ndyy}%3A8089%2Fcas%2Flogin"
)
session = requests.Session()
headers = {
    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/120.0 Mobile/15E148 Safari/605.1.15",
    "connection": "close",
}
session.headers.update(headers)

def log(level: str, msg: str) -> None:
    """
    日志输出函数
    
    Parameters
    ----------
    level : str
        日志级别
    msg : str
        日志消息
    """
    if debug and level == "DEBUG":
        print(f"[{datetime.now()}] [DEBUG]: {msg}")
    else:
        print(f"[{datetime.now()}] [{level}]: {msg}")
        

def getXToken(username: str, password: str) -> Optional[str]:
    """
    获取系统登录Token
    
    Parameters
    ----------
    username : str
        用户名
    password : str
        密码
        
    Returns
    -------
    Optional[str]
        登录Token
    """
    response = session.get(loginUrl)
    soup = BeautifulSoup(response.text, "html.parser")
    data = {
        "username": username,
        "password": password,
        "rememberMe": False,
        "captcha": soup.find("input", {"name": "captcha"}).get("value"),
        "currentMenu": soup.find("input", {"name": "currentMenu"}).get("value"),
        "failN": soup.find("input", {"name": "failN"}).get("value"),
        "mfaState": soup.find("input", {"name": "mfaState"}).get("value"),
        "execution": soup.find("input", {"name": "execution"}).get("value"),
        "_eventId": soup.find("input", {"name": "_eventId"}).get("value"),
        "geolocation": soup.find("input", {"name": "geolocation"}).get("value"),
        "submit": soup.find("input", {"name": "submit"}).get("value"),
    }
    response = session.post(loginUrl, data=data)
    parsed_url = urlparse(response.request.path_url)
    query_params = parse_qs(parsed_url.query)
    token = query_params.get('token', [None])[0]
    log("DEBUG", token)
    return token


def getCaptcha(token: str) -> requests.Response:
    """
    获取验证码
    
    Parameters
    ----------
    token : str
        登录Token
        
    Returns
    -------
    requests.Response
        验证码响应对象
    """
    url_captcha = "https://ndyy.ncu.edu.cn/api/generateCaptcha"
    headers_captcha = {
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
        "Referer": "https://ndyy.ncu.edu.cn/booking",
        "Token": token,
    }
    session.headers.update(headers_captcha) 
    response_captcha = session.get(url_captcha)
    return response_captcha

KEY = b'ndyyM1m2c3$0j9m8'
IV = b'ncuHe110F*4g5htt'

def pad(data: bytes) -> bytes:
    """
    使用PKCS#7填充数据
    
    Parameters
    ----------
    data : bytes
        需要填充的数据
        
    Returns
    -------
    bytes
        填充后的数据
    """
    # 使用PKCS#7填充
    padding_length = AES.block_size - (len(data) % AES.block_size)
    padding = bytes([padding_length]) * padding_length
    return data + padding

def unpad(data: bytes) -> bytes:
    """
    移除PKCS#7填充
    
    Parameters
    ----------
    data : bytes
        带填充的数据
        
    Returns
    -------
    bytes
        移除填充后的数据
    """
    # 移除PKCS#7填充
    if not data:
        return data
    padding_length = data[-1]
    if padding_length > AES.block_size:
        return data  # 不是有效的填充，返回原始数据
    if len(data) < padding_length:
        return data  # 数据长度不足，不能移除填充
    # 验证所有填充字节是否相同
    if data[-padding_length:] != bytes([padding_length]) * padding_length:
        return data  # 填充无效，返回原始数据
    return data[:-padding_length]

def Encrypt(word: str, keyStr: Optional[str] = None, ivStr: Optional[str] = None) -> str:
    """
    AES加密函数
    
    Parameters
    ----------
    word : str
        需要加密的文本
    keyStr : Optional[str]
        加密密钥
    ivStr : Optional[str]
        初始化向量
        
    Returns
    -------
    str
        加密后的Base64编码字符串
    """
    key = KEY if keyStr is None else keyStr.encode('utf-8')
    iv = IV if ivStr is None else ivStr.encode('utf-8')
    data = pad(word.encode('utf-8'))
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(data)
    encrypted_base64 = base64.b64encode(encrypted).decode('utf-8')
    return encrypted_base64

def Decrypt(word: str, keyStr: Optional[str] = None, ivStr: Optional[str] = None) -> bytes:
    """
    AES解密函数
    
    Parameters
    ----------
    word : str
        需要解密的Base64编码字符串
    keyStr : Optional[str]
        解密密钥
    ivStr : Optional[str]
        初始化向量
        
    Returns
    -------
    bytes
        解密后的二进制数据
    """
    key = KEY if keyStr is None else keyStr.encode('utf-8')
    iv = IV if ivStr is None else ivStr.encode('utf-8')
    encrypted_data = base64.b64decode(word)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted = cipher.decrypt(encrypted_data)
    decrypted = unpad(decrypted)
    return decrypted

def decodeCaptcha(captcha_data: Dict[str, Any]) -> Optional[str]:
    """
    解码验证码
    
    Parameters
    ----------
    captcha_data : Dict[str, Any]
        验证码数据
        
    Returns
    -------
    Optional[str]
        识别后的验证码文本
    """
    captcha_base64 = captcha_data.get("captchaImg")
    if not captcha_base64:
        log("ERROR", "获取的验证码数据中缺少 'captchaImg' 键")
        print(captcha_data)
        return None
    
    log("DEBUG", f"验证码数据类型: {type(captcha_base64)}")
    log("DEBUG", f"验证码数据长度: {len(captcha_base64)}")
    log("DEBUG", f"验证码数据前30字符: {captcha_base64[:30]}")
    
    # 首先尝试直接作为Base64编码的图像数据处理
    if ',' in captcha_base64:
        # 如果包含逗号分隔符，可能是标准的Base64编码图像
        header, encoded = captcha_base64.split(',', 1)
        log("DEBUG", f"检测到Base64头部: {header}")
        try:
            image_data = base64.b64decode(encoded)
            log("DEBUG", "直接Base64解码成功")
        except Exception as e:
            log("ERROR", f"Base64解码失败: {str(e)}")
            return None
    else:
        # 如果没有逗号分隔符，尝试解密
        try:
            decrypted_data = Decrypt(captcha_base64)
            log("DEBUG", f"解密后数据类型: {type(decrypted_data)}")
            log("DEBUG", f"解密后数据长度: {len(decrypted_data)}")
            
            # 检查解密后的数据是否为图像
            if decrypted_data.startswith(b'\xff\xd8\xff'):  # JPEG文件头
                log("DEBUG", "检测到JPEG图像头部")
                image_data = decrypted_data
            else:
                # 尝试从解密后的数据中提取Base64编码
                try:
                    # 查找可能的Base64编码头部
                    if b',' in decrypted_data:
                        header, encoded = decrypted_data.split(b',', 1)
                        log("DEBUG", f"从解密数据中找到Base64头部: {header}")
                        image_data = base64.b64decode(encoded)
                    else:
                        # 尝试直接解码
                        log("DEBUG", "尝试直接解码解密后的数据")
                        try:
                            image_data = base64.b64decode(decrypted_data)
                        except:
                            # 如果解码失败，可能就是原始二进制数据
                            image_data = decrypted_data
                except Exception as e:
                    log("ERROR", f"处理解密数据时出错: {str(e)}")
                    # 最后尝试直接使用解密后的数据
                    image_data = decrypted_data
        except Exception as e:
            log("ERROR", f"解密失败: {str(e)}")
            # 解密失败时尝试直接解码Base64
            try:
                image_data = base64.b64decode(captcha_base64)
                log("DEBUG", "直接Base64解码成功")
            except Exception as e2:
                log("ERROR", f"Base64解码也失败: {str(e2)}")
                return None
    
    # 保存图像数据到文件
    captcha_file = 'captcha1.jpg'
    with open(captcha_file, 'wb') as f:
        f.write(image_data)
    log("DEBUG", "保存图片文件成功")
    
    # 使用OCR识别验证码
    try:
        ocr = ddddocr.DdddOcr()
        image = open(captcha_file, "rb").read()
        result = ocr.classification(image)
        log("DEBUG", f"OCR识别结果: {result}")
        return result
    except Exception as e:
        log("ERROR", f"OCR识别失败: {str(e)}")
        return None

def cleanup_temp_files() -> None:
    """
    清理程序生成的临时文件
    """
    temp_files = ['captcha1.jpg']
    for file in temp_files:
        try:
            if os.path.exists(file):
                os.remove(file)
                log("DEBUG", f"临时文件 {file} 已删除")
        except Exception as e:
            log("ERROR", f"删除临时文件 {file} 失败: {str(e)}")

def makeReservation(token: str, captcha_result: str, date: str, startTime: str, areaName: str, areaNickname: str) -> requests.Response:
    """
    提交场地预约请求
    
    Parameters
    ----------
    token : str
        登录Token
    captcha_result : str
        验证码结果
    date : str
        预约日期，格式为YYYY-MM-DD
    startTime : str
        预约时间段，格式为HH:MM-HH:MM
    areaName : str
        场地名称
    areaNickname : str
        场地代码
        
    Returns
    -------
    requests.Response
        预约请求响应对象
    """
    url_reservation = "https://ndyy.ncu.edu.cn/api/badminton/saveReservationInformation"
    
    params = {
        "role": "ROLE_STUDENT",
        "date": date,
        "startTime": startTime,
        "areaName": areaName,
        "areaNickname": areaNickname,
        "captcha": captcha_result  
    }
    headers_reservation = {
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
        "Referer": "https://ndyy.ncu.edu.cn/booking",
        "Token": token,
    }
    session.headers.update(headers_reservation)  # 更新 session 的 headers
    response_reservation = session.get(url_reservation, params=params)
    return response_reservation

def get_user_input() -> Tuple[str, str, str, str, str, str]:
    """
    获取用户输入的预约信息
    
    Returns
    -------
    Tuple[str, str, str, str, str, str]
        用户名、密码、预约日期、时间段、场地名称、场地代码
    """
    # 默认账号密码
    DEFAULT_USERNAME = "419100240107"
    DEFAULT_PASSWORD = "31415926535@Zj"
    
    # 可选时间段列表
    TIME_SLOTS = [
        "08:00-09:00", "09:00-10:00", "10:00-11:00", "11:00-12:00", 
        "12:00-13:00", "13:00-14:00", "14:00-15:00", "15:00-16:00", 
        "16:00-17:00", "17:00-18:00", "18:00-19:00", "19:00-20:00", 
        "20:00-21:00", "21:00-22:00"
    ]
    
    # 尝试从环境变量获取用户名密码（安全做法）
    username = getEnv("BADMINTON_USERNAME")
    password = getEnv("BADMINTON_PASSWORD")
    
    # 如果环境变量中没有，则请求用户输入
    if not username:
        username_input = input("请输入学号(直接回车使用默认账号): ")
        username = username_input if username_input.strip() else DEFAULT_USERNAME
    
    if not password:
        import getpass
        password_input = getpass.getpass("请输入密码(直接回车使用默认密码): ")
        password = password_input if password_input.strip() else DEFAULT_PASSWORD
    
    # 获取预约日期，默认为后天
    day_after_tomorrow = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    date_input = input(f"请输入预约日期(格式:YYYY-MM-DD，直接回车预约{day_after_tomorrow}): ")
    date = date_input if date_input.strip() else day_after_tomorrow
    
    # 时间段选择
    print("\n可选时间段:")
    for i, time_slot in enumerate(TIME_SLOTS, 1):
        print(f"{i}. {time_slot}")
    
    time_choice = input("\n请选择时间段编号(1-14): ")
    try:
        time_idx = int(time_choice) - 1
        if 0 <= time_idx < len(TIME_SLOTS):
            startTime = TIME_SLOTS[time_idx]
        else:
            print("无效选择，默认选择12:00-13:00")
            startTime = "12:00-13:00"
    except ValueError:
        print("输入格式错误，默认选择12:00-13:00")
        startTime = "12:00-13:00"
    
    # 场地选择
    print("\n可选场地:")
    print("1. 羽毛球1号场地 (hall1)")
    print("2. 羽毛球2号场地 (hall2)")
    print("3. 羽毛球3号场地 (hall3)")
    print("4. 羽毛球4号场地 (hall4)")
    print("5. 羽毛球5号场地 (hall5)")
    print("6. 羽毛球6号场地 (hall6)")
    print("7. 羽毛球7号场地 (hall7)")
    print("8. 羽毛球8号场地 (hall8)")
    print("9. 羽毛球9号场地 (hall9)")
    print("10. 羽毛球10号场地 (hall10)")
    print("11. 羽毛球11号场地 (hall11)")
    print("12. 羽毛球12号场地 (hall12)")
    
    choice = input("\n请选择场地编号(1-12): ")
    try:
        hall_num = int(choice)
        if 1 <= hall_num <= 12:
            areaName = f"羽毛球{hall_num}号场地"
            areaNickname = f"hall{hall_num}"
        else:
            print("无效选择，默认选择7号场地")
            areaName = "羽毛球7号场地"
            areaNickname = "hall7"
    except ValueError:
        print("输入格式错误，默认选择7号场地")
        areaName = "羽毛球7号场地"
        areaNickname = "hall7"
    
    print(f"\n预约信息确认:")
    print(f"日期: {date}")
    print(f"时间段: {startTime}")
    print(f"场地: {areaName}")
    
    return username, password, date, startTime, areaName, areaNickname

def get_start_time() -> Optional[datetime]:
    """
    获取用户指定的预约开始执行时间
    
    Returns
    -------
    Optional[datetime]
        用户指定的开始执行时间，如果不指定则返回None
    """
    use_timer = input("\n是否需要定时执行？(y/n，默认n): ").strip().lower()
    
    if use_timer != 'y':
        print("\n未设置定时，系统将立即开始执行预约程序")
        return None
    
    now = datetime.now()
    
    # 获取小时
    while True:
        hour_input = input("请输入开始执行的小时(0-23，24小时制): ")
        try:
            hour = int(hour_input)
            if 0 <= hour <= 23:
                break
            else:
                print("输入的小时必须在0到23之间，请重新输入")
        except ValueError:
            print("请输入有效的数字")
    
    # 获取分钟
    while True:
        minute_input = input("请输入开始执行的分钟(0-59): ")
        try:
            minute = int(minute_input)
            if 0 <= minute <= 59:
                break
            else:
                print("输入的分钟必须在0到59之间，请重新输入")
        except ValueError:
            print("请输入有效的数字")
    
    # 创建目标时间
    target_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    
    # 如果目标时间已经过去，则设置为明天的这个时间
    if target_time < now:
        print("设定的时间已过去，将在明天的这个时间执行")
        target_time = target_time + timedelta(days=1)
    
    print(f"\n系统将在 {target_time.strftime('%Y-%m-%d %H:%M:%S')} 开始执行预约")
    
    return target_time

def wait_until(target_time: datetime) -> None:
    """
    等待直到指定的时间
    
    Parameters
    ----------
    target_time : datetime
        目标时间
    """
    now = datetime.now()
    
    if now >= target_time:
        return
    
    wait_seconds = (target_time - now).total_seconds()
    
    # 如果等待时间超过5分钟，每分钟显示一次倒计时
    if wait_seconds > 300:
        minutes_to_wait = int(wait_seconds / 60)
        for i in range(minutes_to_wait, 0, -1):
            if i % 5 == 0 or i <= 5:  # 每5分钟或最后5分钟每分钟提示一次
                print(f"距离开始执行还有 {i} 分钟...")
            time.sleep(60)
        
        # 剩余不足1分钟的秒数
        remaining_seconds = wait_seconds % 60
        if remaining_seconds > 0:
            print(f"最后倒计时 {int(remaining_seconds)} 秒...")
            time.sleep(remaining_seconds)
    else:
        # 等待时间不长，直接等待
        print(f"等待 {int(wait_seconds)} 秒后开始执行...")
        time.sleep(wait_seconds)
    
    print("开始执行预约程序!")

def attempt_reservation(username: str, password: str, date: str, 
                      startTime: str, areaName: str, areaNickname: str,
                      max_attempts: int = 10, retry_interval: int = 3) -> bool:
    """
    尝试进行场地预约，失败时自动重试
    
    Parameters
    ----------
    username : str
        用户名
    password : str
        密码
    date : str
        预约日期
    startTime : str
        预约时间段
    areaName : str
        场地名称
    areaNickname : str
        场地代码
    max_attempts : int
        最大尝试次数
    retry_interval : int
        重试间隔(秒)
        
    Returns
    -------
    bool
        是否预约成功
    """
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        log("INFO", f"开始第 {attempt} 次预约尝试")
        
        try:
            # 获取登录token
            token = getXToken(username, password)
            if not token:
                log("ERROR", "获取Token失败，重试中...")
                time.sleep(retry_interval)
                continue
                
            log("INFO", f"获取到Token: {token}")
            
            # 获取验证码
            response_captcha = getCaptcha(token)
            if response_captcha.status_code != 200:
                log("ERROR", f"获取验证码失败，状态码：{response_captcha.status_code}")
                log("DEBUG", response_captcha.text)
                time.sleep(retry_interval)
                continue
                
            captcha_data = response_captcha.json()
            captcha_result = decodeCaptcha(captcha_data)
            
            if not captcha_result:
                log("ERROR", "验证码识别失败，重试中...")
                time.sleep(retry_interval)
                continue
            
            # 提交预约
            response_reservation = makeReservation(token, captcha_result, date, startTime, areaName, areaNickname)
            
            # 检查响应
            if response_reservation.status_code != 200:
                log("ERROR", f"预约请求失败，状态码：{response_reservation.status_code}")
                log("DEBUG", response_reservation.text)
                time.sleep(retry_interval)
                continue
                
            # 解析响应内容
            result = response_reservation.json()
            
            # 处理可能的业务错误
            if 'status' in result and result['status'] == 200:
                log("INFO", "预约成功!")
                print(result.get('message', ''))
                print(result)
                return True
            else:
                error_msg = result.get('message', '未知错误')
                log("ERROR", f"预约失败: {error_msg}")
                
                # 如果是验证码错误，直接重试，其他错误增加等待时间
                if '验证码' in error_msg:
                    time.sleep(1)
                else:
                    time.sleep(retry_interval)
        
        except Exception as e:
            log("ERROR", f"预约过程出现异常: {str(e)}")
            time.sleep(retry_interval)
    
    log("ERROR", f"达到最大尝试次数 {max_attempts}，预约失败")
    return False

if __name__ == "__main__":
    log("INFO", "BEGIN")
    
    try:
        # 获取用户输入
        username, password, date, startTime, areaName, areaNickname = get_user_input()
        
        # 获取开始执行时间
        start_time = get_start_time()
        
        # 如果设置了定时，等待到指定时间
        if start_time:
            wait_until(start_time)
        
        # 开始轮询预约
        success = False
        retry_count = 0
        max_retries = 50  # 最大重试次数
        
        print("\n开始预约流程，将持续尝试直到成功或达到最大尝试次数...")
        
        while not success and retry_count < max_retries:
            retry_count += 1
            log("INFO", f"第 {retry_count} 轮预约尝试")
            
            # 尝试预约
            success = attempt_reservation(
                username, password, date, startTime, areaName, areaNickname,
                max_attempts=3, retry_interval=2
            )
            
            if not success:
                # 失败后等待几秒再试
                wait_time = 5
                log("INFO", f"本轮预约失败，{wait_time} 秒后重试...")
                time.sleep(wait_time)
        
        if success:
            log("INFO", "预约流程成功完成!")
        else:
            log("ERROR", f"达到最大重试次数 {max_retries}，预约彻底失败")
            
    except KeyboardInterrupt:
        log("INFO", "用户中断程序")
    except Exception as e:
        log("ERROR", f"程序运行异常: {str(e)}")
    finally:
        # 清理临时文件
        cleanup_temp_files()
        log("INFO", "END")
