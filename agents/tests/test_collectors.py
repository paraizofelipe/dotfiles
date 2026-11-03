import io
import json
import os
import sys
import tempfile
import unittest
import urllib.error
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents_usage import common  # noqa: E402
from agents_usage.collectors import claude, codex, openrouter  # noqa: E402

NOW = 1_800_000_000.0


def http_error(code):
    return urllib.error.HTTPError("https://x", code, "err", {}, io.BytesIO(b""))  # type: ignore[arg-type]


def raising(exc):
    def fetch(_url, _headers):
        raise exc
    return fetch


def returning(payload, calls=None):
    def fetch(url, headers):
        if calls is not None:
            calls.append((url, headers))
        return payload
    return fetch


class HomeMixin:
    def make_home(self, filename=None, content=None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)  # type: ignore[attr-defined]
        if filename:
            with open(os.path.join(tmp.name, filename), "w", encoding="utf-8") as f:
                json.dump(content, f)
        return {"provider": "x", "id": "main", "home": tmp.name}


class TestPace(unittest.TestCase):
    def limit(self, percent, remaining, window=common.SESSION_WINDOW):
        return common.make_limit("session", "5h", percent, NOW + remaining, window)

    def test_should_be_one_when_usage_matches_elapsed_time(self):
        self.assertAlmostEqual(common.pace(self.limit(50, common.SESSION_WINDOW / 2), NOW), 1.0)

    def test_should_be_none_at_window_start_to_avoid_noise(self):
        self.assertIsNone(common.pace(self.limit(3, common.SESSION_WINDOW - 60), NOW))

    def test_should_be_none_without_reset_time(self):
        self.assertIsNone(common.pace(common.make_limit("s", "5h", 40, None, 3600), NOW))

    def test_should_flag_high_when_burning_fast_mid_window(self):
        # 60% usado com só 30% da janela decorrida: esgota antes do reset
        lim = self.limit(60, common.SESSION_WINDOW * 0.7)
        self.assertEqual(common.severity(lim, NOW), "high")

    def test_should_stay_low_when_usage_is_behind_pace(self):
        lim = self.limit(20, common.SESSION_WINDOW * 0.2)
        self.assertEqual(common.severity(lim, NOW), "low")

    def test_should_flag_high_at_absolute_ninety_percent_regardless_of_pace(self):
        lim = self.limit(91, 60)
        self.assertEqual(common.severity(lim, NOW), "high")


class TestToEpoch(unittest.TestCase):
    def test_should_convert_milliseconds_to_seconds(self):
        self.assertEqual(common.to_epoch(1_800_000_000_000), 1_800_000_000.0)

    def test_should_parse_iso_with_z_suffix(self):
        expected = datetime(2027, 1, 15, 8, tzinfo=timezone.utc).timestamp()
        self.assertEqual(common.to_epoch("2027-01-15T08:00:00Z"), expected)

    def test_should_treat_naive_iso_as_utc(self):
        self.assertEqual(common.to_epoch("2027-01-15T08:00:00"),
                         common.to_epoch("2027-01-15T08:00:00Z"))

    def test_should_return_none_for_garbage(self):
        self.assertIsNone(common.to_epoch("not-a-date"))
        self.assertIsNone(common.to_epoch(None))


