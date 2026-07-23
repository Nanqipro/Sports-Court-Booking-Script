"""Interactive CLI for planning, scheduling, and retrying reservations."""

import argparse
import logging
import time
from datetime import datetime, timedelta
from getpass import getpass
from typing import Callable, List, Optional, Sequence, Tuple

from .client import BookingClient, BookingError
from .config import Settings, load_settings
from .models import BookingPlan, BookingTask, Court


LOGGER = logging.getLogger(__name__)
TIME_SLOTS: Tuple[str, ...] = tuple(
    f"{hour:02d}:00-{hour + 1:02d}:00" for hour in range(8, 22)
)
COURTS: Tuple[Court, ...] = tuple(
    Court(number=number, name=f"羽毛球{number}号场地", nickname=f"hall{number}")
    for number in range(1, 13)
)


def parse_number_choices(raw: str, minimum: int, maximum: int, default: int) -> List[int]:
    """Parse comma-separated menu choices and remove duplicates while preserving order."""

    normalized = raw.replace("，", ",").strip()
    if not normalized:
        return [default]
    selected: List[int] = []
    for item in normalized.split(","):
        try:
            number = int(item.strip())
        except ValueError as exc:
            raise ValueError(f"{item!r} 不是有效编号") from exc
        if number < minimum or number > maximum:
            raise ValueError(f"编号必须在 {minimum}–{maximum} 之间")
        if number not in selected:
            selected.append(number)
    return selected


def build_tasks(plan: BookingPlan) -> List[BookingTask]:
    return [
        BookingTask(plan.booking_date, time_slot, court)
        for time_slot in plan.time_slots
        for court in plan.courts
    ]


def _prompt_until_valid(prompt: str, parser: Callable[[str], object]) -> object:
    while True:
        try:
            return parser(input(prompt))
        except ValueError as exc:
            print(f"输入有误：{exc}")


