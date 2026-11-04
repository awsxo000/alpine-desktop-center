# Alpine Desktop Center

**Status:** experimental alpha (`0.1.0-alpha.41`)

Alpine Desktop Center is a small graphical frontend for the stable
[`alpine-desktop`](https://github.com/awsxo000/alpine) backend. It does not copy
or replace the Ansible roles. The backend remains the source of truth and can
always be executed directly from the terminal.

## Alpha scope

The modular alpha provides global actions and a dedicated **Modules** area.
The available roles are `base`, `nix`, `steam`, `nix_opengl`, `rede`,
`bluetooth`, `audio`, `swap`, `energia`, `fontes` and `kde`. For each role, the
interface can check a fixed system signal, apply the Ansible tag independently
and open its persisted log.

Global actions remain available:

- **Apply Full Configuration** — runs `make aplicar`, or opens `sh instalar.sh` in a visible terminal on first use when `make` is missing;
- **Refresh Nix Apps** — runs the installed `Refresh Nix Apps` utility when available;
- **Apply Full Configuration with Diagnostics** — runs `make diagnostico` with detailed Ansible output.

Module logs are stored inside the project/release under `./logs/<frontend-version>/<module>/`. The Overview tab's **Show Logs** button audits the live session, global actions, module execution logs and timestamped diagnostic JSON files.
In the Modules tab, `Check Status` shows the current live result, while
`View Module Log` displays the latest saved record and older history. `Open Log
Folder` opens the selected module directory in the file manager. Each module
directory contains `execution.log` and one timestamped JSON file per status check
under `diagnostics/`. Each release starts with a fresh log namespace.
The history view provides a selectable list for each saved check and the
Ansible execution log; the folder action is available there as an icon.

The application opens as a normal KDE desktop application. It does not execute
arbitrary commands typed into the interface. Backend output is shown in the
activity log so the terminal remains optional, but it is still available for
recovery and advanced use.

The project includes its own Alpine mountain and desktop configuration identity.
The visual direction uses a deep navy background, electric blue gradients,
faceted geometry and subtle orbital lines, inspired by the Roku institutional
site while remaining a distinct mark for this application. The optional
installation flow places the icon in the user's KDE icon theme instead of
using a generic Wayland or computer icon.

The source-controlled assets are [`alpine-desktop-center.svg`](resources/alpine-desktop-center.svg)
for the application icon and [`alpine-desktop-center-logo.svg`](resources/alpine-desktop-center-logo.svg)
for the horizontal wordmark.

The interface opens in the Roku-inspired dark theme by default and includes a
`Light theme` / `Dark theme` control in the header. The selected theme is saved
for the next launch. The application keeps the active Qt/Plasma style for
buttons, tabs, lists, focus rings and hover behavior; only the palette,
hierarchy and spacing are branded.

Module status checks use the backend's versioned, read-only diagnostic command.
Each result lists individual components, warnings, failures and known
dependencies instead of repeating a silent shell predicate. Ansible execution
logs remain separate from diagnostic history under the release's local
`./logs/` directory.

## Development setup

The alpha uses Python and PySide6. On Alpine 3.24, the launcher detects the
missing module and offers to install the official `py3-pyside6` package from
the `community` repository. If you prefer to prepare it manually, run:

```sh
doas apk add py3-pyside6
```

The package includes the Qt for Python bindings and their Alpine dependencies.
For development outside the system package, a generic Python setup is:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -e '.[pip]'
./alpine-desktop-center
```

The source checkout is intended for development and does not include the
backend. Use a combined release package for normal testing and distribution.

Release packages from `0.1.0-alpha.16` onward are self-contained and use only the
backend bundled in the package. Their layout is intentionally simple:

```text
Alpine-Desktop-Center-v0.1.0-alpha.36/
├── Alpine Desktop Center
├── frontend/
├── backend/
└── RELEASE-VERSIONS
```

`RELEASE-VERSIONS` records the exact frontend version, backend tag, backend
commit and diagnostic schema. The application does not fall back to a backend
found elsewhere on the machine.

The package also contains `BACKEND-MANIFEST.sha256`. On startup, and whenever
`Validate Backend` is clicked, the application checks the embedded backend's
required files and checksums. If the backend is missing or modified, all
backend-executing actions remain locked; only validation and local history
viewing remain available. The integrity check is repeated immediately before
every backend action, so deleting a file after startup cannot allow `Check
Status` or an Ansible operation to run.

## Portable two-click mode

The Release includes an executable named `Alpine Desktop Center` in the
project folder. After extracting the Release, open that file with two clicks.
It launches the portable copy of the application from the same folder and
does not require installing a desktop entry globally.

The `.desktop` entry remains available for optional menu installation. It is
not the primary portable launcher because local `.desktop` files in a download
folder require absolute executable paths on some KDE configurations.

KDE may ask you to mark the downloaded `.desktop` file as trusted. Choose
**Allow Launching** once. The application then opens normally and you can
choose an action from its window.

## Optional installation

Keep the extracted package directory intact: the root executable resolves the
adjacent `frontend/` and `backend/` directories. If a command on `PATH` is
useful, copy the complete directory and create a symlink to the root launcher;
do not copy only the frontend executable:

```sh
mkdir -p ~/.local/opt ~/.local/bin
cp -R Alpine-Desktop-Center-v0.1.0-alpha.36 ~/.local/opt/
ln -sfn "$HOME/.local/opt/Alpine-Desktop-Center-v0.1.0-alpha.36/Alpine Desktop Center" \
  ~/.local/bin/alpine-desktop-center
```

## Relationship with the backend

- Stable backend: `awsxo000/alpine`, currently released independently.
- Experimental frontend: `awsxo000/alpine-desktop-center`.
- Backend failures remain visible in the activity log and can be reproduced by
  running the equivalent command in a terminal.

This repository is intentionally alpha quality. Hardware-specific behavior,
privilege prompts and packaging integration will be validated incrementally.

## Documentation

The design is described in [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md), and
the fixed frontend/backend operations are listed in
[`docs/CONTRATO-BACKEND.md`](docs/CONTRATO-BACKEND.md).

To build a combined release locally, use:

```sh
sh scripts/package-release.sh 0.1.0-alpha.36 v1.43
```
