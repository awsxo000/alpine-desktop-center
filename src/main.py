#!/usr/bin/env python3
"""Alpine Desktop Center — modular alpha frontend.

The interface deliberately exposes only named backend operations. The stable
alpine-desktop repository remains the source of truth for Ansible roles.
"""
from __future__ import annotations

import os
import json
import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QProcess, QSettings, QTimer, Qt
from PySide6.QtGui import QColor, QDesktopServices, QFont, QIcon, QPalette
from PySide6.QtCore import QUrl
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
    QToolButton,
    QStyle,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

APP_NAME = "Alpine Desktop Center"
APP_VERSION = "0.1.0-alpha.30"
FRONTEND_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = Path(os.environ.get("ALPINE_DESKTOP_CENTER_ROOT", FRONTEND_ROOT)).resolve()
ICON_PATH = FRONTEND_ROOT / "resources" / "alpine-desktop-center.svg"


@dataclass(frozen=True)
class ModuleSpec:
    key: str
    title: str
    description: str
    tag: str
    enable_var: str | None


def load_module_catalog() -> tuple[ModuleSpec, ...]:
    catalog_path = PACKAGE_ROOT / "backend" / "modulos.json"
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        return tuple(
            ModuleSpec(str(item["key"]), str(item["title"]), str(item["description"]), str(item["tag"]), item.get("enable_var"))
            for item in catalog
        )
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        return ()


MODULES = load_module_catalog()


