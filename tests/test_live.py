"""Live tests — hit the real ferien-api.de API. Cautious: few requests.

Run:  pytest tests/test_live.py -v
Skip: pytest -m "not live"  (or set FERIEN_SKIP_LIVE=1)
"""
import json
import os
import pathlib
import sys
import unittest

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from ferien_mcp import server as srv  # noqa: E402

pytestmark = pytest.mark.live
SKIP = os.environ.get("FERIEN_SKIP_LIVE") == "1"


@pytest.mark.skipif(SKIP, reason="FERIEN_SKIP_LIVE=1")
class TestLive(unittest.TestCase):
    def test_list_holidays_live(self):
        out = json.loads(srv.ferien_list_holidays(2026, "BY"))
        self.assertNotIn("error", out)
        self.assertEqual(out["count"], 6)
        names = [h["name"] for h in out["holidays"]]
        self.assertIn("sommerferien bayern 2026", names)
        sommer = next(h for h in out["holidays"]
                      if h["kind"] == "sommerferien")
        self.assertEqual(sommer["start"], "2026-08-03")
        self.assertEqual(sommer["end"], "2026-09-15")
        self.assertEqual(sommer["duration_days"], 44)
        print("\nLIVE 2026 BY: 6 holidays")

    def test_list_holidays_month_live(self):
        out = json.loads(srv.ferien_list_holidays(2026, "BY", month=8))
        self.assertNotIn("error", out)
        self.assertEqual(out["count"], 1)
        self.assertEqual(out["holidays"][0]["kind"], "sommerferien")
        print("\nLIVE 2026 BY August: Sommerferien only")

    def test_empty_coverage_live(self):
        # Berlin 2026: the API returns [] (verified 2026-11-14) — a
        # coverage gap, not an error.
        out = json.loads(srv.ferien_list_holidays(2026, "BE"))
        self.assertNotIn("error", out)
        self.assertEqual(out["count"], 0)
        self.assertIn("coverage_note", out)
        print("\nLIVE 2026 BE: empty (API has no data for Berlin 2026)")

    def test_is_holiday_live(self):
        out = json.loads(srv.ferien_is_holiday("2026-04-02", "BY"))
        self.assertNotIn("error", out)
        self.assertTrue(out["is_holiday"])
        self.assertEqual(out["holidays"], ["osterferien bayern 2026"])
        self.assertEqual(out["weekday"], "Thursday")
        out2 = json.loads(srv.ferien_is_holiday("2026-01-15", "BY"))
        self.assertFalse(out2["is_holiday"])
        self.assertEqual(out2["holidays"], [])
        print("\nLIVE is_holiday: 2026-04-02 yes (Osterferien), 2026-01-15 no")

    def test_next_holiday_live(self):
        out = json.loads(srv.ferien_next_holiday("2026-01-01", "BY"))
        self.assertNotIn("error", out)
        self.assertEqual(out["next_holiday"]["kind"], "frühjahrsferien")
        self.assertEqual(out["next_holiday"]["start"], "2026-02-16")
        self.assertFalse(out["next_holiday"]["ongoing"])
        # inside Sommerferien -> the ongoing holiday itself
        out2 = json.loads(srv.ferien_next_holiday("2026-08-10", "BY"))
        self.assertEqual(out2["next_holiday"]["kind"], "sommerferien")
        self.assertTrue(out2["next_holiday"]["ongoing"])
        print("\nLIVE next_holiday: 2026-01-01 -> Frühjahrsferien; "
              "2026-08-10 -> ongoing Sommerferien")

    def test_holidays_between_live(self):
        out = json.loads(srv.ferien_holidays_between(
            "2026-03-30", "2026-04-11", "BY"))
        self.assertNotIn("error", out)
        self.assertEqual(out["count"], 1)
        self.assertEqual(out["holidays"][0]["kind"], "osterferien")
        print("\nLIVE between 2026-03-30..2026-04-11 BY: Osterferien only")

    def test_list_states_live(self):
        out = json.loads(srv.ferien_list_states())
        self.assertEqual(out["count"], 16)
        codes = [s["code"] for s in out["states"]]
        self.assertIn("BY", codes)
        self.assertIn("BE", codes)
        print("\nLIVE states: 16")

    def test_bad_state_live(self):
        out = json.loads(srv.ferien_list_holidays(2026, "XX"))
        self.assertIn("error", out)
        self.assertIn("unknown state", out["error"])

    def test_health_live(self):
        out = json.loads(srv.ferien_health())
        self.assertEqual(out["status"], "ok")
        self.assertEqual(out["http_status"], 200)
        print(f"\nLIVE health: {out['status']} {out['http_status']}")


if __name__ == "__main__":
    unittest.main()
