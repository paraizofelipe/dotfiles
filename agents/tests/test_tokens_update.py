import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents_usage import common, tokens, update  # noqa: E402

NOW = 1_800_000_000.0
DAY = 86400


def iso(ts):
    from datetime import datetime, timezone
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def claude_line(msg_id, ts, model="claude-opus-5", inp=10, out=5, cread=100, ccreate=0, kind="assistant"):
    return json.dumps({"type": kind, "timestamp": iso(ts), "requestId": f"req-{msg_id}",
                       "message": {"id": msg_id, "model": model, "usage": {
                           "input_tokens": inp, "output_tokens": out,
                           "cache_read_input_tokens": cread,
                           "cache_creation_input_tokens": ccreate}}})


def codex_token_line(ts, inp, cached, out, total):
    return json.dumps({"timestamp": iso(ts), "type": "event_msg", "payload": {
        "type": "token_count", "info": {
            "last_token_usage": {"input_tokens": inp, "cached_input_tokens": cached,
                                 "output_tokens": out},
            "total_token_usage": {"total_tokens": total}}}})


def codex_context_line(model):
    return json.dumps({"type": "turn_context", "payload": {"model": model}})


class TestClaudeParsing(unittest.TestCase):
    def test_should_keep_last_usage_when_message_is_streamed_in_several_lines(self):
        lines = [claude_line("m1", NOW, out=1), claude_line("m1", NOW, out=50)]
        entries = tokens.parse_claude_lines(lines)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0][4], 50)

    def test_should_sum_cache_read_and_creation(self):
        entries = tokens.parse_claude_lines([claude_line("m1", NOW, cread=100, ccreate=20)])
        self.assertEqual(entries[0][5], 120)

    def test_should_skip_synthetic_corrupt_and_non_assistant_lines(self):
        lines = [claude_line("m1", NOW, model="<synthetic>"), '{"assistant" "usage" broken',
                 claude_line("m2", NOW, kind="user"), ""]
        self.assertEqual(tokens.parse_claude_lines(lines), [])

    def test_should_skip_valid_json_lines_with_unexpected_shapes_and_keep_the_rest(self):
        bad = [
            json.dumps({"type": "assistant", "timestamp": iso(NOW), "message": "texto", "usage": 1}),
            json.dumps({"type": "assistant", "timestamp": iso(NOW),
                        "message": {"id": "x", "model": "m", "usage": ["assistant", "usage"]}}),
            json.dumps({"type": "assistant", "timestamp": iso(NOW),
                        "message": {"id": "y", "model": "m", "usage": {"input_tokens": "n/a"}}}),
        ]
        parsed = tokens.parse_claude_lines(bad + [claude_line("ok", NOW)])
        self.assertEqual([e[0] for e in parsed], ["ok"])


class TestCodexParsing(unittest.TestCase):
    def test_should_attribute_model_and_split_cached_input(self):
        lines = [codex_context_line("gpt-5.3-codex"), codex_token_line(NOW, 1000, 800, 50, 1050)]
        [entry] = tokens.parse_codex_lines(lines, "f")
        self.assertEqual(entry[2:], ["gpt-5.3-codex", 200, 50, 800])

    def test_should_ignore_repeated_events_with_same_cumulative_total(self):
        lines = [codex_token_line(NOW, 10, 0, 5, 15), codex_token_line(NOW + 1, 10, 0, 5, 15)]
        self.assertEqual(len(tokens.parse_codex_lines(lines, "f")), 1)

    def test_should_skip_malformed_codex_events_without_losing_later_ones(self):
        bad = json.dumps({"type": "event_msg", "timestamp": iso(NOW),
                          "payload": {"type": "token_count", "info": {"last_token_usage": "x"}}})
        lines = [codex_context_line("gpt-5"), bad, codex_token_line(NOW, 100, 40, 10, 150)]
        self.assertEqual(len(tokens.parse_codex_lines(lines, "f")), 1)

    def test_should_skip_events_without_last_usage(self):
        line = json.dumps({"timestamp": iso(NOW), "type": "event_msg",
                           "payload": {"type": "token_count", "info": None}})
        self.assertEqual(tokens.parse_codex_lines([line], "f"), [])


