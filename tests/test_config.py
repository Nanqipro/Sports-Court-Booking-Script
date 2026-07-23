import tempfile
import unittest
from pathlib import Path

from ncu_booking.config import load_settings, parse_bool


class ConfigTests(unittest.TestCase):
    def test_parse_bool(self) -> None:
        self.assertTrue(parse_bool("yes"))
        self.assertFalse(parse_bool("0"))
        with self.assertRaises(ValueError):
            parse_bool("maybe")

    def test_environment_takes_precedence_and_password_repr_is_safe(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.ini"
            path.write_text(
                "[CONFIG]\nBADMINTON_USERNAME = from-file\n"
                "BADMINTON_PASSWORD = file-password\nDEBUG = false\n",
                encoding="utf-8",
            )
            settings = load_settings(
                path,
                {
                    "BADMINTON_USERNAME": "from-env",
                    "BADMINTON_PASSWORD": "env-password",
                },
            )
        self.assertEqual(settings.username, "from-env")
        self.assertEqual(settings.password, "env-password")
        self.assertNotIn("env-password", repr(settings))


if __name__ == "__main__":
    unittest.main()