class TestEnv(unittest.TestCase):
    def test_should_read_exported_quoted_value_from_env_file(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write('FOO=1\nexport OPENROUTER_TEST_KEY="sk-abc"\n')
        self.addCleanup(os.unlink, f.name)
        self.assertEqual(common.env_var("OPENROUTER_TEST_KEY", [f.name]), "sk-abc")

    def test_should_return_none_when_missing_everywhere(self):
        self.assertIsNone(common.env_var("DEFINITELY_NOT_SET_VAR", ["/nonexistent"]))


class TestClaude(HomeMixin, unittest.TestCase):
    CREDS = {"claudeAiOauth": {"accessToken": "tok", "expiresAt": (NOW + 3600) * 1000,
                               "subscriptionType": "max"}}
    PAYLOAD = {"five_hour": {"utilization": 42.0, "resets_at": "2027-01-15T10:00:00Z"},
               "seven_day": {"utilization": 12.5, "resets_at": "2027-01-20T10:00:00Z"},
               "seven_day_opus": None}

    def test_should_return_session_and_weekly_limits_with_plan(self):
        calls = []
        res = claude.collect(self.make_home(".credentials.json", self.CREDS), now=NOW,
                             fetch=returning(self.PAYLOAD, calls))
        self.assertEqual(res["status"], common.OK)
        self.assertEqual(res["plan"], "max")
        self.assertEqual([lim["id"] for lim in res["limits"]], ["session", "weekly"])
        self.assertEqual(res["limits"][0]["percent"], 42.0)
        self.assertEqual(res["limits"][1]["window_seconds"], common.WEEKLY_WINDOW)
        self.assertEqual(calls[0][1]["Authorization"], "Bearer tok")

    def test_should_require_signin_when_credentials_file_is_missing(self):
        res = claude.collect(self.make_home(), now=NOW, fetch=raising(AssertionError("no call")))
        self.assertEqual(res["status"], common.SIGNIN_REQUIRED)

    def test_should_require_signin_without_calling_api_when_token_expired(self):
        creds = {"claudeAiOauth": {**self.CREDS["claudeAiOauth"], "expiresAt": (NOW - 1) * 1000}}
        res = claude.collect(self.make_home(".credentials.json", creds), now=NOW,
                             fetch=raising(AssertionError("no call")))
        self.assertEqual(res["status"], common.SIGNIN_REQUIRED)
        self.assertEqual(res["plan"], "max")

    def test_should_require_signin_on_401(self):
        res = claude.collect(self.make_home(".credentials.json", self.CREDS), now=NOW,
                             fetch=raising(http_error(401)))
        self.assertEqual(res["status"], common.SIGNIN_REQUIRED)

    def test_should_report_error_on_5xx(self):
        res = claude.collect(self.make_home(".credentials.json", self.CREDS), now=NOW,
                             fetch=raising(http_error(503)))
        self.assertEqual((res["status"], res["error"]), (common.ERROR, "HTTP 503"))

    def test_should_report_offline_on_network_failure(self):
        res = claude.collect(self.make_home(".credentials.json", self.CREDS), now=NOW,
                             fetch=raising(urllib.error.URLError("dns")))
        self.assertEqual(res["status"], common.OFFLINE)

    def test_should_return_empty_limits_for_empty_payload(self):
        self.assertEqual(claude.parse_usage({}), [])

    FABLE = {"kind": "weekly_scoped", "group": "weekly", "percent": 37,
             "resets_at": "2027-01-20T10:00:00+00:00",
             "scope": {"model": {"id": None, "display_name": "Fable"}, "surface": None}}

    def test_should_add_model_scoped_weekly_limit_after_base_windows(self):
        payload = {**self.PAYLOAD, "limits": [
            {"kind": "session", "percent": 42}, {"kind": "weekly_all", "percent": 12.5}, self.FABLE]}
        limits = claude.parse_usage(payload)
        self.assertEqual([lim["id"] for lim in limits], ["session", "weekly", "weekly_fable"])
        fable = limits[2]
        self.assertEqual((fable["label"], fable["percent"], fable["window_seconds"]),
                         ("Fable", 37.0, common.WEEKLY_WINDOW))
        self.assertEqual(fable["resets_at"], common.to_epoch("2027-01-20T10:00:00Z"))

    def test_should_label_scope_without_model_by_surface_or_generic_name(self):
        by_surface = {**self.FABLE, "scope": {"model": None, "surface": {"display_name": "Cowork"}}}
        nameless = {**self.FABLE, "scope": None}
        labels = [lim["label"] for lim in claude.parse_scoped_limits([by_surface, nameless])]
        self.assertEqual(labels, ["Cowork", "Escopo"])

    def test_should_ignore_malformed_scoped_items(self):
        items = [None, "x", {"kind": "weekly_scoped"}, {**self.FABLE, "percent": "37"},
                 {**self.FABLE, "kind": "session"}]
        self.assertEqual(claude.parse_scoped_limits(items), [])

    def test_should_keep_base_windows_when_limits_field_is_missing_or_not_a_list(self):
        for value in (None, {}, "oops"):
            limits = claude.parse_usage({**self.PAYLOAD, "limits": value})
            self.assertEqual([lim["id"] for lim in limits], ["session", "weekly"])

    def test_should_never_write_to_credentials_file(self):
        account = self.make_home(".credentials.json", self.CREDS)
        path = os.path.join(account["home"], ".credentials.json")
        before = os.stat(path).st_mtime_ns
        claude.collect(account, now=NOW, fetch=raising(http_error(401)))
        self.assertEqual(os.stat(path).st_mtime_ns, before)


class TestCodex(HomeMixin, unittest.TestCase):
    AUTH = {"tokens": {"access_token": "tok", "account_id": "acc-1"}}
    PAYLOAD = {"plan_type": "plus", "rate_limit": {
        "primary_window": {"used_percent": 30, "reset_at": NOW + 600, "limit_window_seconds": 18000},
        "secondary_window": {"used_percent": 70, "reset_at": NOW + 86400}}}

    def test_should_parse_windows_and_send_account_header(self):
        calls = []
        res = codex.collect(self.make_home("auth.json", self.AUTH), fetch=returning(self.PAYLOAD, calls))
        self.assertEqual(res["status"], common.OK)
        self.assertEqual(res["plan"], "plus")
        self.assertEqual([lim["percent"] for lim in res["limits"]], [30.0, 70.0])
        self.assertEqual(res["limits"][1]["window_seconds"], common.WEEKLY_WINDOW)
        self.assertEqual(calls[0][1]["ChatGPT-Account-Id"], "acc-1")

    def test_should_expose_credit_balance_when_plan_has_no_windows(self):
        parsed = codex.parse_usage({"credits": {"has_credits": True, "balance": "12.5"}})
        self.assertEqual(parsed["limits"], [])
        self.assertEqual(parsed["balance"]["remaining"], 12.5)

    def test_should_ignore_non_numeric_credit_balance(self):
        parsed = codex.parse_usage({"credits": {"has_credits": True, "balance": "n/a"}})
        self.assertIsNone(parsed["balance"])

    def test_should_require_signin_without_auth_file(self):
        self.assertEqual(codex.collect(self.make_home())["status"], common.SIGNIN_REQUIRED)

    def test_should_require_signin_on_403(self):
        res = codex.collect(self.make_home("auth.json", self.AUTH), fetch=raising(http_error(403)))
        self.assertEqual(res["status"], common.SIGNIN_REQUIRED)


class TestOpenRouter(unittest.TestCase):
    def test_should_compute_remaining_balance(self):
        res = openrouter.collect({}, key="k", fetch=returning(
            {"data": {"total_credits": 20, "total_usage": 7.25}}))
        self.assertEqual(res["balance"], {"remaining": 12.75, "total": 20.0, "currency": "USD"})

    def test_should_be_not_configured_without_key(self):
        os.environ.pop("OPENROUTER_API_KEY", None)
        original = common.ENV_FILES
        common.ENV_FILES = []
        self.addCleanup(setattr, common, "ENV_FILES", original)
        self.assertEqual(openrouter.collect({})["status"], common.NOT_CONFIGURED)

    def test_should_flag_invalid_key_on_401(self):
        res = openrouter.collect({}, key="k", fetch=raising(http_error(401)))
        self.assertEqual(res["status"], common.SIGNIN_REQUIRED)


if __name__ == "__main__":
    unittest.main()