def _booking_date(raw: str) -> str:
    default = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    selected = raw.strip() or default
    try:
        return datetime.strptime(selected, "%Y-%m-%d").strftime("%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("日期格式应为 YYYY-MM-DD") from exc


def _target_time(raw: str) -> Tuple[int, int]:
    selected = raw.strip() or "12:00"
    try:
        parsed = datetime.strptime(selected, "%H:%M")
    except ValueError as exc:
        raise ValueError("触发时间格式应为 HH:MM，例如 12:00") from exc
    return parsed.hour, parsed.minute


def collect_plan() -> BookingPlan:
    default_date = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
    booking_date = _prompt_until_valid(
        f"预约日期 [默认 {default_date}]：", _booking_date
    )

    print("\n可选时间段：")
    for index, slot in enumerate(TIME_SLOTS, 1):
        print(f"  {index:>2}. {slot}")
    slot_numbers = _prompt_until_valid(
        "选择时间段编号，多个用逗号分隔 [默认 5]：",
        lambda raw: parse_number_choices(raw, 1, len(TIME_SLOTS), 5),
    )

    print("\n可选场地：")
    for court in COURTS:
        print(f"  {court.number:>2}. {court.name}")
    court_numbers = _prompt_until_valid(
        "选择场地编号，多个用逗号分隔 [默认 7]：",
        lambda raw: parse_number_choices(raw, 1, len(COURTS), 7),
    )
    target_hour, target_minute = _prompt_until_valid(
        "开始预约的时间 HH:MM [默认 12:00]：", _target_time
    )

    return BookingPlan(
        booking_date=str(booking_date),
        time_slots=tuple(TIME_SLOTS[number - 1] for number in slot_numbers),
        courts=tuple(COURTS[number - 1] for number in court_numbers),
        target_hour=target_hour,
        target_minute=target_minute,
    )


def describe_plan(plan: BookingPlan) -> None:
    print("\n预约计划")
    print(f"  日期：{plan.booking_date}")
    print(f"  时间段：{', '.join(plan.time_slots)}")
    print(f"  场地：{', '.join(court.name for court in plan.courts)}")
    print(f"  触发时间：{plan.target_hour:02d}:{plan.target_minute:02d}")
    print(f"  任务数：{len(plan.time_slots) * len(plan.courts)}")


def _credentials(settings: Settings) -> Tuple[str, str]:
    username = settings.username
    while not username:
        username = input("学号：").strip()
        if not username:
            print("学号不能为空。")

    password = settings.password
    while not password:
        password = getpass("密码（输入不会回显）：")
        if not password:
            print("密码不能为空。")
    return username, password


def wait_for_target(plan: BookingPlan) -> None:
    now = datetime.now()
    target = now.replace(
        hour=plan.target_hour,
        minute=plan.target_minute,
        second=0,
        microsecond=0,
    )
    if target <= now:
        target += timedelta(days=1)
    LOGGER.info(
        "等待至 %s 开始预约；按 Ctrl+C 可取消",
        target.strftime("%Y-%m-%d %H:%M"),
    )
    while True:
        remaining = (target - datetime.now()).total_seconds()
        if remaining <= 0:
            return
        time.sleep(min(1.0, remaining))


def _safe_server_message(result: dict) -> str:
    for key in ("message", "msg"):
        value = result.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()[:160]
    return "服务器未返回成功状态"


def run_plan(plan: BookingPlan, settings: Settings, username: str, password: str) -> int:
    pending = build_tasks(plan)
    successful: List[BookingTask] = []
    failed: List[BookingTask] = []
    request_attempts = 0

    with BookingClient(settings) as client:
        LOGGER.info("正在登录南昌大学统一身份认证系统")
        client.login(username, password)

        while pending:
            for task in list(pending):
                if task.attempts >= settings.max_attempts:
                    pending.remove(task)
                    failed.append(task)
                    continue

                if request_attempts and request_attempts % settings.token_refresh_interval == 0:
                    LOGGER.info("刷新登录会话")
                    client.login(username, password)

                task.attempts += 1
                request_attempts += 1
                LOGGER.info(
                    "尝试预约 %s（第 %d/%d 次）",
                    task.label,
                    task.attempts,
                    settings.max_attempts,
                )
                try:
                    result = client.reserve(task)
                    if str(result.get("code")) == "200":
                        task.succeeded = True
                        task.last_message = _safe_server_message(result)
                        pending.remove(task)
                        successful.append(task)
                        LOGGER.info("预约成功：%s", task.label)
                        continue
                    task.last_message = _safe_server_message(result)
                    LOGGER.warning("预约未成功：%s — %s", task.label, task.last_message)
                except BookingError as exc:
                    task.last_message = str(exc)
                    LOGGER.warning("预约未成功：%s — %s", task.label, exc)

                if task.attempts >= settings.max_attempts:
                    pending.remove(task)
                    failed.append(task)
                else:
                    time.sleep(settings.retry_delay)

    print("\n预约结果")
    print(f"  成功：{len(successful)}")
    print(f"  失败：{len(failed)}")
    for task in failed:
        print(f"  - {task.label}：{task.last_message or '达到最大尝试次数'}")
    return 0 if not failed else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="南昌大学羽毛球场地预约命令行工具")
    parser.add_argument("--config", help="INI 配置文件路径；默认读取 ./config.ini")
    parser.add_argument(
        "--run-now", action="store_true", help="确认计划后立即运行，不等待触发时间"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="只生成计划，不登录或发送网络请求"
    )
    parser.add_argument(
        "--debug", action="store_true", help="显示调试日志（不会输出密码或 Token）"
    )
    return parser


def _configure_logging(debug: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        settings = load_settings(args.config)
    except (OSError, ValueError) as exc:
        print(f"配置错误：{exc}")
        return 2
    if args.debug and not settings.debug:
        settings = Settings(
            username=settings.username,
            password=settings.password,
            debug=True,
            request_timeout=settings.request_timeout,
            max_attempts=settings.max_attempts,
            retry_delay=settings.retry_delay,
            token_refresh_interval=settings.token_refresh_interval,
        )
    _configure_logging(settings.debug)

    print("NCU 羽毛球场地预约助手")
    print("请遵守学校预约规则；本工具不保证预约成功。")
    try:
        plan = collect_plan()
        describe_plan(plan)
        if args.dry_run:
            print("\n演练完成：未读取账号、未登录、未发送网络请求。")
            return 0
        username, password = _credentials(settings)
        if not args.run_now:
            wait_for_target(plan)
        return run_plan(plan, settings, username, password)
    except KeyboardInterrupt:
        print("\n已取消。")
        return 130
    except BookingError as exc:
        LOGGER.error("%s", exc)
        return 1
