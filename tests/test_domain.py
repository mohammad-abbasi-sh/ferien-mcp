"""Offline tests — domain logic against recorded ferien-api.de fixtures.

Run:  pytest tests/test_domain.py -v
"""
import pathlib
import sys
import unittest
from datetime import date

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from ferien_mcp import domain as dom  # noqa: E402

FIX = pathlib.Path(__file__).resolve().parent / "fixtures"


def _read(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


class TestValidation(unittest.TestCase):
    def test_year_ok(self):
        self.assertEqual(dom.validate_year(2026), 2026)
        self.assertEqual(dom.validate_year("2030"), 2030)
        self.assertEqual(dom.validate_year(None), date.today().year)

    def test_year_bad(self):
        for bad in (1999, 2101, "soon"):
            with self.assertRaises(ValueError, msg=str(bad)):
                dom.validate_year(bad)

    def test_state_ok(self):
        self.assertEqual(dom.validate_state("BY"), "BY")
        self.assertEqual(dom.validate_state("by"), "BY")
        self.assertEqual(dom.validate_state("  nw "), "NW")

    def test_state_bad(self):
        for bad in ("", "XX", "DE", "Berlin", "B", "NATIONAL", None):
            with self.assertRaises(ValueError, msg=str(bad)):
                dom.validate_state(bad)

    def test_date_ok(self):
        self.assertEqual(dom.validate_date("2026-08-03"), date(2026, 8, 3))
        self.assertEqual(dom.validate_date(" 2026-01-01 "), date(2026, 1, 1))

    def test_date_bad(self):
        for bad in ("", "2026-13-01", "2026-02-30", "03.08.2026",
                    "2026/08/03", "20260803"):
            with self.assertRaises(ValueError, msg=bad):
                dom.validate_date(bad)

    def test_month_ok(self):
        self.assertIsNone(dom.validate_month(None))
        self.assertEqual(dom.validate_month(8), 8)
        self.assertEqual(dom.validate_month("3"), 3)

    def test_month_bad(self):
        for bad in (0, 13, "soon"):
            with self.assertRaises(ValueError, msg=str(bad)):
                dom.validate_month(bad)


class TestUrls(unittest.TestCase):
    def test_holidays_url(self):
        self.assertEqual(dom.holidays_url(2026, "BY"),
                         "https://ferien-api.de/api/v1/holidays/BY/2026")
        self.assertEqual(dom.holidays_url(2026, "be"),
                         "https://ferien-api.de/api/v1/holidays/BE/2026")

    def test_holidays_url_bad(self):
        with self.assertRaises(ValueError):
            dom.holidays_url(1999, "BY")
        with self.assertRaises(ValueError):
            dom.holidays_url(2026, "XX")


class TestKind(unittest.TestCase):
    def test_kinds(self):
        self.assertEqual(dom.derive_kind("sommerferien bayern 2026"),
                         "sommerferien")
        self.assertEqual(dom.derive_kind("frühjahrsferien bayern 2026"),
                         "frühjahrsferien")
        self.assertEqual(
            dom.derive_kind("herbstferien bayern 2026 (beweglicher ferientag)"),
            "beweglicher ferientag")
        self.assertEqual(dom.derive_kind("weihnachtsferien berlin 2025"),
                         "weihnachtsferien")
        self.assertIsNone(dom.derive_kind("unterrichtsfreier tag"))


class TestParse(unittest.TestCase):
    def test_parse_by_2026(self):
        rows = dom.parse_holidays(_read("holidays-2026-by.json"))
        self.assertEqual(len(rows), 6)
        names = [r["name"] for r in rows]
        self.assertIn("sommerferien bayern 2026", names)
        sommer = next(r for r in rows if r["kind"] == "sommerferien")
        self.assertEqual(sommer["start"], "2026-08-03")
        self.assertEqual(sommer["end"], "2026-09-15")
        self.assertEqual(sommer["duration_days"], 44)
        self.assertEqual(sommer["start_weekday"], "Monday")
        self.assertEqual(sommer["start_weekday_de"], "Montag")
        self.assertEqual(sommer["end_weekday"], "Tuesday")
        self.assertEqual(sommer["state"], "BY")
        self.assertEqual(sommer["year"], 2026)
        # sorted by start
        self.assertEqual([r["start"] for r in rows],
                         sorted(r["start"] for r in rows))
        # single-day movable day
        beweglich = next(r for r in rows
                         if r["kind"] == "beweglicher ferientag")
        self.assertEqual(beweglich["duration_days"], 2)
        self.assertEqual(beweglich["start"], "2026-11-18")

    def test_parse_nw_2026(self):
        rows = dom.parse_holidays(_read("holidays-2026-nw.json"))
        self.assertEqual(len(rows), 5)
        # cross-year Weihnachtsferien
        weihnachten = next(r for r in rows if r["kind"] == "weihnachtsferien")
        self.assertEqual(weihnachten["start"], "2026-12-23")
        self.assertEqual(weihnachten["end"], "2027-01-06")
        self.assertEqual(weihnachten["duration_days"], 15)
        # single-day Pfingstferien
        pfingsten = next(r for r in rows if r["kind"] == "pfingstferien")
        self.assertEqual(pfingsten["duration_days"], 1)

    def test_parse_empty_is_valid(self):
        # BE/2026 and BY/2030: the API returns [] for state/years
        # it has no data for — not an error.
        self.assertEqual(dom.parse_holidays(_read("holidays-2026-be.json")), [])
        self.assertEqual(dom.parse_holidays(_read("holidays-2030-by.json")), [])

    def test_parse_be_2025(self):
        rows = dom.parse_holidays(_read("holidays-2025-be.json"))
        self.assertEqual(len(rows), 7)
        winter = rows[0]
        self.assertEqual(winter["kind"], "winterferien")
        self.assertEqual(winter["start"], "2025-02-03")

    def test_parse_bad(self):
        with self.assertRaises(ValueError):
            dom.parse_holidays("not json")
        with self.assertRaises(ValueError):
            dom.parse_holidays('{"not": "a list"}')
        with self.assertRaises(ValueError):
            dom.parse_holidays('[{"start": "2026-01-01"}]')


class TestFilters(unittest.TestCase):
    def setUp(self):
        self.rows = dom.parse_holidays(_read("holidays-2026-by.json"))

    def test_holidays_in_month(self):
        self.assertEqual(len(dom.holidays_in_month(self.rows, 8)), 1)
        self.assertEqual(dom.holidays_in_month(self.rows, 8)[0]["kind"],
                         "sommerferien")
        # November holds Herbstferien + the movable day
        self.assertEqual(len(dom.holidays_in_month(self.rows, 11)), 2)
        self.assertEqual(len(dom.holidays_in_month(self.rows, 1)), 0)
        self.assertEqual(len(dom.holidays_in_month(self.rows, None)), 6)

    def test_is_holiday(self):
        hit = dom.is_holiday(self.rows, date(2026, 8, 10))
        self.assertEqual(len(hit), 1)
        self.assertEqual(hit[0]["kind"], "sommerferien")
        self.assertEqual(dom.is_holiday(self.rows, date(2026, 8, 3)),
                         dom.is_holiday(self.rows, date(2026, 9, 15)))
        self.assertEqual(dom.is_holiday(self.rows, date(2026, 1, 15)), [])
        self.assertEqual(dom.is_holiday(self.rows, date(2026, 5, 1)), [])

    def test_next_holiday(self):
        nxt = dom.next_holiday(self.rows, date(2026, 1, 1))
        self.assertEqual(nxt["kind"], "frühjahrsferien")
        self.assertFalse(nxt["ongoing"])
        # inside Sommerferien -> the ongoing holiday itself
        ongoing = dom.next_holiday(self.rows, date(2026, 8, 10))
        self.assertEqual(ongoing["kind"], "sommerferien")
        self.assertTrue(ongoing["ongoing"])
        # after the last 2026 entry -> None (server looks at next year)
        self.assertIsNone(dom.next_holiday(self.rows, date(2026, 11, 20)))

    def test_holidays_between(self):
        rows_by_year = {2026: self.rows}
        out = dom.holidays_between(rows_by_year, date(2026, 3, 30),
                                   date(2026, 4, 11))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "osterferien")
        # cross-year: NW Weihnachtsferien 2026/27 overlaps Jan 2027
        nw = dom.parse_holidays(_read("holidays-2026-nw.json"))
        out2 = dom.holidays_between({2026: nw}, date(2027, 1, 2),
                                    date(2027, 1, 5))
        self.assertEqual(len(out2), 1)
        self.assertEqual(out2[0]["kind"], "weihnachtsferien")
        # empty range, reversed range, too-wide range
        self.assertEqual(dom.holidays_between(rows_by_year, date(2026, 1, 5),
                                              date(2026, 1, 6)), [])
        with self.assertRaises(ValueError):
            dom.holidays_between(rows_by_year, date(2026, 4, 11),
                                 date(2026, 3, 30))
        with self.assertRaises(ValueError):
            dom.holidays_between(rows_by_year, date(2026, 1, 1),
                                 date(2028, 1, 3))


class TestStates(unittest.TestCase):
    def test_list_states(self):
        states = dom.list_states()
        self.assertEqual(len(states), 16)
        codes = [s["code"] for s in states]
        self.assertIn("BY", codes)
        self.assertIn("BE", codes)
        self.assertNotIn("NATIONAL", codes)
        self.assertNotIn("DE", codes)


if __name__ == "__main__":
    unittest.main()
