"""Domain models shared by the CLI and booking client."""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class Court:
    """A court name and the identifier expected by the booking API."""

    number: int
    name: str
    nickname: str


@dataclass(frozen=True)
class BookingPlan:
    """The user's booking choices before network requests begin."""

    booking_date: str
    time_slots: Tuple[str, ...]
    courts: Tuple[Court, ...]
    target_hour: int
    target_minute: int


@dataclass
class BookingTask:
    """A single court/time combination and its retry state."""

    booking_date: str
    time_slot: str
    court: Court
    attempts: int = 0
    succeeded: bool = False
    last_message: str = ""

    @property
    def label(self) -> str:
        return f"{self.court.name} {self.time_slot}"

