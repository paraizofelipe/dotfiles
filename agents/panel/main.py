#!/usr/bin/env python3
"""Painel de agentes (PySide6 + QML). Rodar de novo com o painel aberto fecha
o painel (toggle do clique no polybar)."""
import fcntl
import os
import shlex
import signal
import sys

AGENTS_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, AGENTS_DIR)

from agents_usage import accounts, common, view  # noqa: E402

PIDFILE = os.path.join(common.STATE_DIR, "panel.pid")
LOCKFILE = os.path.join(common.STATE_DIR, "panel.lock")
AGENTS_BIN = os.path.join(AGENTS_DIR, "bin", "agents")
TERMINAL = os.environ.get("AGENTS_TERMINAL", "alacritty")
MONITOR = os.environ.get("AGENTS_PANEL_MONITOR", "DP-1")
BAR_HEIGHT = int(os.environ.get("AGENTS_PANEL_TOP", "30"))
MARGIN = 8
# Gruvbox dark; exposto ao QML como context property `theme` (visível também em inline components).
THEME = {
    "bg": "#282828", "bgAlt": "#32302f", "bgSoft": "#3c3836", "border": "#504945",
    "fg": "#ebdbb2", "fgDim": "#a89984", "accent": "#83a598", "orange": "#fe8019",
    "red": "#fb4934", "font": "Hack Nerd Font",
}


def running_panel_pid():
    try:
        with open(PIDFILE, encoding="utf-8") as f:
            pid = int(f.read().strip())
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            cmdline = f.read()
    except (OSError, ValueError):
        return None
    # PID reaproveitado por outro processo não conta como painel aberto.
    return pid if b"panel/main.py" in cmdline and pid != os.getpid() else None


def toggle_off_if_open():
    pid = running_panel_pid()
    if pid:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass
        return True
    return False


def main():
    # Lock atômico: dois cliques rápidos não abrem dois painéis. Quem não pega o
    # lock é o clique de fechar (toggle).
    os.makedirs(common.STATE_DIR, mode=0o700, exist_ok=True)
    lock = open(LOCKFILE, "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        toggle_off_if_open()
        return 0

    from PySide6.QtCore import (QFileSystemWatcher, QObject, QProcess, Property, QTimer, QUrl,
                                Signal, Slot)
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine

    class Backend(QObject):
        changed = Signal()
        busyChanged = Signal()

        def __init__(self):
            super().__init__()
            self._model = {}
            self._busy = False
            self._update_pid = None
            self._poll = QTimer(self)
            self._poll.timeout.connect(self._check_update)
            os.makedirs(common.STATE_DIR, mode=0o700, exist_ok=True)
            # O usage.json é trocado via rename atômico: observar o diretório.
            self._watcher = QFileSystemWatcher([common.STATE_DIR])
            self._watcher.directoryChanged.connect(lambda _p: self.reload())
            self._clock = QTimer(self)
            self._clock.timeout.connect(self.reload)  # "há X min" envelhece sozinho
            self._clock.start(30_000)
            self.reload()

        @Property("QVariant", notify=changed)
        def model(self):
            return self._model

        @Property(bool, notify=busyChanged)
        def busy(self):
            return self._busy

        @Slot()
        def reload(self):
            usage = common.read_json(common.USAGE_FILE, {}) or {}
            self._model = view.build(usage, accounts.load_registry())
            self.changed.emit()

        def _set_busy(self, value):
            self._busy = value
            self.busyChanged.emit()

        @Slot()
        def refresh(self):
            if self._busy:
                return
            # Destacado: fechar o painel no meio da coleta não pode matar o update.
            ok, pid = QProcess.startDetached(AGENTS_BIN, ["usage-update"], AGENTS_DIR)
            if not ok:
                print("agents-panel: não foi possível iniciar o usage-update", file=sys.stderr)
                return
            self._update_pid = pid
            self._set_busy(True)
            self._poll.start(500)

        def _check_update(self):
            try:
                os.kill(self._update_pid, 0)  # destacado: o init recolhe, não vira zumbi nosso
                return
            except ProcessLookupError:
                pass
            except PermissionError:
                return
            self._poll.stop()
            self._set_busy(False)
            self.reload()

        def _guard(self, fn, *args):
            try:
                fn(*args)
            except accounts.AccountError as exc:
                print(f"agents-panel: {exc}", file=sys.stderr)
            self.reload()

        @Slot(str, str)
        def useAccount(self, provider, account_id):
            self._guard(accounts.use_account, provider, account_id)

        @Slot(str)
        def toggleMode(self, provider):
            mode = accounts.load_registry()[provider].get("mode", "notify")
            self._guard(accounts.set_mode, provider, "notify" if mode == "auto" else "auto")

        @Slot(str, str, str)
        def renameAccount(self, provider, account_id, label):
            self._guard(accounts.rename_account, provider, account_id, label)

        def _in_terminal(self, *agents_args):
            # Login é interativo: roda num terminal, que atualiza o uso ao terminar.
            cmd = " ".join(shlex.quote(a) for a in (AGENTS_BIN, *agents_args))
            script = (f"{cmd}; {shlex.quote(AGENTS_BIN)} usage-update >/dev/null 2>&1; "
                      "read -rp 'Enter para fechar...'")
            QProcess.startDetached(TERMINAL, ["--class", "agents-login", "-e", "bash", "-c", script])
            QGuiApplication.quit()

        @Slot(str, str)
        def login(self, provider, account_id):
            self._in_terminal("account", "login", provider, account_id)

        @Slot(str, str)
        def addAccount(self, provider, label):
            if label.strip():
                self._in_terminal("account", "add", provider, label.strip())

        @Slot(result="QVariant")
        def geometry(self):
            screens = QGuiApplication.screens()
            screen = next((s for s in screens if s.name() == MONITOR), QGuiApplication.primaryScreen())
            g = screen.geometry()
            return {"right": g.x() + g.width() - MARGIN, "top": g.y() + BAR_HEIGHT + 4,
                    "maxHeight": g.height() - BAR_HEIGHT - 2 * MARGIN}

    with open(PIDFILE, "w", encoding="utf-8") as f:
        f.write(str(os.getpid()))

    QGuiApplication.setApplicationName("agents-panel")
    QGuiApplication.setDesktopFileName("agents-panel")
    app = QGuiApplication(sys.argv)
    # singleShot: um quit() antes do app.exec() seria ignorado (toggle logo após abrir)
    signal.signal(signal.SIGTERM, lambda *_: QTimer.singleShot(0, app.quit))
    signal.signal(signal.SIGINT, lambda *_: QTimer.singleShot(0, app.quit))
    # Sem isto o Python não roda os handlers de sinal enquanto o loop do Qt está ocioso.
    tick = QTimer()
    tick.timeout.connect(lambda: None)
    tick.start(250)

    backend = Backend()
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.rootContext().setContextProperty("theme", THEME)
    # Verificação visual: QT_QPA_PLATFORM=offscreen ... main.py --screenshot out.png
    shot = sys.argv[sys.argv.index("--screenshot") + 1] if "--screenshot" in sys.argv else ""
    engine.rootContext().setContextProperty("screenshotPath", shot)
    engine.load(QUrl.fromLocalFile(os.path.join(os.path.dirname(os.path.realpath(__file__)), "Panel.qml")))
    if not engine.rootObjects():
        return 1
    if "--refresh" in sys.argv:
        backend.refresh()
    try:
        return app.exec()
    finally:
        try:
            os.remove(PIDFILE)  # só o dono do lock chega aqui
        except OSError:
            pass
        lock.close()


if __name__ == "__main__":
    sys.exit(main())
