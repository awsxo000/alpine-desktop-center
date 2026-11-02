#!/usr/bin/env python3
"""Alpine Desktop Center — alpha 0.1.

A interface é deliberadamente fina: o backend continua sendo o repositório
alpine-desktop e as ações disponíveis são comandos fixos, não texto arbitrário.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from PySide6.QtCore import QProcess, Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

APP_NAME = "Alpine Desktop Center"
APP_VERSION = "0.1.0-alpha.1"


class Backend:
    """Localiza o backend sem executar comandos fornecidos pelo usuário."""

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

    @property
    def available(self) -> bool:
        return self.path is not None

    def command(self, action: str) -> list[str] | None:
        if not self.path:
            return None
        if action == "apply" and (self.path / "instalar.sh").is_file():
            return ["sh", "instalar.sh"]
        if action == "diagnostics":
            return ["make", "diagnostico"]
        if action == "refresh":
            names = (
                "refresh-nix-apps",
                "atualizar-aplicativos-nix",
                "Refresh Nix Apps",
            )
            for name in names:
                candidate = Path.home() / ".local" / "bin" / name
                if candidate.is_file() and os.access(candidate, os.X_OK):
                    return [str(candidate)]
            for name in names[:2]:
                found = shutil.which(name)
                if found:
                    return [found]
        return None


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.backend = Backend()
        self.process: QProcess | None = None
        self.setWindowTitle(f"{APP_NAME} — {APP_VERSION}")
        self.setMinimumSize(760, 520)
        self._build_ui()
        self._refresh_status()

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setSpacing(14)

        title = QLabel(APP_NAME)
        title.setFont(QFont("", 20, QFont.Weight.Bold))
        subtitle = QLabel("Manage your Alpine Linux desktop configuration")
        subtitle.setProperty("secondary", True)
        layout.addWidget(title)
        layout.addWidget(subtitle)

        status_box = QGroupBox("Backend status")
        status_layout = QVBoxLayout(status_box)
        self.backend_label = QLabel()
        self.version_label = QLabel(f"Application: {APP_VERSION}")
        status_layout.addWidget(self.backend_label)
        status_layout.addWidget(self.version_label)
        layout.addWidget(status_box)

        actions_box = QGroupBox("Actions")
        actions_layout = QHBoxLayout(actions_box)
        self.apply_button = self._button("Apply Desktop Configuration", "apply")
        self.refresh_button = self._button("Refresh Nix Apps", "refresh")
        self.diagnostics_button = self._button("Run Diagnostics", "diagnostics")
        actions_layout.addWidget(self.apply_button)
        actions_layout.addWidget(self.refresh_button)
        actions_layout.addWidget(self.diagnostics_button)
        layout.addWidget(actions_box)

        log_label = QLabel("Activity log")
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setPlaceholderText("Action output will appear here.")
        layout.addWidget(log_label)
        layout.addWidget(self.log, 1)

        self.setCentralWidget(root)

    def _button(self, text: str, action: str) -> QPushButton:
        button = QPushButton(text)
        button.setMinimumHeight(42)
        button.clicked.connect(lambda: self._run_action(action))
        return button

    def _refresh_status(self) -> None:
        if self.backend.available:
            self.backend_label.setText(f"Backend: detected at {self.backend.path}")
            self.log.appendPlainText("Backend detected. Ready for actions.")
        else:
            self.backend_label.setText("Backend: not detected")
            self.log.appendPlainText(
                "Backend not found. Set ALPINE_DESKTOP_BACKEND or clone alpine-desktop into ~/alpine-desktop."
            )
            self.apply_button.setEnabled(False)
            self.diagnostics_button.setEnabled(False)
            self.refresh_button.setEnabled(False)

    def _run_action(self, action: str) -> None:
        if self.process and self.process.state() != QProcess.ProcessState.NotRunning:
            QMessageBox.information(self, APP_NAME, "Another action is already running.")
            return
        command = self.backend.command(action)
        if command is None:
            QMessageBox.warning(
                self,
                APP_NAME,
                "This action is not available yet. Check the backend installation.",
            )
            return
        if action == "apply":
            answer = QMessageBox.question(
                self,
                "Apply configuration",
                "Apply the complete Alpine Desktop configuration now?",
            )
            if answer != QMessageBox.StandardButton.Yes:
                return

        self.log.appendPlainText(f"\n$ {' '.join(command)}")
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
        if self.process:
            text = bytes(self.process.readAllStandardOutput()).decode(errors="replace")
            if text:
                self.log.insertPlainText(text)
                self.log.ensureCursorVisible()

    def _process_finished(self, exit_code: int, _status: QProcess.ExitStatus) -> None:
        self._read_output()
        result = "completed successfully" if exit_code == 0 else f"failed with exit code {exit_code}"
        self.log.appendPlainText(f"\nAction {result}.")
        self._set_actions_enabled(True)

    def _process_error(self, _error: QProcess.ProcessError) -> None:
        self._read_output()
        self.log.appendPlainText("\nCould not start the backend command.")
        self._set_actions_enabled(True)

    def _set_actions_enabled(self, enabled: bool) -> None:
        self.apply_button.setEnabled(enabled and self.backend.available)
        self.refresh_button.setEnabled(enabled and self.backend.available)
        self.diagnostics_button.setEnabled(enabled and self.backend.available)


def main() -> int:
    app = QApplication([])
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