class TestAggregate(unittest.TestCase):
    def test_should_group_by_day_and_model_and_pick_top_model(self):
        entries = [["a", NOW - 10, "opus", 10, 10, 0], ["b", NOW - DAY, "sonnet", 1, 1, 0],
                   ["c", NOW - 20, "opus", 5, 5, 10]]
        agg = tokens.aggregate(entries, NOW)
        self.assertEqual(agg["by_model"], {"opus": 40, "sonnet": 2})
        self.assertEqual(agg["top_model"], "opus")
        self.assertEqual(agg["week"]["total"], 42)
        self.assertEqual(len(agg["by_day"]), 2)

    def test_should_exclude_entries_older_than_a_week_and_duplicates(self):
        entries = [["a", NOW - 8 * DAY, "opus", 100, 0, 0], ["b", NOW, "opus", 1, 0, 0],
                   ["b", NOW, "opus", 1, 0, 0]]
        self.assertEqual(tokens.aggregate(entries, NOW)["week"]["total"], 1)

    def test_should_return_empty_stats_without_entries(self):
        agg = tokens.aggregate([], NOW)
        self.assertEqual((agg["top_model"], agg["week"]["total"], agg["by_day"]), (None, 0, {}))


class TestCollectTokens(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = os.path.join(self.tmp.name, "claude")
        os.makedirs(os.path.join(self.home, "projects", "p1"))
        self.cache_file = os.path.join(self.tmp.name, "cache.json")

    def write_transcript(self, name, lines):
        path = os.path.join(self.home, "projects", "p1", name)
        with open(path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
        return path

    def test_should_reuse_cache_for_unchanged_files(self):
        import time
        now = time.time()
        self.write_transcript("s.jsonl", [claude_line("m1", now - 60)])
        first = tokens.collect_tokens({"claude": [self.home]}, now=now, cache_file=self.cache_file)
        cache = common.read_json(self.cache_file) or {}
        key = next(iter(cache["claude"]))
        cache["claude"][key]["entries"][0][3] = 999_000  # marca: se reparsear, some
        common.write_json_atomic(self.cache_file, cache)
        second = tokens.collect_tokens({"claude": [self.home]}, now=now, cache_file=self.cache_file)
        self.assertEqual(first["claude"]["week"]["input"], 10)
        self.assertEqual(second["claude"]["week"]["input"], 999_000)

    def test_should_count_shared_history_once_across_accounts(self):
        import time
        now = time.time()
        self.write_transcript("s.jsonl", [claude_line("m1", now - 60)])
        other = os.path.join(self.tmp.name, "claude-work")
        os.makedirs(other)
        os.symlink(os.path.join(self.home, "projects"), os.path.join(other, "projects"))
        res = tokens.collect_tokens({"claude": [self.home, other]}, now=now, cache_file=self.cache_file)
        self.assertEqual(res["claude"]["week"]["input"], 10)

    def test_should_ignore_files_not_touched_in_lookback_window(self):
        import time
        now = time.time()
        path = self.write_transcript("old.jsonl", [claude_line("m1", now - 60)])
        os.utime(path, (now - 30 * DAY, now - 30 * DAY))
        res = tokens.collect_tokens({"claude": [self.home]}, now=now, cache_file=self.cache_file)
        self.assertEqual(res["claude"]["week"]["total"], 0)


class TestUpdate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.usage_file = os.path.join(self.tmp.name, "state", "usage.json")
        self.registry = {
            "claude": {"active": "work", "accounts": [
                {"id": "main", "label": "Main", "home": "/h/claude"},
                {"id": "work", "label": "Work", "home": "/h/claude-work"}]},
            "codex": {"active": "main", "accounts": [{"id": "main", "label": "Main", "home": "/h/codex"}]},
        }

    def run_update(self, collectors, now=NOW):
        return update.run(now=now, registry=self.registry, collectors=collectors,
                          usage_file=self.usage_file, token_collector=lambda homes, now: {})

    def ok(self, percent):
        return lambda account, now: {"status": common.OK, "plan": "max", "limits": [
            common.make_limit("session", "5h", percent, now + 600, common.SESSION_WINDOW)]}

    def test_should_write_one_record_per_account_marking_active(self):
        data = self.run_update({"claude": self.ok(10), "codex": self.ok(20), "openrouter": self.ok(0)})
        claude = [r for r in data["accounts"] if r["provider"] == "claude"]
        self.assertEqual([(r["account"], r["active"]) for r in claude], [("main", False), ("work", True)])
        self.assertEqual((common.read_json(self.usage_file) or {})["accounts"], data["accounts"])

    def test_should_store_usage_file_privately(self):
        self.run_update({"claude": self.ok(1), "codex": self.ok(1), "openrouter": self.ok(1)})
        self.assertEqual(os.stat(self.usage_file).st_mode & 0o777, 0o600)

    def test_should_keep_last_good_numbers_as_stale_when_offline(self):
        self.run_update({"claude": self.ok(55), "codex": self.ok(1), "openrouter": self.ok(1)})
        offline = lambda account, now: {"status": common.OFFLINE, "error": "sem conexão"}  # noqa: E731
        data = self.run_update({"claude": offline, "codex": offline, "openrouter": offline}, now=NOW + 900)
        rec = data["accounts"][0]
        self.assertEqual((rec["status"], rec["stale"], rec["limits"][0]["percent"]),
                         (common.OFFLINE, True, 55.0))
        self.assertEqual(rec["updated_at"], NOW)

    def test_should_not_keep_old_numbers_when_signin_is_required(self):
        self.run_update({"claude": self.ok(55), "codex": self.ok(1), "openrouter": self.ok(1)})
        signin = lambda account, now: {"status": common.SIGNIN_REQUIRED, "error": "x"}  # noqa: E731
        rec = self.run_update({"claude": signin, "codex": signin, "openrouter": signin})["accounts"][0]
        self.assertEqual((rec["limits"], rec["stale"]), ([], False))

    def test_should_isolate_crashing_collector(self):
        def boom(account, now):
            raise RuntimeError("kaboom")
        data = self.run_update({"claude": boom, "codex": self.ok(5), "openrouter": self.ok(0)})
        codex = next(r for r in data["accounts"] if r["provider"] == "codex")
        self.assertEqual(data["accounts"][0]["status"], common.ERROR)
        self.assertEqual(codex["status"], common.OK)

    def test_should_store_token_stats_from_real_transcripts(self):
        home = os.path.join(self.tmp.name, "claude-home")
        os.makedirs(os.path.join(home, "projects", "p"))
        with open(os.path.join(home, "projects", "p", "s.jsonl"), "w") as f:
            f.write(claude_line("m1", NOW - 60, inp=7) + "\n")
        os.utime(os.path.join(home, "projects", "p", "s.jsonl"), (NOW, NOW))
        self.registry["claude"]["accounts"] = [{"id": "main", "label": "Main", "home": home}]
        self.registry["claude"]["active"] = "main"
        self.addCleanup(setattr, common, "TOKENS_CACHE_FILE", common.TOKENS_CACHE_FILE)
        common.TOKENS_CACHE_FILE = os.path.join(self.tmp.name, "tokens-cache.json")
        data = update.run(now=NOW, registry=self.registry, usage_file=self.usage_file,
                          collectors={"claude": self.ok(1), "codex": self.ok(1), "openrouter": self.ok(0)})
        self.assertEqual(data["tokens"]["claude"]["week"]["input"], 7)

    def test_should_survive_corrupt_previous_usage_file(self):
        os.makedirs(os.path.dirname(self.usage_file))
        with open(self.usage_file, "w") as f:
            f.write("{not json")
        data = self.run_update({"claude": self.ok(1), "codex": self.ok(1), "openrouter": self.ok(1)})
        self.assertEqual(len(data["accounts"]), 4)


if __name__ == "__main__":
    unittest.main()
