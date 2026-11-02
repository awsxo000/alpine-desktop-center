#!/usr/bin/env python3
"""Alpine Desktop Center — modular alpha frontend.

The interface deliberately exposes only named backend operations. The stable
alpine-desktop repository remains the source of truth for Ansible roles.
"""
from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QProcess, QTimer
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

APP_NAME = "Alpine Desktop Center"
APP_VERSION = "0.1.0-alpha.11"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ICON_PATH = PROJECT_ROOT / "resources" / "alpine-desktop-center.svg"


@dataclass(frozen=True)
class ModuleSpec:
    key: str
    title: str
    description: str
    tag: str
    enable_var: str | None
    check: tuple[str, ...]


MODULES = (
    ModuleSpec("base", "Base", "Core Alpine desktop packages and privileges.", "base", None, ("sh", "-c", "command -v doas >/dev/null && command -v ansible-playbook >/dev/null")),
    ModuleSpec("nix", "Nix", "Nix package manager and user profile integration.", "nix", None, ("sh", "-c", "command -v nix >/dev/null || test -x \"$HOME/.local/share/nix/profiles/profile/bin/nix\"")),
    ModuleSpec("steam", "Steam", "Steam installation and desktop integration.", "steam", "steam_habilitado=true", ("sh", "-c", "command -v steam >/dev/null || (command -v nix >/dev/null && nix profile list 2>/dev/null | grep -q steam)")),
    ModuleSpec("nix_opengl", "Nix OpenGL", "Mesa/OpenGL integration for Nix applications.", "nix_opengl", "nix_opengl_habilitado=true", ("sh", "-c", "test -d /run/opengl-driver || test -d /run/opengl-driver-32")),
    ModuleSpec("rede", "Network", "NetworkManager and KDE network integration.", "rede", "rede_habilitada=true", ("sh", "-c", "rc-service networkmanager status >/dev/null 2>&1")),
    ModuleSpec("bluetooth", "Bluetooth", "BlueZ and KDE Bluetooth integration.", "bluetooth", "bluetooth_habilitado=true", ("sh", "-c", "rc-service bluetooth status >/dev/null 2>&1 || rc-service bluetoothd status >/dev/null 2>&1")),
    ModuleSpec("audio", "Audio", "PipeWire and WirePlumber user audio services.", "audio", "audio_habilitado=true", ("sh", "-c", "pgrep -x pipewire >/dev/null || command -v pipewire >/dev/null")),
    ModuleSpec("swap", "Swap", "Additional swapfile and hibernation support.", "swap", "swap_habilitada=true", ("sh", "-c", "swapon --show 2>/dev/null | tail -n +2 | grep -q .")),
    ModuleSpec("energia", "Energy", "Elogind, polkit and desktop power actions.", "energia", "energia_habilitada=true", ("sh", "-c", "rc-service elogind status >/dev/null 2>&1")),
    ModuleSpec("fontes", "Fonts", "Unicode, CJK, Japanese kanji and emoji coverage.", "fontes", "fontes_habilitadas=true", ("sh", "-c", "command -v fc-list >/dev/null && fc-list 2>/dev/null | grep -Eiq 'Noto|CJK|Emoji'")),
    ModuleSpec("kde", "KDE", "KDE/OpenRC compatibility and System Monitor layout.", "kde", "kde_habilitado=true", ("sh", "-c", "command -v plasmashell >/dev/null || command -v kded6 >/dev/null")),
)


