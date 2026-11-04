import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents_usage import accounts, common, view  # noqa: E402

NOW = 1_800_000_000.0
HOUR = 3600


def registry(active="main"):
    reg = accounts.load_registry("/nonexistent/accounts.json")
    reg["claude"]["accounts"].append({"id": "work", "label": "Work", "home": "/w"})
    reg["claude"]["active"] = active
    return reg


def rec(provider, account, percent=10, status=common.OK, **extra):
    return {"provider": provider, "provider_name": provider.title(), "account": account,
            "status": status, "stale": False, "updated_at": NOW, "plan": "max",
            "limits": [common.make_limit("session", "5h", percent, NOW + 2 * HOUR,
                                         common.SESSION_WINDOW)], "balance": None, **extra}


class TestFormatting(unittest.TestCase):
    def test_should_humanize_tokens_in_pt_br(self):
        self.assertEqual([view.human_tokens(n) for n in (950, 1_500, 97_730_356, 2_000_000_000)],
                         ["950", "1,5k", "97,7M", "2B"])

    def test_should_format_money_with_brazilian_separators(self):
        self.assertEqual(view.money(1234.5), "US$ 1.234,50")
        self.assertEqual(view.money(None), "?")

    def test_should_format_durations(self):
        self.assertEqual([view.duration(s) for s in (59, 600, 2 * HOUR + 5 * 60, 26 * HOUR, -5)],
                         ["0m", "10m", "2h 05m", "1d 2h", "0m"])


class TestBuild(unittest.TestCase):
    def test_should_list_registered_accounts_even_without_records(self):
        model = view.build({"accounts": [rec("claude", "main")], "updated_at": NOW}, registry(), NOW)
        claude = model["providers"][0]
        self.assertEqual([a["label"] for a in claude["accounts"]], ["Main", "Work"])
        self.assertEqual(claude["accounts"][1]["status_text"], "Aguardando atualização")

    def test_should_mark_active_account_from_registry(self):
        model = view.build({"accounts": []}, registry(active="work"), NOW)
        self.assertEqual([a["active"] for a in model["providers"][0]["accounts"]], [False, True])

    def test_should_assign_global_keyboard_keys_across_providers(self):
        model = view.build({"accounts": []}, registry(), NOW)
        keys = [a["key"] for p in model["providers"] for a in p["accounts"]]
        self.assertEqual(keys, [1, 2, 3])

    def test_should_flag_signin_required(self):
        usage = {"accounts": [rec("claude", "main", status=common.SIGNIN_REQUIRED, limits=[])]}
        acc = view.build(usage, registry(), NOW)["providers"][0]["accounts"][0]
        self.assertTrue(acc["needs_signin"])
        self.assertEqual(acc["status_text"], "Sign-in required")

    def test_should_explain_stale_numbers(self):
        usage = {"accounts": [rec("claude", "main", status=common.OFFLINE, stale=True,
                                  updated_at=NOW - 20 * 60)]}
        acc = view.build(usage, registry(), NOW)["providers"][0]["accounts"][0]
        self.assertEqual(acc["status_text"], "Sem conexão · últimos dados há 20m")
        self.assertEqual(len(acc["meters"]), 1)

    def test_should_hide_openrouter_when_not_configured(self):
        usage = {"accounts": [rec("openrouter", "main", status=common.NOT_CONFIGURED, limits=[])]}
        self.assertEqual([p["id"] for p in view.build(usage, registry(), NOW)["providers"]],
                         ["claude", "codex"])

    def test_should_show_openrouter_balance_fraction(self):
        usage = {"accounts": [rec("openrouter", "main", limits=[],
                                  balance={"remaining": 25, "total": 100, "currency": "USD"})]}
        acc = view.build(usage, registry(), NOW)["providers"][2]["accounts"][0]
        self.assertEqual(acc["balance"], {"text": "US$ 25,00 de US$ 100,00", "fraction": 0.25})
        self.assertEqual((acc["plan"], acc["key"]), ("", 0))

    def test_should_flag_outdated_usage_file(self):
        self.assertTrue(view.build({"updated_at": NOW - 31 * 60}, registry(), NOW)["outdated"])
        self.assertTrue(view.build({}, registry(), NOW)["outdated"])
        self.assertFalse(view.build({"updated_at": NOW - 60}, registry(), NOW)["outdated"])

    def test_should_show_empty_ticker_message_without_usage(self):
        self.assertEqual(view.build({}, registry(), NOW)["ticker"],
                         ["Sem uso registrado nos últimos 7 dias"])

    def test_should_merge_models_across_providers_in_ticker(self):
        tokens = {"claude": {"week": {"total": 3_000_000}, "by_model": {"opus": 3_000_000}, "by_day": {}},
                  "codex": {"week": {"total": 500}, "by_model": {"gpt": 500}, "by_day": {}}}
        lines = view.build({"tokens": tokens}, registry(), NOW)["ticker"]
        self.assertIn("3M tokens nos últimos 7 dias", lines)
        self.assertIn("Modelo mais usado: opus (3M)", lines)


class TestWorst(unittest.TestCase):
    def test_should_ignore_inactive_accounts(self):
        records = [rec("claude", "main", 10), rec("claude", "work", 99)]
        self.assertEqual(view.worst(records, registry())["percent"], 10)

    def test_should_pick_highest_severity(self):
        records = [rec("claude", "main", 30), rec("codex", "main", 92)]
        worst = view.worst(records, registry())
        self.assertEqual((worst["percent"], worst["severity"]), (92, "high"))

    def test_should_name_provider_of_worst_limit_for_bar_glyph(self):
        records = [rec("claude", "main", 92), rec("codex", "main", 30)]
        self.assertEqual(view.worst(records, registry())["provider"], "claude")

    def test_should_be_neutral_without_limits(self):
        worst = view.worst([], registry())
        self.assertEqual((worst["severity"], worst["provider"]), ("none", None))


if __name__ == "__main__":
    unittest.main()
