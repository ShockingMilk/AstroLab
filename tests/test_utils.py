"""Tests for common utility functions."""

import unittest

from astro_assist.common.utils import (
    clamp,
    format_bytes,
    sanitize_filename,
    switch,
)


class TestUtils(unittest.TestCase):
    """Test shared utility behavior."""

    def test_clamp(self) -> None:
        self.assertEqual(clamp(5, 0, 10), 5)
        self.assertEqual(clamp(-1, 0, 10), 0)
        self.assertEqual(clamp(11, 0, 10), 10)

    def test_format_bytes(self) -> None:
        self.assertEqual(format_bytes(1024), "1.0 KB")

    def test_sanitize_filename(self) -> None:
        self.assertEqual(
            sanitize_filename("Jupiter / Test!"),
            "Jupiter_Test",
        )

    def test_switch_literal(self) -> None:
        result = switch(
            "start",
            {"start": "running", "stop": "stopped"},
            default="unknown",
        )
        self.assertEqual(result, "running")

    def test_switch_callable(self) -> None:
        result = switch(
            5,
            {5: lambda value: value * 2},
        )
        self.assertEqual(result, 10)

    def test_switch_default(self) -> None:
        result = switch(
            "other",
            {"start": "running"},
            default="unknown",
        )
        self.assertEqual(result, "unknown")


if __name__ == "__main__":
    unittest.main()