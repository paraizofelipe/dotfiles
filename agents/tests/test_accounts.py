import json
import os
import subprocess
import sys
import tempfile
import unittest

AGENTS_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, AGENTS_DIR)

from agents_usage import accounts, common  # noqa: E402


class AccountsTestCase(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = tmp.name
        self.data_dir = os.path.join(self.root, "data")
        self.main_claude = os.path.join(self.root, "dot-claude")
        self.main_codex = os.path.join(self.root, "dot-codex")
        for home in (self.main_claude, self.main_codex):
            os.makedirs(os.path.join(home, "projects" if home == self.main_claude else "sessions"))
        open(os.path.join(self.main_claude, "settings.json"), "w").close()
        with open(os.path.join(self.main_claude, ".credentials.json"), "w") as f:
            f.write('{"claudeAiOauth": {"accessToken": "MAIN-SECRET"}}')
        self.main_state = os.path.join(self.root, "dot-claude.json")
        with open(self.main_state, "w") as f:
            json.dump({"mcpServers": {"ctx": {"command": "ctx"}}, "userID": "private"}, f)
        original = dict(accounts.MAIN_HOMES)
        accounts.MAIN_HOMES.update(claude=self.main_claude, codex=self.main_codex)
        self.addCleanup(accounts.MAIN_HOMES.update, original)

    def registry(self):
        return accounts.load_registry(accounts.registry_file(self.data_dir))

    def add(self, label, provider="claude"):
        return accounts.add_account(provider, label, data_dir=self.data_dir, main_state=self.main_state)


class TestRegistry(AccountsTestCase):
    def test_should_always_expose_main_account_when_registry_is_missing(self):
        reg = self.registry()
        self.assertEqual([a["id"] for a in reg["claude"]["accounts"]], ["main"])
        self.assertEqual((reg["claude"]["active"], reg["claude"]["threshold"]), ("main", 95))

    def test_should_find_account_by_id_label_or_position(self):
        self.add("Work Max")
        reg = self.registry()
        for ref in ("work-max", "WORK MAX", "2"):
            self.assertEqual(accounts.find_account(reg, "claude", ref)["id"], "work-max")

    def test_should_fail_for_unknown_or_out_of_range_reference(self):
        reg = self.registry()
        for ref in ("nope", "0", "9"):
            with self.assertRaises(accounts.AccountError):
                accounts.find_account(reg, "claude", ref)


class TestAdd(AccountsTestCase):
    def test_should_create_private_home_with_shared_history_but_own_credentials(self):
        acc = self.add("Work")
        self.assertEqual(os.stat(acc["home"]).st_mode & 0o777, 0o700)
        self.assertEqual(os.readlink(os.path.join(acc["home"], "projects")),
                         os.path.join(self.main_claude, "projects"))
        self.assertFalse(os.path.lexists(os.path.join(acc["home"], ".credentials.json")))

    def test_should_copy_only_mcp_servers_from_main_state(self):
        acc = self.add("Work")
        state = common.read_json(os.path.join(acc["home"], ".claude.json"))
        self.assertEqual(state, {"mcpServers": {"ctx": {"command": "ctx"}}})

    def test_should_not_copy_claude_state_into_codex_accounts(self):
        acc = self.add("Side", provider="codex")
        self.assertFalse(os.path.exists(os.path.join(acc["home"], ".claude.json")))
        self.assertTrue(os.path.islink(os.path.join(acc["home"], "sessions")))

    def test_should_reject_duplicate_and_empty_names(self):
        self.add("Work")
        with self.assertRaises(accounts.AccountError):
            self.add("work")
        with self.assertRaises(accounts.AccountError):
            self.add("  !! ")

    def test_should_store_registry_privately(self):
        self.add("Work")
        self.assertEqual(os.stat(accounts.registry_file(self.data_dir)).st_mode & 0o777, 0o600)


class TestUse(AccountsTestCase):
    def test_should_write_pointer_for_extra_account_and_clear_it_for_main(self):
        acc = self.add("Work")
        pointer = accounts.pointer_file("claude", self.data_dir)
        accounts.use_account("claude", "work", data_dir=self.data_dir)
        with open(pointer) as f:
            self.assertEqual(f.read().strip(), acc["home"])
        self.assertEqual(self.registry()["claude"]["active"], "work")
        accounts.use_account("claude", "main", data_dir=self.data_dir)
        self.assertFalse(os.path.exists(pointer))

    def test_should_keep_providers_independent(self):
        self.add("Work")
        accounts.use_account("claude", "work", data_dir=self.data_dir)
        self.assertEqual(self.registry()["codex"]["active"], "main")


class TestRenameRemove(AccountsTestCase):
    def test_should_rename_label_keeping_stable_id(self):
        self.add("Work")
        acc = accounts.rename_account("claude", "work", "Empresa", data_dir=self.data_dir)
        self.assertEqual((acc["id"], acc["label"]), ("work", "Empresa"))

    def test_should_refuse_removing_main(self):
        with self.assertRaises(accounts.AccountError):
            accounts.remove_account("claude", "main", data_dir=self.data_dir)

    def test_should_remove_home_without_touching_shared_history(self):
        acc = self.add("Work")
        marker = os.path.join(self.main_claude, "projects", "keep.jsonl")
        open(marker, "w").close()
        accounts.remove_account("claude", "work", data_dir=self.data_dir)
        self.assertFalse(os.path.exists(acc["home"]))
        self.assertTrue(os.path.exists(marker))
        self.assertTrue(os.path.exists(os.path.join(self.main_claude, ".credentials.json")))

    def test_should_fall_back_to_main_when_removing_active_account(self):
        self.add("Work")
        accounts.use_account("claude", "work", data_dir=self.data_dir)
        accounts.remove_account("claude", "work", data_dir=self.data_dir)
        self.assertEqual(self.registry()["claude"]["active"], "main")
        self.assertFalse(os.path.exists(accounts.pointer_file("claude", self.data_dir)))

    def test_should_refuse_deleting_home_outside_accounts_root(self):
        self.add("Work")
        reg = self.registry()
        reg["claude"]["accounts"][1]["home"] = self.main_claude  # registro adulterado
        accounts.save_registry(reg, self.data_dir)
        with self.assertRaises(accounts.AccountError):
            accounts.remove_account("claude", "work", data_dir=self.data_dir)
        self.assertTrue(os.path.isdir(self.main_claude))


class TestModeAndLogin(AccountsTestCase):
    def test_should_set_auto_mode_with_threshold(self):
        entry = accounts.set_mode("codex", "auto", 90, data_dir=self.data_dir)
        self.assertEqual((entry["mode"], entry["threshold"]), ("auto", 90))

    def test_should_reject_invalid_mode_or_threshold(self):
        with self.assertRaises(accounts.AccountError):
            accounts.set_mode("claude", "turbo", data_dir=self.data_dir)
        with self.assertRaises(accounts.AccountError):
            accounts.set_mode("claude", "auto", 150, data_dir=self.data_dir)

    def test_should_login_extra_account_in_its_home_with_private_browser(self):
        acc = self.add("Work")
        argv, env = accounts.login_command("claude", acc, browser="/x/private")
        self.assertEqual(argv, ["claude", "auth", "login"])
        self.assertEqual((env["CLAUDE_CONFIG_DIR"], env["BROWSER"]), (acc["home"], "/x/private"))

    def test_should_login_main_without_config_dir_override(self):
        os.environ["CODEX_HOME"] = "/leak"
        self.addCleanup(os.environ.pop, "CODEX_HOME", None)
        argv, env = accounts.login_command("codex", {"id": "main", "home": self.main_codex}, "/x/p")
        self.assertEqual(argv, ["codex", "login"])
        self.assertNotIn("CODEX_HOME", env)
        self.assertEqual(env.get("BROWSER"), os.environ.get("BROWSER"))  # main usa o navegador normal


class TestShim(unittest.TestCase):
    """Executa o shim real contra um 'claude' falso que imprime o env."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = tmp.name
        self.real_bin = os.path.join(self.root, "realbin")
        os.makedirs(self.real_bin)
        fake = os.path.join(self.real_bin, "claude")
        with open(fake, "w") as f:
            f.write('#!/usr/bin/env bash\necho "dir=${CLAUDE_CONFIG_DIR:-} args=$*"\n')
        os.chmod(fake, 0o755)
        self.data = os.path.join(self.root, "xdg")
        os.makedirs(os.path.join(self.data, "agents"))
        self.work_home = os.path.join(self.root, "work")
        os.makedirs(self.work_home)

    def run_shim(self, extra_env=None):
        shims = os.path.join(AGENTS_DIR, "shims")
        env = {"PATH": f"{shims}:{self.real_bin}:/usr/bin:/bin", "HOME": self.root,
               "XDG_DATA_HOME": self.data, **(extra_env or {})}
        out = subprocess.run([os.path.join(shims, "claude"), "-p", "hi"], env=env,
                             capture_output=True, text=True, timeout=10)
        return out.returncode, out.stdout.strip()

    def set_pointer(self, value):
        with open(os.path.join(self.data, "agents", "active-claude"), "w") as f:
            f.write(value + "\n")

    def test_should_pass_through_without_pointer(self):
        self.assertEqual(self.run_shim(), (0, "dir= args=-p hi"))

    def test_should_export_active_account_home(self):
        self.set_pointer(self.work_home)
        self.assertEqual(self.run_shim(), (0, f"dir={self.work_home} args=-p hi"))

    def test_should_respect_explicit_env_over_active_account(self):
        self.set_pointer(self.work_home)
        self.assertEqual(self.run_shim({"CLAUDE_CONFIG_DIR": "/explicit"}),
                         (0, "dir=/explicit args=-p hi"))

    def test_should_ignore_pointer_to_missing_directory(self):
        self.set_pointer(os.path.join(self.root, "gone"))
        self.assertEqual(self.run_shim(), (0, "dir= args=-p hi"))

    def test_should_fail_cleanly_when_real_binary_is_missing(self):
        os.remove(os.path.join(self.real_bin, "claude"))
        code, _ = self.run_shim()
        self.assertEqual(code, 127)


if __name__ == "__main__":
    unittest.main()
