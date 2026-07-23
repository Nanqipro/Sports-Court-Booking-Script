"""Load local configuration without exposing credentials in logs or reprs."""

import os
from configparser import ConfigParser, Error as ConfigError
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Optional, Union


TRUE_VALUES = {"1", "true", "yes", "on"}
FALSE_VALUES = {"0", "false", "no", "off"}


@dataclass(frozen=True)
class Settings:
    """Runtime settings. Password is deliberately excluded from repr output."""

    username: str = ""
    password: str = field(default="", repr=False)
    debug: bool = False
    request_timeout: float = 10.0
    max_attempts: int = 5
    retry_delay: float = 1.0
    token_refresh_interval: int = 5


def parse_bool(value: object, default: bool = False) -> bool:
    """Parse a conventional configuration boolean."""

    if value is None:
        return default
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    raise ValueError("DEBUG 必须是 true/false、yes/no、on/off 或 1/0")


def _positive_float(name: str, value: object) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} 必须是数字") from exc
    if parsed <= 0:
        raise ValueError(f"{name} 必须大于 0")
    return parsed


def _positive_int(name: str, value: object) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{name} 必须是整数") from exc
    if parsed <= 0:
        raise ValueError(f"{name} 必须大于 0")
    return parsed


def load_settings(
    config_path: Optional[Union[str, Path]] = None,
    environ: Optional[Mapping[str, str]] = None,
) -> Settings:
    """Load settings, with environment variables taking precedence over INI values."""

    env = os.environ if environ is None else environ
    selected_path = config_path or env.get("BADMINTON_CONFIG") or "config.ini"
    path = Path(selected_path).expanduser()

    parser = ConfigParser()
    if path.is_file():
        try:
            parser.read(path, encoding="utf-8")
        except ConfigError as exc:
            raise ValueError("配置文件格式无效") from exc
    section = parser["CONFIG"] if parser.has_section("CONFIG") else {}

    def value(name: str, default: str) -> str:
        env_value = env.get(name)
        if env_value is not None and env_value != "":
            return env_value
        config_value = section.get(name, "")
        return config_value if config_value != "" else default

    return Settings(
        username=value("BADMINTON_USERNAME", "").strip(),
        password=value("BADMINTON_PASSWORD", ""),
        debug=parse_bool(value("DEBUG", "false")),
        request_timeout=_positive_float("REQUEST_TIMEOUT", value("REQUEST_TIMEOUT", "10")),
        max_attempts=_positive_int("MAX_ATTEMPTS", value("MAX_ATTEMPTS", "5")),
        retry_delay=_positive_float("RETRY_DELAY", value("RETRY_DELAY", "1")),
        token_refresh_interval=_positive_int(
            "TOKEN_REFRESH_INTERVAL", value("TOKEN_REFRESH_INTERVAL", "5")
        ),
    )