class Backend:
    """Locate the backend and expose only fixed, named operations."""

    def __init__(self) -> None:
        configured = os.environ.get("ALPINE_DESKTOP_BACKEND", "").strip()
        candidates = [
            Path(configured).expanduser() if configured else None,
            Path.home() / "alpine-desktop",
            Path.home() / "Documents" / "alpine-desktop",
            Path.home() / "Downloads" / "alpine-desktop",
            Path.home() / "Music" / "alpine-desktop",
        ]
        self.path = next(
            (path for path in candidates if path and (path / "Makefile").is_file()),
            None,
        )
        self.log_dir = Path.home() / ".local" / "state" / "alpine-desktop-center" / "logs"

    @property
    def available(self) -> bool:
        return self.path is not None

    def command(self, action: str, module: ModuleSpec | None = None) -> list[str] | None:
        if not self.path:
            return None
        if action == "apply" and module is None and (self.path / "instalar.sh").is_file():
            return ["sh", "instalar.sh"]
        if action == "diagnostics":
            return ["make", "diagnostico"]
        if action == "refresh":
            names = ("refresh-nix-apps", "atualizar-aplicativos-nix", "Refresh Nix Apps")
            for name in names:
                candidate = Path.home() / ".local" / "bin" / name
                if candidate.is_file() and os.access(candidate, os.X_OK):
                    return [str(candidate)]
            for name in names[:2]:
                found = shutil.which(name)
                if found:
                    return [found]
            return None
        if action == "module" and module is not None:
            command = ["ansible-playbook", "playbooks/site.yml", "--tags", module.tag]
            if module.enable_var:
                command.extend(["-e", module.enable_var])
            return command
        return None

    def check_command(self, module: ModuleSpec) -> list[str]:
        return list(module.check)

    def log_path(self, module_key: str) -> Path:
        return self.log_dir / f"{module_key}.log"


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.backend = Backend()
        self.process: QProcess | None = None
        self.active_purpose = ""
        self.active_module: ModuleSpec | None = None
        self.statuses: dict[str, str] = {module.key: "Unknown" for module in MODULES}
        self.setWindowTitle(f"{APP_NAME} — {APP_VERSION}")
        self.setMinimumSize(980, 650)
        self._build_ui()
        self._refresh_backend_status()

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setSpacing(12)

        title = QLabel(APP_NAME)
        title.setFont(QFont("", 20, QFont.Weight.Bold))
        subtitle = QLabel("Configure, inspect and maintain your Alpine Linux desktop")
        root_layout.addWidget(title)
        root_layout.addWidget(subtitle)

        status_box = QGroupBox("Backend")
        status_layout = QFormLayout(status_box)
        self.backend_label = QLabel()
        self.version_label = QLabel(f"Frontend: {APP_VERSION}")
        status_layout.addRow("Location", self.backend_label)
        status_layout.addRow("Version", self.version_label)
        root_layout.addWidget(status_box)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_overview_tab(), "Overview")
        self.tabs.addTab(self._build_modules_tab(), "Modules")
        root_layout.addWidget(self.tabs, 1)
        self.setCentralWidget(root)

    def _build_overview_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        actions = QGroupBox("Global actions")
        action_layout = QHBoxLayout(actions)
        self.apply_button = self._button("Apply Full Configuration", "apply")
        self.refresh_button = self._button("Refresh Nix Apps", "refresh")
        self.diagnostics_button = self._button("Run Full Diagnostics", "diagnostics")
        self.check_all_button = QPushButton("Check All Modules")
        self.check_all_button.setMinimumHeight(42)
        self.check_all_button.clicked.connect(self._check_all_modules)
        for button in (self.apply_button, self.refresh_button, self.diagnostics_button, self.check_all_button):
            action_layout.addWidget(button)
        layout.addWidget(actions)

        summary = QGroupBox("Module summary")
        summary_layout = QVBoxLayout(summary)
        self.summary_label = QLabel("No module checks have run yet.")
        summary_layout.addWidget(self.summary_label)
        layout.addWidget(summary)

        log_label = QLabel("Activity log")
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Global and module output will appear here.")
        layout.addWidget(log_label)
        layout.addWidget(self.log, 1)
        return tab

    def _build_modules_tab(self) -> QWidget:
        tab = QWidget()
        layout = QHBoxLayout(tab)
        self.module_list = QListWidget()
        self.module_list.setMinimumWidth(270)
        for module in MODULES:
            item = QListWidgetItem(f"{module.title}  ·  Unknown")
            item.setData(256, module.key)
            self.module_list.addItem(item)
        self.module_list.currentRowChanged.connect(self._module_selected)
        layout.addWidget(self.module_list)

        details = QVBoxLayout()
        self.module_title = QLabel("Select a module")
        self.module_title.setFont(QFont("", 17, QFont.Weight.Bold))
        self.module_description = QLabel("Choose a role to inspect its status or run it independently.")
        self.module_description.setWordWrap(True)
        self.module_status = QLabel("Status: Unknown")
        details.addWidget(self.module_title)
        details.addWidget(self.module_description)
        details.addWidget(self.module_status)

        buttons = QHBoxLayout()
        self.module_apply_button = QPushButton("Apply Module")
        self.module_check_button = QPushButton("Check Status")
        self.module_log_button = QPushButton("View Module Log")
        self.module_apply_button.clicked.connect(self._apply_selected_module)
        self.module_check_button.clicked.connect(self._check_selected_module)
        self.module_log_button.clicked.connect(self._view_selected_log)
        for button in (self.module_apply_button, self.module_check_button, self.module_log_button):
            button.setMinimumHeight(38)
            buttons.addWidget(button)
        details.addLayout(buttons)

        details.addWidget(QLabel("Selected module log"))
        self.module_log = QPlainTextEdit()
        self.module_log.setReadOnly(True)
        self.module_log.setPlaceholderText("Select View Module Log to load the persisted role log.")
        details.addWidget(self.module_log, 1)
        layout.addLayout(details, 1)
        self.module_apply_button.setEnabled(False)
        self.module_check_button.setEnabled(False)
        self.module_log_button.setEnabled(False)
        return tab

    def _button(self, text: str, action: str) -> QPushButton:
        button = QPushButton(text)
        button.setMinimumHeight(42)
        button.clicked.connect(lambda: self._run_action(action))
        return button

    def _refresh_backend_status(self) -> None:
        if self.backend.available:
            self.backend_label.setText(str(self.backend.path))
            self.log.appendPlainText("Backend detected. Ready for global or modular actions.")
            return
        self.backend_label.setText("Not detected")
        self.log.appendPlainText("Backend not found. Set ALPINE_DESKTOP_BACKEND or clone alpine-desktop into ~/alpine-desktop.")
        self._set_actions_enabled(False)

    def _module_selected(self, row: int) -> None:
        module = MODULES[row] if 0 <= row < len(MODULES) else None
        if not module:
            return
        self.module_title.setText(module.title)
        self.module_description.setText(module.description)
        self.module_status.setText(f"Status: {self.statuses[module.key]}")
        enabled = self.backend.available and self._idle()
        self.module_apply_button.setEnabled(enabled)
        self.module_check_button.setEnabled(enabled)
        self.module_log_button.setEnabled(True)
        self._view_selected_log()

    def _selected_module(self) -> ModuleSpec | None:
        row = self.module_list.currentRow()
        return MODULES[row] if 0 <= row < len(MODULES) else None

    def _check_all_modules(self) -> None:
        if not self._idle() or not self.backend.available:
            return
        self.log.appendPlainText("\nChecking all modules...")
        self._check_queue = list(MODULES)
        self._check_next()

    def _check_next(self) -> None:
        if not getattr(self, "_check_queue", None):
            self._update_summary()
            return
        module = self._check_queue.pop(0)
        self._start_process(self.backend.check_command(module), "check", module)

    def _check_selected_module(self) -> None:
        module = self._selected_module()
        if module and self._idle():
            self._start_process(self.backend.check_command(module), "check", module)

    def _apply_selected_module(self) -> None:
        module = self._selected_module()
        if not module or not self._idle():
            return
        answer = QMessageBox.question(self, APP_NAME, f"Apply the {module.title} module now?")
        if answer == QMessageBox.StandardButton.Yes:
            command = self.backend.command("module", module)
            if command:
                self._start_process(command, "module", module)

    def _view_selected_log(self) -> None:
        module = self._selected_module()
        if not module:
            return
        path = self.backend.log_path(module.key)
        self.module_log.setPlainText(path.read_text(errors="replace") if path.is_file() else "No log recorded for this module yet.")

    def _run_action(self, action: str) -> None:
        if not self._idle():
            QMessageBox.information(self, APP_NAME, "Another action is already running.")
            return
        command = self.backend.command(action)
        if command is None:
            QMessageBox.warning(self, APP_NAME, "This action is not available. Check the backend installation.")
            return
        if action == "apply":
            answer = QMessageBox.question(self, APP_NAME, "Apply the complete Alpine Desktop configuration now?")
            if answer != QMessageBox.StandardButton.Yes:
                return
        self._start_process(command, action, None)

    def _start_process(self, command: list[str], purpose: str, module: ModuleSpec | None) -> None:
        self.active_purpose = purpose
        self.active_module = module
        self.log.appendPlainText(f"\n$ {' '.join(command)}")
        if module:
            self._append_module_log(module, f"\n$ {' '.join(command)}")
        self._set_actions_enabled(False)
        self.process = QProcess(self)
        self.process.setWorkingDirectory(str(self.backend.path))
        self.process.setProgram(command[0])
        self.process.setArguments(command[1:])
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyReadStandardOutput.connect(self._read_output)
        self.process.finished.connect(self._process_finished)
        self.process.errorOccurred.connect(self._process_error)
        self.process.start()

    def _read_output(self) -> None:
        if not self.process:
            return
        text = bytes(self.process.readAllStandardOutput()).decode(errors="replace")
        if text:
            self.log.insertPlainText(text)
            self.log.ensureCursorVisible()
            if self.active_module:
                self._append_module_log(self.active_module, text)

    def _append_module_log(self, module: ModuleSpec, text: str) -> None:
        path = self.backend.log_path(module.key)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(text)

    def _process_finished(self, exit_code: int, _status: QProcess.ExitStatus) -> None:
        self._read_output()
        purpose, module = self.active_purpose, self.active_module
        if purpose == "check" and module:
            self.statuses[module.key] = "Installed / available" if exit_code == 0 else "Not detected"
            self._update_module_row(module)
            self.module_status.setText(f"Status: {self.statuses[module.key]}")
            self.log.appendPlainText(f"{module.title}: {self.statuses[module.key]}.")
        else:
            result = "completed successfully" if exit_code == 0 else f"failed with exit code {exit_code}"
            self.log.appendPlainText(f"\nAction {result}.")
            if purpose == "module" and module and exit_code == 0:
                self.statuses[module.key] = "Applied"
                self._update_module_row(module)
                QTimer.singleShot(250, lambda: self._check_module_after_apply(module))
        self._set_actions_enabled(True)
        if purpose == "check" and getattr(self, "_check_queue", None):
            QTimer.singleShot(150, self._check_next)
        self._update_summary()

    def _check_module_after_apply(self, module: ModuleSpec) -> None:
        if self._idle():
            self._start_process(self.backend.check_command(module), "check", module)

    def _process_error(self, _error: QProcess.ProcessError) -> None:
        self._read_output()
        self.log.appendPlainText("\nCould not start the backend command.")
        self._set_actions_enabled(True)

    def _update_module_row(self, module: ModuleSpec) -> None:
        for row in range(self.module_list.count()):
            item = self.module_list.item(row)
            if item.data(256) == module.key:
                item.setText(f"{module.title}  ·  {self.statuses[module.key]}")
                break

    def _update_summary(self) -> None:
        counts = {name: sum(status == name for status in self.statuses.values()) for name in ("Installed / available", "Applied", "Not detected", "Unknown")}
        self.summary_label.setText(f"Available: {counts['Installed / available']}  ·  Applied: {counts['Applied']}  ·  Not detected: {counts['Not detected']}  ·  Unknown: {counts['Unknown']}")

    def _idle(self) -> bool:
        return not self.process or self.process.state() == QProcess.ProcessState.NotRunning

    def _set_actions_enabled(self, enabled: bool) -> None:
        available = enabled and self.backend.available
        self.apply_button.setEnabled(available)
        self.refresh_button.setEnabled(available)
        self.diagnostics_button.setEnabled(available)
        self.check_all_button.setEnabled(available)
        module = self._selected_module()
        self.module_apply_button.setEnabled(available and module is not None)
        self.module_check_button.setEnabled(available and module is not None)
        self.module_log_button.setEnabled(module is not None)


def main() -> int:
    app = QApplication([])
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    if ICON_PATH.is_file():
        app.setWindowIcon(QIcon(str(ICON_PATH)))
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
