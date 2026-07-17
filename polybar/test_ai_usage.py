import importlib.util
import os
import unittest
from datetime import datetime, timezone

_spec = importlib.util.spec_from_file_location(
    "ai_usage", os.path.join(os.path.dirname(__file__), "ai-usage.py"))
assert _spec is not None and _spec.loader is not None
ai_usage = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ai_usage)


class TestHelpers(unittest.TestCase):
    def test_severity_color_green(self):
        self.assertEqual(ai_usage.severity_color(0), ai_usage.GREEN)
        self.assertEqual(ai_usage.severity_color(49.9), ai_usage.GREEN)

    def test_severity_color_yellow(self):
        self.assertEqual(ai_usage.severity_color(50), ai_usage.YELLOW)
        self.assertEqual(ai_usage.severity_color(80), ai_usage.YELLOW)

    def test_severity_color_red(self):
        self.assertEqual(ai_usage.severity_color(80.1), ai_usage.RED)
        self.assertEqual(ai_usage.severity_color(100), ai_usage.RED)

    def test_human_int(self):
        self.assertEqual(ai_usage.human_int(999), "999")
        self.assertEqual(ai_usage.human_int(1500), "1.5k")
        self.assertEqual(ai_usage.human_int(0), "0")
        self.assertEqual(ai_usage.human_int(None), "0")

    def test_relative_reset_hours_minutes(self):
        now = datetime(2026, 6, 17, 12, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(
            ai_usage.relative_reset("2026-06-17T15:30:00+00:00", now), "reset em 3h 30m")

    def test_relative_reset_days(self):
        now = datetime(2026, 6, 17, 12, 0, 0, tzinfo=timezone.utc)
        epoch = datetime(2026, 6, 18, 13, 0, 0, tzinfo=timezone.utc).timestamp()
        self.assertEqual(ai_usage.relative_reset(epoch, now), "reset em 1d 1h")

    def test_relative_reset_past(self):
        now = datetime(2026, 6, 17, 12, 0, 0, tzinfo=timezone.utc)
        self.assertEqual(
            ai_usage.relative_reset("2026-06-17T11:00:00+00:00", now), "reset agora")

    def test_relative_reset_invalid(self):
        self.assertEqual(ai_usage.relative_reset(None), "")
        self.assertEqual(ai_usage.relative_reset("not-a-date"), "")


class TestParsers(unittest.TestCase):
    CLAUDE = {
        "five_hour": {"utilization": 22.0, "resets_at": "2026-06-17T23:00:00+00:00"},
        "seven_day": {"utilization": 7.0, "resets_at": "2026-06-23T02:00:00+00:00"},
    }
    CODEX = {
        "plan_type": "plus",
        "rate_limit": {
            "primary_window": {"used_percent": 7, "limit_window_seconds": 18000,
                               "reset_at": 1781805540},
            "secondary_window": {"used_percent": 1, "limit_window_seconds": 604800,
                                 "reset_at": 1782392340},
        },
        "credits": {"has_credits": False, "unlimited": False, "balance": "0"},
    }
    OPENROUTER = {"data": {"total_credits": 100, "total_usage": 84.74115602}}
    CODEX_NO_WINDOWS = {
        "plan_type": "plus",
        "rate_limit": {"primary_window": None, "secondary_window": None},
        "credits": {"has_credits": False, "unlimited": False, "balance": "0"},
    }
    COPILOT_LIMITED = {
        "copilot_plan": "individual",
        "quota_reset_date": "2026-07-01",
        "quota_snapshots": {
            "premium_interactions": {"unlimited": False, "has_quota": True,
                                     "percent_remaining": 40.0,
                                     "entitlement": 300, "remaining": 120},
            "chat": {"unlimited": False, "has_quota": True, "percent_remaining": 90.0},
            "completions": {"unlimited": True, "has_quota": True, "percent_remaining": 100.0},
        },
    }
    COPILOT_BUSINESS = {
        "copilot_plan": "business",
        "quota_reset_date": "2026-07-01",
        "quota_snapshots": {
            "premium_interactions": {"unlimited": False, "has_quota": False,
                                     "percent_remaining": 0.0,
                                     "entitlement": 3000, "remaining": 0},
            "chat": {"unlimited": True, "has_quota": True, "percent_remaining": 100.0},
            "completions": {"unlimited": True, "has_quota": True, "percent_remaining": 100.0},
        },
    }

    def test_parse_claude_usage(self):
        r = ai_usage.parse_claude_usage(self.CLAUDE)
        self.assertTrue(r["ok"])
        self.assertEqual([b["label"] for b in r["bars"]], ["Atual (5h)", "Semanal"])
        self.assertEqual(r["bars"][0]["percent"], 22.0)
        self.assertEqual(r["bars"][1]["percent"], 7.0)
        self.assertEqual(r["bars"][0]["resets_at"], "2026-06-17T23:00:00+00:00")

    def test_parse_codex_usage(self):
        r = ai_usage.parse_codex_usage(self.CODEX)
        self.assertTrue(r["ok"])
        self.assertEqual([b["label"] for b in r["bars"]], ["Atual (5h)", "Semanal"])
        self.assertEqual(r["bars"][0]["percent"], 7.0)
        self.assertEqual(r["bars"][1]["percent"], 1.0)
        self.assertEqual(r["bars"][0]["resets_at"], 1781805540)
        self.assertIn("Plano: plus", r["info"])

    def test_parse_codex_usage_no_windows(self):
        r = ai_usage.parse_codex_usage(self.CODEX_NO_WINDOWS)
        self.assertTrue(r["ok"])
        self.assertEqual(r["bars"], [])
        self.assertIn("Sem limites de janela", r["info"])

    def test_parse_openrouter_credits(self):
        r = ai_usage.parse_openrouter_credits(self.OPENROUTER)
        self.assertTrue(r["ok"])
        self.assertEqual(len(r["bars"]), 1)
        self.assertAlmostEqual(r["bars"][0]["percent"], 84.74115602, places=4)
        self.assertEqual(r["info"], ["Disponível: $15.26 de $100.00"])

    def test_parse_copilot_usage_limited(self):
        r = ai_usage.parse_copilot_usage(self.COPILOT_LIMITED)
        self.assertTrue(r["ok"])
        # premium e chat têm cota; completions é ilimitado → sem barra
        self.assertEqual([b["label"] for b in r["bars"]], ["Premium (mês)", "Chat"])
        self.assertEqual(r["bars"][0]["percent"], 60.0)   # 100 - 40
        self.assertEqual(r["bars"][0]["resets_at"], "2026-07-01")
        self.assertEqual(r["bars"][1]["percent"], 10.0)   # 100 - 90
        self.assertIn("Plano: individual", r["info"])
        self.assertIn("Premium: 180 de 300 usados", r["info"])  # 300 - 120

    def test_parse_copilot_usage_business_premium_exhausted(self):
        # premium com teto real esgotado (has_quota=false = sem cota SOBRANDO,
        # não 'sem cota'): barra em 100%, mesmo com chat/completions ilimitados.
        r = ai_usage.parse_copilot_usage(self.COPILOT_BUSINESS)
        self.assertTrue(r["ok"])
        self.assertEqual([b["label"] for b in r["bars"]], ["Premium (mês)"])
        self.assertEqual(r["bars"][0]["percent"], 100.0)
        self.assertEqual(r["bars"][0]["resets_at"], "2026-07-01")
        self.assertIn("Plano: business", r["info"])
        self.assertIn("Premium: 3000 de 3000 usados", r["info"])


class TestPoll(unittest.TestCase):
    def test_worst_percent_picks_max_of_ok_providers(self):
        data = {"providers": {
            "A": {"ok": True, "bars": [{"percent": 10}, {"percent": 22}]},
            "B": {"ok": True, "bars": [{"percent": 84.7}]},
            "C": {"ok": False, "bars": [{"percent": 99}]},  # ignorado
        }}
        self.assertEqual(ai_usage.worst_percent(data), 84.7)

    def test_worst_percent_none_when_no_ok_bars(self):
        data = {"providers": {"A": {"ok": False, "bars": []}}}
        self.assertIsNone(ai_usage.worst_percent(data))

    def test_worst_percent_excludes_openrouter(self):
        data = {"providers": {
            "Anthropic": {"ok": True, "bars": [{"percent": 9}]},
            "OpenRouter": {"ok": True, "bars": [{"percent": 84.7}]},  # ignorado na cor
        }}
        self.assertEqual(ai_usage.worst_percent(data), 9)

    def test_worst_percent_includes_copilot(self):
        data = {"providers": {
            "Anthropic": {"ok": True, "bars": [{"percent": 9}]},
            "GitHub Copilot": {"ok": True, "bars": [{"percent": 60}]},  # conta na cor
        }}
        self.assertEqual(ai_usage.worst_percent(data), 60)


class TestEnvVar(unittest.TestCase):
    def test_extract_plain(self):
        self.assertEqual(
            ai_usage.extract_env_value("export OPENROUTER_API_KEY=sk-or-abc\n",
                                       "OPENROUTER_API_KEY"), "sk-or-abc")

    def test_extract_without_export_and_quotes(self):
        self.assertEqual(
            ai_usage.extract_env_value('FOO=bar\nOPENROUTER_API_KEY="xyz"\n',
                                       "OPENROUTER_API_KEY"), "xyz")

    def test_extract_absent(self):
        self.assertIsNone(ai_usage.extract_env_value("NADA=1\n", "OPENROUTER_API_KEY"))


class TestCopilotToken(unittest.TestCase):
    def test_extract_oauth_from_apps_json(self):
        text = ('{"github.com:Iv1.abc": {"user": "u", "oauth_token": "gho_secret"}}')
        self.assertEqual(ai_usage.extract_copilot_oauth(text), "gho_secret")

    def test_extract_oauth_absent(self):
        self.assertIsNone(ai_usage.extract_copilot_oauth('{"github.com": {"user": "u"}}'))

    def test_extract_oauth_invalid_json(self):
        self.assertIsNone(ai_usage.extract_copilot_oauth("not json"))


class TestMonitor(unittest.TestCase):
    XRANDR = (
        "DP-1 connected primary 2560x1080+1080+0 (normal left inverted) 798mm x 334mm\n"
        "DP-2 connected 1920x2160+3640+0 (normal left inverted) 465mm x 523mm\n"
        "DVI-I-1-1 connected 1080x1920+0+0 left (normal) 598mm x 336mm\n"
        "HDMI-1 disconnected (normal left inverted right x axis y axis)\n"
    )

    def test_named_monitor_geometry(self):
        self.assertEqual(
            ai_usage.parse_monitor_geometry(self.XRANDR, "DP-1"), (1080, 0, 2560, 1080))

    def test_other_named_monitor(self):
        self.assertEqual(
            ai_usage.parse_monitor_geometry(self.XRANDR, "DVI-I-1-1"), (0, 0, 1080, 1920))

    def test_falls_back_to_primary_when_name_absent(self):
        self.assertEqual(
            ai_usage.parse_monitor_geometry(self.XRANDR, "NOPE-9"), (1080, 0, 2560, 1080))

    def test_none_when_empty(self):
        self.assertIsNone(ai_usage.parse_monitor_geometry("", "DP-1"))

    def test_right_aligned_x(self):
        # DP-1 em x=1080, largura 2560; modal de 320px, margem 8 → x=3312
        self.assertEqual(ai_usage.right_aligned_x(1080, 2560, 320, 8), 3312)
        # borda direita do modal (3312+320=3632) fica 8px antes do fim (3640)
        self.assertEqual(1080 + 2560 - ai_usage.right_aligned_x(1080, 2560, 320, 8), 320 + 8)


if __name__ == "__main__":
    unittest.main()
