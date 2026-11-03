import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents_usage import accounts, alerts, common  # noqa: E402

NOW = 1_800_000_000.0
HOUR = 3600


def record(account, session, weekly=10, provider="claude", status=common.OK, stale=False,
           session_reset=NOW + HOUR, weekly_reset=NOW + 48 * HOUR, label=None):
    return {"provider": provider, "provider_name": "Claude Code", "account": account,
            "label": label or account.title(), "status": status, "stale": stale, "limits": [
                common.make_limit("session", "5h", session, session_reset, common.SESSION_WINDOW),
                common.make_limit("weekly", "Semanal", weekly, weekly_reset, common.WEEKLY_WINDOW)]}


def registry(active="main", mode="notify", threshold=95, extra=("work",)):
    accs = [{"id": "main", "label": "Main", "home": "/m"}] + [
        {"id": a, "label": a.title(), "home": f"/{a}"} for a in extra]
    return {"default_provider": "claude",
            "claude": {"active": active, "mode": mode, "threshold": threshold, "accounts": accs},
            "codex": {"active": "main", "mode": "notify", "threshold": 95,
                      "accounts": [{"id": "main", "label": "Main", "home": "/c"}]}}


class TestDecide(unittest.TestCase):
    def test_should_do_nothing_below_threshold(self):
        self.assertEqual(alerts.decide([record("main", 94.9)], registry(), NOW), [])

    def test_should_suggest_account_with_most_headroom_in_notify_mode(self):
        recs = [record("main", 96), record("work", 60), record("side", 20)]
        [action] = alerts.decide(recs, registry(extra=("work", "side")), NOW)
        self.assertEqual((action["kind"], action["to"]), ("suggest", "side"))

    def test_should_trigger_on_weekly_window_too(self):
        [action] = alerts.decide([record("main", 10, weekly=97), record("work", 5)], registry(), NOW)
        self.assertEqual(action["to"], "work")

    def test_should_switch_in_auto_mode(self):
        [action] = alerts.decide([record("main", 99), record("work", 1)], registry(mode="auto"), NOW)
        self.assertEqual(action["kind"], "switch")

    def test_should_respect_custom_threshold(self):
        recs = [record("main", 91), record("work", 1)]
        self.assertEqual(len(alerts.decide(recs, registry(threshold=90), NOW)), 1)
        self.assertEqual(alerts.decide(recs, registry(threshold=95), NOW), [])

    def test_should_not_suggest_accounts_requiring_signin(self):
        recs = [record("main", 99), record("work", 1, status=common.SIGNIN_REQUIRED)]
        [action] = alerts.decide(recs, registry(), NOW)
        self.assertEqual(action["kind"], "exhausted")

    def test_should_report_which_account_frees_first_when_all_are_over(self):
        recs = [record("main", 99, session_reset=NOW + 4 * HOUR),
                record("work", 98, session_reset=NOW + 1 * HOUR)]
        [action] = alerts.decide(recs, registry(), NOW)
        self.assertEqual(action["kind"], "exhausted")
        self.assertIn("Work libera primeiro", action["body"])

    def test_should_use_latest_reset_among_exceeded_windows_to_know_when_it_frees(self):
        rec = record("main", 99, weekly=99, session_reset=NOW + HOUR, weekly_reset=NOW + 30 * HOUR)
        self.assertEqual(alerts.frees_at(rec, 95), NOW + 30 * HOUR)

    def test_should_alert_single_account_users_without_switch_target(self):
        [action] = alerts.decide([record("main", 97)], registry(extra=()), NOW)
        self.assertEqual((action["kind"], action["to"]), ("exhausted", None))
        self.assertIn("Libera às", action["body"])

    def test_should_ignore_active_account_without_usable_data(self):
        recs = [record("main", 99, status=common.OFFLINE), record("work", 1)]
        self.assertEqual(alerts.decide(recs, registry(), NOW), [])

    def test_should_use_stale_numbers_when_offline_but_cached(self):
        recs = [record("main", 99, status=common.OFFLINE, stale=True), record("work", 1)]
        self.assertEqual(len(alerts.decide(recs, registry(), NOW)), 1)

    def test_should_only_evaluate_the_active_account(self):
        recs = [record("main", 10), record("work", 99)]
        self.assertEqual(alerts.decide(recs, registry(), NOW), [])


class TestPolling(unittest.TestCase):
    def test_should_poll_fast_within_fifteen_points_of_threshold(self):
        self.assertEqual(alerts.next_interval([record("main", 80)], registry()), alerts.FAST_INTERVAL)

    def test_should_poll_normally_below_margin(self):
        self.assertEqual(alerts.next_interval([record("main", 79.9)], registry()), alerts.NORMAL_INTERVAL)

    def test_should_poll_normally_without_data(self):
        self.assertEqual(alerts.next_interval([], registry()), alerts.NORMAL_INTERVAL)


class TestApply(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.alerts_file = os.path.join(tmp.name, "alerts.json")
        self.data_dir = os.path.join(tmp.name, "data")
        self.notified, self.spawned = [], []
        os.makedirs(os.path.join(tmp.name, "work"))
        self.work_home = os.path.join(tmp.name, "work")
        reg = accounts.load_registry(accounts.registry_file(self.data_dir))
        reg["claude"]["accounts"].append({"id": "work", "label": "Work", "home": self.work_home})
        accounts.save_registry(reg, self.data_dir)

    def apply(self, actions):
        return alerts.apply(actions, "/bin/agents", alerts_file=self.alerts_file, data_dir=self.data_dir,
                            notifier=lambda *a: self.notified.append(a),
                            spawner=lambda action, _bin: self.spawned.append(action))

    def action(self, kind, key="k1"):
        return {"kind": kind, "provider": "claude", "from": "main", "to": "work",
                "title": "t", "body": "b", "key": key}

    def test_should_alert_only_once_per_window(self):
        self.apply([self.action("suggest")])
        self.apply([self.action("suggest")])
        self.assertEqual(len(self.spawned), 1)

    def test_should_alert_again_after_condition_clears(self):
        self.apply([self.action("exhausted")])
        self.apply([])
        self.apply([self.action("exhausted")])
        self.assertEqual(len(self.notified), 2)

    def test_should_switch_active_account_in_auto_mode(self):
        self.apply([self.action("switch")])
        reg = accounts.load_registry(accounts.registry_file(self.data_dir))
        self.assertEqual(reg["claude"]["active"], "work")
        with open(accounts.pointer_file("claude", self.data_dir)) as f:
            self.assertEqual(f.read().strip(), self.work_home)

    def test_should_send_exhausted_as_critical(self):
        self.apply([self.action("exhausted")])
        self.assertEqual(self.notified[0][2], "critical")


class TestDbusParsing(unittest.TestCase):
    def test_should_match_action_invoked_signal(self):
        line = ("/org/freedesktop/Notifications: org.freedesktop.Notifications.ActionInvoked "
                "(uint32 42, 'switch')")
        self.assertEqual(alerts.ACTION_RE.search(line).groups(), ("42", "switch"))  # type: ignore[union-attr]

    def test_should_escape_quotes_for_gvariant(self):
        self.assertEqual(alerts._gvariant_str("Usar O'Neil"), "'Usar O\\'Neil'")


if __name__ == "__main__":
    unittest.main()