class Backend:
    """Locate the backend and expose only fixed, named operations."""

    def __init__(self) -> None:
        embedded = PACKAGE_ROOT / "backend"
        self.path = embedded if (embedded / "Makefile").is_file() else None
        self.log_dir = PACKAGE_ROOT / "logs" / APP_VERSION
        self.version = self._read_version()
        self.valid, self.validation_message = self.validate()

    def _read_version(self) -> str:
        manifest = PACKAGE_ROOT / "RELEASE-VERSIONS"
        if not manifest.is_file():
            return "embedded package manifest unavailable"
        for line in manifest.read_text(errors="replace").splitlines():
            if line.startswith("backend_version="):
                return line.partition("=")[2].strip()
        return "embedded backend version unavailable"

    @property
    def available(self) -> bool:
        return self.path is not None

    def validate(self) -> tuple[bool, str]:
        if not self.path:
            return False, "Embedded backend directory is missing."
        required = ("Makefile", "playbooks/site.yml", "scripts/diagnostico-modulo.py")
        for relative in required:
            if not (self.path / relative).is_file():
                return False, f"Required backend file is missing: {relative}"
        manifest = PACKAGE_ROOT / "BACKEND-MANIFEST.sha256"
        if not manifest.is_file():
            return False, "BACKEND-MANIFEST.sha256 is missing."
        expected: dict[str, str] = {}
        try:
            for line in manifest.read_text(errors="strict").splitlines():
                digest, separator, relative = line.partition("  ")
                if not separator or len(digest) != 64 or not relative:
                    return False, "Backend manifest is malformed."
                expected[relative] = digest
            actual_files = {
                str(path.relative_to(self.path))
                for path in self.path.rglob("*")
                if path.is_file()
            }
            if actual_files != set(expected):
                return False, "Embedded backend files differ from its manifest."
            for relative, digest in expected.items():
                file_digest = hashlib.sha256((self.path / relative).read_bytes()).hexdigest()
                if file_digest != digest:
                    return False, f"Backend file checksum mismatch: {relative}"
        except (OSError, ValueError) as exc:
            return False, f"Could not validate backend: {exc}"
        return True, f"Embedded backend {self.version} is intact."

    def command(self, action: str, module: ModuleSpec | None = None) -> list[str] | None:
        if not self.path:
            return None
        if action == "apply" and module is None and (self.path / "instalar.sh").is_file():
            return ["make", "aplicar"]
        if action == "diagnostics":
            return ["make", "diagnostico"]
        if action == "check_stable":
            return ["make", "verificar-canal-stable-nix"]
        if action == "migrate_stable":
            return ["make", "migrar-canal-stable-nix"]
        if action == "update_apps":
            return ["make", "atualizar-aplicativos-nix"]
        if action == "refresh":
            names = (
                "atualizar-aplicativos-nix.sh",
                "refresh-nix-apps",
                "atualizar-aplicativos-nix",
            )
            for name in names:
                candidate = Path.home() / ".local" / "bin" / name
                if candidate.is_file():
                    return [str(candidate)] if os.access(candidate, os.X_OK) else ["sh", str(candidate)]
            for name in names:
                found = shutil.which(name)
                if found:
                    return [found]
            return None
        if action == "module" and module is not None:
            return ["make", "aplicar-modulo", f"MODULO={module.tag}"]
        return None

    def diagnostic_command(self, module: ModuleSpec) -> list[str]:
        return ["make", "diagnostico-modulo", f"MODULO={module.key}"]

    def log_path(self, module_key: str) -> Path:
        return self.log_dir / module_key / "execution.log"

    def diagnostic_log_dir(self, module_key: str) -> Path:
        return self.log_dir / module_key / "diagnostics"

    def log_directory(self, module_key: str) -> Path:
        return self.log_dir / module_key


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.backend = Backend()
        self.settings = QSettings("AlpineDesktop", "AlpineDesktopCenter")
        self.theme = str(self.settings.value("theme", "dark"))
        self.process: QProcess | None = None
        self.active_purpose = ""
        self.active_module: ModuleSpec | None = None
        self.active_output = ""
        self.statuses: dict[str, str] = {module.key: "Unknown" for module in MODULES}
        self.setWindowTitle(f"{APP_NAME} — {APP_VERSION}")
        self.setMinimumSize(980, 650)
        self._build_ui()
        self._apply_theme()
        self._refresh_backend_status()

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("Root")
        root_layout = QVBoxLayout(root)
        root_layout.setSpacing(12)

        header = QHBoxLayout()
        header.setContentsMargins(8, 8, 8, 8)
        brand_icon = QLabel()
        brand_icon.setPixmap(QIcon(str(ICON_PATH)).pixmap(52, 52))
        header.addWidget(brand_icon)
        title_column = QVBoxLayout()
        title = QLabel(APP_NAME)
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("", 21, QFont.Weight.Bold))
        subtitle = QLabel("Configure, inspect and maintain your Alpine Linux desktop")
        subtitle.setObjectName("Subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_column.addWidget(title)
        title_column.addWidget(subtitle)
        header.addLayout(title_column, 1)
        self.theme_button = QPushButton()
        self.theme_button.setObjectName("ThemeButton")
        self.theme_button.setMinimumHeight(36)
        self.theme_button.clicked.connect(self._toggle_theme)
        header.addWidget(self.theme_button)
        root_layout.addLayout(header)

        status_box = QGroupBox("Backend")
        status_layout = QFormLayout(status_box)
        self.backend_label = QLabel()
        self.version_label = QLabel(f"Frontend: {APP_VERSION}")
        validation_row = QHBoxLayout()
        self.backend_validation_label = QLabel()
        self.validate_backend_button = QPushButton("Validate Backend")
        self.validate_backend_button.clicked.connect(self._validate_backend)
        validation_row.addWidget(self.backend_validation_label, 1)
        validation_row.addWidget(self.validate_backend_button)
        status_layout.addRow("Location", self.backend_label)
        status_layout.addRow("Version", self.version_label)
        status_layout.addRow("Integrity", validation_row)
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
        self.check_stable_button = self._button("Check Stable Channel", "check_stable")
        self.migrate_stable_button = self._button("Migrate to Latest Stable", "migrate_stable")
        self.update_apps_button = self._button("Update Nix Apps", "update_apps")
        self.refresh_button = self._button("Refresh Nix Apps", "refresh")
        self.diagnostics_button = self._button("Apply Full Configuration with Diagnostics", "diagnostics")
        self.check_all_button = QPushButton("Check All Modules")
        self.check_all_button.setMinimumHeight(42)
        self.check_all_button.clicked.connect(self._check_all_modules)
        for button in (self.apply_button, self.check_stable_button, self.migrate_stable_button, self.update_apps_button, self.refresh_button, self.diagnostics_button, self.check_all_button):
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

    def _apply_theme(self) -> None:
        dark = self.theme != "light"
        if dark:
            colors = {
                "bg": "#061226", "surface": "#0b1d38", "raised": "#10284a",
                "text": "#f5f8ff", "muted": "#9bb0d1", "accent": "#4d7ff2",
                "accent_hover": "#6b98ff", "border": "#29466e", "selection": "#1d4fae",
            }
            self.theme_button.setText("Light theme")
        else:
            colors = {
                "bg": "#f4f7fd", "surface": "#ffffff", "raised": "#eaf1fc",
                "text": "#10213a", "muted": "#58708f", "accent": "#2864db",
                "accent_hover": "#1d4fb6", "border": "#c5d5ec", "selection": "#dce9ff",
            }
            self.theme_button.setText("Dark theme")
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(colors["bg"]))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(colors["text"]))
        palette.setColor(QPalette.ColorRole.Base, QColor(colors["surface"]))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(colors["raised"]))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(colors["surface"]))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(colors["text"]))
        palette.setColor(QPalette.ColorRole.Text, QColor(colors["text"]))
        palette.setColor(QPalette.ColorRole.Button, QColor(colors["raised"]))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors["text"]))
        palette.setColor(QPalette.ColorRole.BrightText, QColor("#ffffff"))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(colors["selection"]))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff" if dark else colors["text"]))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(colors["muted"]))
        palette.setColor(QPalette.ColorRole.Link, QColor(colors["accent_hover"]))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(colors["muted"]))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(colors["muted"]))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(colors["muted"]))
        QApplication.instance().setPalette(palette)

        # Keep the active KDE/Qt style responsible for buttons, tabs, lists,
        # focus rings and hover behavior. Only the brand colors and hierarchy
        # are customized here.
        self.setStyleSheet(f"""
            QWidget#Root {{ background: {colors['bg']}; }}
            QLabel#Title {{ color: {colors['text']}; letter-spacing: 1px; }}
            QLabel#Subtitle {{ color: {colors['muted']}; }}
        """)

    def _toggle_theme(self) -> None:
        self.theme = "light" if self.theme != "light" else "dark"
        self.settings.setValue("theme", self.theme)
        self._apply_theme()

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
        self.module_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.module_title.setFont(QFont("", 17, QFont.Weight.Bold))
        self.module_description = QLabel("Choose a role to inspect its status or run it independently.")
        self.module_description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.module_description.setWordWrap(True)
        self.module_status = QLabel("Status: Unknown")
        self.module_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
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

        details.addWidget(QLabel("Current status (live check)"))
        self.module_current_status = QPlainTextEdit()
        self.module_current_status.setReadOnly(True)
        self.module_current_status.setPlaceholderText("Click Check Status to inspect the module as it is now.")
        details.addWidget(self.module_current_status)

        history_header = QHBoxLayout()
        history_header.addWidget(QLabel("Module history"))
        history_header.addStretch(1)
        self.module_folder_button = QToolButton()
        self.module_folder_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
        self.module_folder_button.setToolTip("Open this module's log folder")
        self.module_folder_button.setAccessibleName("Open module log folder")
        self.module_folder_button.clicked.connect(self._open_log_folder)
        history_header.addWidget(self.module_folder_button)
        details.addLayout(history_header)

        self.module_history_list = QListWidget()
        self.module_history_list.setMaximumHeight(130)
        self.module_history_list.currentRowChanged.connect(self._history_selected)
        details.addWidget(self.module_history_list)

        self.module_log = QPlainTextEdit()
        self.module_log.setReadOnly(True)
        self.module_log.setPlaceholderText("Click View Module Log to load the saved history.")
        details.addWidget(self.module_log, 1)
        layout.addLayout(details, 1)
        self.module_apply_button.setEnabled(False)
        self.module_check_button.setEnabled(False)
        self.module_log_button.setEnabled(False)
        self.module_folder_button.setEnabled(False)
        return tab

    def _button(self, text: str, action: str) -> QPushButton:
        button = QPushButton(text)
        button.setMinimumHeight(42)
        button.clicked.connect(lambda: self._run_action(action))
        return button

    def _refresh_backend_status(self) -> None:
        if self.backend.available:
            self.backend_label.setText(f"{self.backend.path} ({self.backend.version})")
            self._update_backend_validation_ui()
            if self.backend.valid:
                self.log.appendPlainText("Backend detected and validated. Ready for global or modular actions.")
            else:
                self.log.appendPlainText(f"Backend validation failed: {self.backend.validation_message}")
            self._set_actions_enabled(True)
            return
        self.backend_label.setText("Not detected")
        self.backend_validation_label.setText("Not validated")
        self.log.appendPlainText("Embedded backend not found. Extract the complete release package with its backend/ directory.")
        self._set_actions_enabled(False)

    def _update_backend_validation_ui(self) -> None:
        if self.backend.valid:
            self.backend_validation_label.setText("Valid and intact")
        else:
            self.backend_validation_label.setText("Blocked: validation failed")

    def _validate_backend(self) -> None:
        self.backend.valid, self.backend.validation_message = self.backend.validate()
        self._update_backend_validation_ui()
        if self.backend.valid:
            self.log.appendPlainText(f"Backend validation passed: {self.backend.validation_message}")
            QMessageBox.information(self, APP_NAME, "The embedded backend is valid and intact. Actions are unlocked.")
        else:
            self.log.appendPlainText(f"Backend validation failed: {self.backend.validation_message}")
            QMessageBox.critical(self, APP_NAME, f"Backend validation failed.\n\n{self.backend.validation_message}\n\nOnly Validate Backend remains available.")
        self._set_actions_enabled(True)

    def _backend_ready(self) -> bool:
        """Revalidate immediately before every operation that executes the backend."""
        valid, message = self.backend.validate()
        self.backend.valid = valid
        self.backend.validation_message = message
        self._update_backend_validation_ui()
        if valid:
            return True
        self._set_actions_enabled(False)
        self.log.appendPlainText(f"Backend execution blocked: {message}")
        QMessageBox.critical(self, APP_NAME, f"Backend execution blocked.\n\n{message}\n\nRun Validate Backend after restoring the embedded backend.")
        return False

    def _module_selected(self, row: int) -> None:
        module = MODULES[row] if 0 <= row < len(MODULES) else None
        if not module:
            return
        self.module_title.setText(module.title)
        self.module_description.setText(module.description)
        self.module_status.setText(f"Status: {self.statuses[module.key]}")
        enabled = self.backend.available and self.backend.valid and bool(MODULES) and self._idle()
        self.module_apply_button.setEnabled(enabled)
        self.module_check_button.setEnabled(enabled)
        self.module_log_button.setEnabled(True)
        self.module_folder_button.setEnabled(True)
        self.module_current_status.clear()
        self.module_history_list.clear()
        self.module_log.clear()

    def _selected_module(self) -> ModuleSpec | None:
        row = self.module_list.currentRow()
        return MODULES[row] if 0 <= row < len(MODULES) else None

    def _check_all_modules(self) -> None:
        if not self._idle() or not self.backend.available or not self._backend_ready():
            return
        self.log.appendPlainText("\nChecking all modules...")
        self._check_queue = list(MODULES)
        self._check_next()

    def _check_next(self) -> None:
        if not getattr(self, "_check_queue", None):
            self._update_summary()
            return
        module = self._check_queue.pop(0)
        self._start_process(self.backend.diagnostic_command(module), "check", module)

    def _check_selected_module(self) -> None:
        module = self._selected_module()
        if module and self._idle() and self._backend_ready():
            self._start_process(self.backend.diagnostic_command(module), "check", module)

    def _apply_selected_module(self) -> None:
        module = self._selected_module()
        if not module or not self._idle() or not self._backend_ready():
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
        execution = path.read_text(errors="replace") if path.is_file() else "No Ansible execution log recorded for this module yet."
        diagnostic_dir = self.backend.diagnostic_log_dir(module.key)
        diagnostic_files = sorted(diagnostic_dir.glob("*.json")) if diagnostic_dir.is_dir() else []
        self._history_entries = []
        self.module_history_list.blockSignals(True)
        self.module_history_list.clear()
        for diagnostic_path in reversed(diagnostic_files):
            try:
                report = json.loads(diagnostic_path.read_text(errors="replace"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(report, dict):
                continue
            checked_at = str(report.get("checked_at", diagnostic_path.stem))
            self._history_entries.append(("diagnostic", diagnostic_path, report))
            self.module_history_list.addItem(f"• Check Status — {checked_at}")
        if path.is_file():
            self._history_entries.append(("execution", path, execution))
            self.module_history_list.addItem("• Ansible execution.log")
        self.module_history_list.blockSignals(False)
        if self._history_entries:
            self.module_history_list.setCurrentRow(0)
        else:
            self.module_log.setPlainText("No saved logs for this module yet.")

    def _history_selected(self, row: int) -> None:
        entries = getattr(self, "_history_entries", [])
        if not 0 <= row < len(entries):
            return
        kind, _path, payload = entries[row]
        if kind == "diagnostic" and isinstance(payload, dict):
            self.module_log.setPlainText(self._format_diagnostic(payload))
        else:
            self.module_log.setPlainText(str(payload))

    def _open_log_folder(self) -> None:
        module = self._selected_module()
        if not module:
            return
        folder = self.backend.log_directory(module.key)
        folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def _run_action(self, action: str) -> None:
        if not self._idle():
            QMessageBox.information(self, APP_NAME, "Another action is already running.")
            return
        if not self._backend_ready():
            return
        command = self.backend.command(action)
        if command is None:
            QMessageBox.warning(self, APP_NAME, "This action is not available. Check the backend installation.")
            return
        if action in ("apply", "diagnostics", "migrate_stable", "update_apps"):
            messages = {
                "apply": "Apply the complete Alpine Desktop configuration now?",
                "diagnostics": "Apply the complete Alpine Desktop configuration with detailed diagnostics?",
                "migrate_stable": "Migrate the Nix profile to the latest official Stable channel?",
                "update_apps": "Update all applications installed in the Nix user profile now?",
            }
            message = messages[action]
            answer = QMessageBox.question(self, APP_NAME, message)
            if answer != QMessageBox.StandardButton.Yes:
                return
        self._start_process(command, action, None)

    def _start_process(self, command: list[str], purpose: str, module: ModuleSpec | None) -> None:
        if not self._backend_ready():
            return
        self.active_purpose = purpose
        self.active_module = module
        self.active_output = ""
        self.log.appendPlainText(f"\n$ {' '.join(command)}\n")
        if module and purpose == "module":
            self._append_module_log(module, f"\n$ {' '.join(command)}\n")
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
            self.active_output += text
            self.log.insertPlainText(text)
            self.log.ensureCursorVisible()
            if self.active_module and self.active_purpose == "module":
                self._append_module_log(self.active_module, text)

    def _append_module_log(self, module: ModuleSpec, text: str) -> None:
        self._append_log(self.backend.log_path(module.key), text)

    def _append_log(self, path: Path, text: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(text)

    def _process_finished(self, exit_code: int, _status: QProcess.ExitStatus) -> None:
        self._read_output()
        purpose, module = self.active_purpose, self.active_module
        if purpose == "check" and module:
            self._finish_module_diagnostic(module, exit_code)
        elif purpose == "check_stable":
            self._finish_stable_check(exit_code)
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

    def _finish_module_diagnostic(self, module: ModuleSpec, exit_code: int) -> None:
        report = None
        try:
            start = self.active_output.find("{")
            report = json.loads(self.active_output[start:]) if start >= 0 else None
        except json.JSONDecodeError:
            report = None
        if not isinstance(report, dict):
            self.statuses[module.key] = "Diagnostic error"
            self.module_status.setText("Status: Diagnostic error")
            self.log.appendPlainText(f"{module.title}: diagnostic output was invalid (exit code {exit_code}).")
            return
        status_map = {
            "complete": "Complete",
            "partial": "Partially configured",
            "incomplete": "Incomplete",
            "unknown": "Unknown",
        }
        status = status_map.get(str(report.get("status")), "Unknown")
        self.statuses[module.key] = status
        self._update_module_row(module)
        self.module_status.setText(f"Status: {status}")
        if self._selected_module() and self._selected_module().key == module.key:
            self.module_current_status.setPlainText(self._format_diagnostic(report))
        checked_at = str(report.get("checked_at", "now")).replace(":", "").replace("+", "-").replace(" ", "_")
        diagnostic_path = self.backend.diagnostic_log_dir(module.key) / f"{checked_at}.json"
        diagnostic_path.parent.mkdir(parents=True, exist_ok=True)
        diagnostic_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        self.log.appendPlainText(f"{module.title}: {status}.")

    def _finish_stable_check(self, exit_code: int) -> None:
        try:
            start = self.active_output.find("{")
            report = json.loads(self.active_output[start:]) if start >= 0 else {}
        except json.JSONDecodeError:
            report = {}
        if exit_code != 0 or not isinstance(report, dict):
            self.log.appendPlainText("Stable channel check failed.")
            return
        current = report.get("current_version") or "unknown"
        latest = report.get("latest_version") or "unknown"
        if report.get("status") == "update_available":
            message = f"Stable update available: nixos-{current} → nixos-{latest}."
        elif report.get("status") == "current":
            message = f"Stable channel is current: nixos-{current}."
        else:
            message = str(report.get("message", "Stable channel status unavailable."))
        self.log.appendPlainText(message)

    def _format_diagnostic(self, report: dict[str, object]) -> str:
        labels = {"ok": "[OK]", "error": "[ERROR]", "warning": "[WARNING]", "unknown": "[UNKNOWN]"}
        status = {"complete": "Complete", "partial": "Partially configured", "incomplete": "Incomplete", "unknown": "Unknown"}.get(str(report.get("status")), "Unknown")
        summary = report.get("summary", {})
        lines = [
            f"{report.get('module', 'module').upper()} — {status}",
            f"Checked at: {report.get('checked_at', 'unknown')}",
            f"Checks: {summary.get('passed', 0)} passed · {summary.get('failed', 0)} failed · {summary.get('warnings', 0)} warnings · {summary.get('total', 0)} total",
            "",
            "Components:",
        ]
        for check in report.get("checks", []):
            if isinstance(check, dict):
                marker = labels.get(str(check.get("status")), "[?]")
                lines.append(f"{marker} {check.get('title', check.get('id', 'check'))}: {check.get('message', '')}")
        dependencies = report.get("dependencies", [])
        if dependencies:
            lines.extend(["", "Dependencies:"])
            for dependency in dependencies:
                if isinstance(dependency, dict):
                    lines.append(f"- {dependency.get('module')}: {dependency.get('status')}")
        return "\n".join(lines)

    def _check_module_after_apply(self, module: ModuleSpec) -> None:
        if self._idle():
            self._start_process(self.backend.diagnostic_command(module), "check", module)

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
        available = enabled and self.backend.available and self.backend.valid
        self.apply_button.setEnabled(available)
        self.check_stable_button.setEnabled(available)
        self.migrate_stable_button.setEnabled(available)
        self.update_apps_button.setEnabled(available)
        self.refresh_button.setEnabled(available)
        self.diagnostics_button.setEnabled(available)
        self.check_all_button.setEnabled(available)
        module = self._selected_module()
        self.module_apply_button.setEnabled(available and module is not None)
        self.module_check_button.setEnabled(available and module is not None)
        self.module_log_button.setEnabled(module is not None)
        self.module_folder_button.setEnabled(module is not None)


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
