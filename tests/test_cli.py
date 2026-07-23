import unittest

from ncu_booking.cli import COURTS, TIME_SLOTS, build_tasks, parse_number_choices
from ncu_booking.models import BookingPlan


class CliTests(unittest.TestCase):
    def test_parse_choices_accepts_chinese_comma_and_deduplicates(self) -> None:
        self.assertEqual(parse_number_choices("1，2,2", 1, 3, 1), [1, 2])

    def test_parse_choices_uses_default(self) -> None:
        self.assertEqual(parse_number_choices("", 1, 12, 7), [7])

    def test_build_tasks_uses_cartesian_product(self) -> None:
        plan = BookingPlan(
            booking_date="2026-07-24",
            time_slots=(TIME_SLOTS[0], TIME_SLOTS[1]),
            courts=(COURTS[0], COURTS[1]),
            target_hour=12,
            target_minute=0,
        )
        tasks = build_tasks(plan)
        self.assertEqual(len(tasks), 4)
        self.assertEqual(tasks[0].label, "羽毛球1号场地 08:00-09:00")
        self.assertEqual(tasks[-1].label, "羽毛球2号场地 09:00-10:00")


if __name__ == "__main__":
    unittest.main()

