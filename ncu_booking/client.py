"""HTTP client for the NCU CAS and badminton reservation endpoints."""

import base64
import logging
from typing import Any, Dict, Iterable, Optional
from urllib.parse import parse_qs, urlparse

from .config import Settings
from .models import BookingTask


LOGGER = logging.getLogger(__name__)
CAS_HOST = "cas.ncu.edu.cn"
BOOKING_HOST = "ndyy.ncu.edu.cn"
LOGIN_URL = (
    f"https://{CAS_HOST}:8443/cas/login?"
    f"service=http%3A%2F%2F{BOOKING_HOST}%3A8089%2Fcas%2Flogin"
)
CAPTCHA_URL = f"https://{BOOKING_HOST}/api/generateCaptcha"
RESERVATION_URL = f"https://{BOOKING_HOST}/api/badminton/saveReservationInformation"
REFERER_URL = f"https://{BOOKING_HOST}/booking"
USER_AGENT = (
    "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Mobile Safari/537.36"
)

# Public constants used by the booking site's CAPTCHA protocol; these are not user credentials.
KEY = b"ndyyM1m2c3$0j9m8"
IV = b"ncuHe110F*4g5htt"
LOGIN_FIELDS = (
    "captcha",
    "currentMenu",
    "failN",
    "mfaState",
    "execution",
    "_eventId",
    "geolocation",
    "submit",
)


class BookingError(RuntimeError):
    """A safe, user-facing booking workflow error."""


def _pkcs7_unpad(data: bytes, block_size: int = 16) -> bytes:
    if not data:
        raise BookingError("验证码解密结果为空")
    padding_length = data[-1]
    if padding_length < 1 or padding_length > block_size:
        raise BookingError("验证码填充格式无效")
    if data[-padding_length:] != bytes([padding_length]) * padding_length:
        raise BookingError("验证码填充校验失败")
    return data[:-padding_length]


def _is_image(data: bytes) -> bool:
    return data.startswith((b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n", b"GIF87a", b"GIF89a"))


def _decode_captcha_image(payload: str) -> bytes:
    """Decode either a data URL or the encrypted payload used by the booking site."""

    if not payload:
        raise BookingError("验证码响应中缺少图片数据")

    if "," in payload:
        _, encoded = payload.split(",", 1)
        try:
            image = base64.b64decode(encoded)
        except (ValueError, TypeError) as exc:
            raise BookingError("验证码图片 Base64 解码失败") from exc
        if not image:
            raise BookingError("验证码图片为空")
        return image

    try:
        from Crypto.Cipher import AES

        encrypted = base64.b64decode(payload)
        decrypted = AES.new(KEY, AES.MODE_CBC, IV).decrypt(encrypted)
        decrypted = _pkcs7_unpad(decrypted, AES.block_size)
    except BookingError:
        raise
    except Exception as exc:
        raise BookingError("验证码解密失败，预约接口可能已更新") from exc

    if _is_image(decrypted):
        return decrypted
    if b"," in decrypted:
        _, decrypted = decrypted.split(b",", 1)
    try:
        decoded = base64.b64decode(decrypted)
    except (ValueError, TypeError):
        decoded = decrypted
    if not decoded:
        raise BookingError("验证码解密后没有可识别的图片")
    return decoded


def _token_from_urls(urls: Iterable[str]) -> Optional[str]:
    for url in urls:
        token = parse_qs(urlparse(url).query).get("token", [None])[0]
        if token:
            return token
    return None


class BookingClient:
    """Stateful session that authenticates and submits booking requests."""

    def __init__(self, settings: Settings) -> None:
        try:
            import requests
        except ImportError as exc:
            raise BookingError("缺少 requests，请先安装 requirements.txt") from exc

        self.settings = settings
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT, "Connection": "close"})
        self._token: Optional[str] = None
        self._ocr: Any = None

    def __enter__(self) -> "BookingClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        self.session.close()

    @property
    def token(self) -> str:
        if not self._token:
            raise BookingError("尚未登录预约系统")
        return self._token

    def login(self, username: str, password: str) -> None:
        """Authenticate through CAS. Credentials and returned tokens are never logged."""

        try:
            from bs4 import BeautifulSoup

            response = self.session.get(LOGIN_URL, timeout=self.settings.request_timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            form: Dict[str, Any] = {
                "username": username,
                "password": password,
                "rememberMe": False,
            }
            for name in LOGIN_FIELDS:
                element = soup.find("input", {"name": name})
                if element is None:
                    raise BookingError(
                        f"登录页面缺少字段 {name}，CAS 页面可能已更新"
                    )
                form[name] = element.get("value", "")

            result = self.session.post(
                LOGIN_URL,
                data=form,
                timeout=self.settings.request_timeout,
            )
            result.raise_for_status()
        except BookingError:
            raise
        except Exception as exc:
            raise BookingError(
                "登录请求失败，请检查网络、账号或系统状态"
            ) from exc

        token = _token_from_urls(
            url
            for url in (
                getattr(result.request, "url", ""),
                getattr(result, "url", ""),
            )
            if url
        )
        if not token:
            raise BookingError(
                "登录响应中没有 Token，请检查账号或 CAS 流程是否变化"
            )
        self._token = token
        LOGGER.debug("登录成功，已安全保存会话 Token")

    def _recognize_captcha(self, image: bytes) -> str:
        try:
            import ddddocr

            if self._ocr is None:
                try:
                    self._ocr = ddddocr.DdddOcr(show_ad=False)
                except TypeError:
                    self._ocr = ddddocr.DdddOcr()
            result = str(self._ocr.classification(image)).strip()
        except Exception as exc:
            raise BookingError("验证码识别失败") from exc
        if not result:
            raise BookingError("验证码识别结果为空")
        return result

    def _captcha(self) -> str:
        try:
            response = self.session.get(
                CAPTCHA_URL,
                headers={
                    "Accept": "application/json, text/plain, */*",
                    "Referer": REFERER_URL,
                    "Token": self.token,
                },
                timeout=self.settings.request_timeout,
            )
            response.raise_for_status()
            payload = response.json()
            image_payload = payload.get("captchaImg") if isinstance(payload, dict) else None
            if not isinstance(image_payload, str):
                raise BookingError("验证码接口返回格式不符合预期")
            return self._recognize_captcha(_decode_captcha_image(image_payload))
        except BookingError:
            raise
        except Exception as exc:
            raise BookingError("获取验证码失败") from exc

    def reserve(self, task: BookingTask) -> Dict[str, Any]:
        """Submit one booking task and return the parsed server result."""

        captcha = self._captcha()
        params = {
            "role": "ROLE_STUDENT",
            "date": task.booking_date,
            "startTime": task.time_slot,
            "areaName": task.court.name,
            "areaNickname": task.court.nickname,
            "captcha": captcha,
        }
        try:
            response = self.session.get(
                RESERVATION_URL,
                params=params,
                headers={
                    "Accept": "application/json, text/plain, */*",
                    "Referer": REFERER_URL,
                    "Token": self.token,
                },
                timeout=self.settings.request_timeout,
            )
            response.raise_for_status()
            result = response.json()
        except Exception as exc:
            raise BookingError("提交预约请求失败") from exc
        if not isinstance(result, dict):
            raise BookingError("预约接口返回格式不符合预期")
        return result
