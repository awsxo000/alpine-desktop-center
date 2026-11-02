# Changelog

## 0.1.0-alpha.19

- Organized module history under `logs/<module>/`.
- Stores Ansible execution output in `execution.log` and diagnostics in `diagnostics.jsonl`.
- Keeps read compatibility with flat log files created by earlier releases.
- `Open Module Log Folder` now opens the selected module's directory directly.

## 0.1.0-alpha.18

- Separated the live module status view from saved execution and diagnostic history.
- `Check Status` now updates the current-state panel without replacing historical logs.
- `View Module Log` opens the latest saved record first and keeps the full JSONL history available.
- Added `Open Log Folder` to launch the file manager at the module log directory.

## 0.1.0-alpha.17

- Uses backend v1.37 with corrected PipeWire session diagnostics.
- Reports `wpctl`/`pactl` evidence instead of treating process discovery as the primary audio signal.
- Includes audited network, Bluetooth and swap checks from the embedded backend.

## 0.1.0-alpha.16

- Added a self-contained release package with mandatory `frontend/` and `backend/` directories.
- Pinned the release backend to `v1.36` and recorded its commit in `RELEASE-VERSIONS`.
- Changed the frontend to use only the embedded backend; external backend discovery is no longer used.
- Added the reproducible `scripts/package-release.sh` release packager.

## 0.1.0-alpha.15

- Replaced one-line module checks with structured, read-only backend diagnostics.
- Shows complete, partial and incomplete module states with individual component results.
- Separates Ansible execution logs from JSONL diagnostic history.
- Adds the versioned backend diagnostic contract to the module documentation.

## 0.1.0-alpha.14

- Fixed discovery of the backend utility `atualizar-aplicativos-nix.sh`.
- Renamed the detailed global action to `Apply Full Configuration with Diagnostics`.
- Kept `Apply Full Configuration` as the compact-output mode.

## 0.1.0-alpha.13

- Preserved native Qt/Plasma controls instead of restyling buttons and tabs.
- Added complete light/dark palettes with readable log and placeholder text.
- Kept the Roku-inspired identity in colors, alignment and hierarchy.

## 0.1.0-alpha.12

- Added Roku-inspired dark and light themes.
- Added centered branded header with persistent theme preference.
- Refined tabs, cards, lists, buttons and module details with the navy/electric-blue component styling.
- Kept native Qt/Plasma control rendering and moved branding to a readable Qt palette.

## 0.1.0-alpha.11

- Added Overview and Modules tabs.
- Added per-role status checks, isolated Ansible execution and persisted logs.
- Added module summary for the stable backend roles.

## 0.1.0-alpha.1 — 2026-11-02

- Initial KDE desktop frontend prototype.
- Added fixed actions for backend installation, Nix menu refresh and diagnostics.
- Added two-click KDE `.desktop` integration.
- Added backend discovery and activity log.
- Added architecture and backend contract documentation.
- Added a portable root `.desktop` launcher for two-click execution from a downloaded Release.
- Added PySide6 detection and optional installation of Alpine's `py3-pyside6` package.
- Added a dedicated path-resolving launcher for KDE file-manager execution.
- Added an extensionless executable `Alpine Desktop Center` for reliable two-click portable execution.
- Added a dedicated Alpine mountain and configuration SVG icon.
- Refined the mark and added a horizontal wordmark inspired by the Roku visual language.
