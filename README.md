# Alpine Desktop Center

**Status:** experimental alpha (`0.1.0-alpha.1`)

Alpine Desktop Center is a small graphical frontend for the stable
[`alpine-desktop`](https://github.com/awsxo000/alpine) backend. It does not copy
or replace the Ansible roles. The backend remains the source of truth and can
always be executed directly from the terminal.

## Alpha scope

The first alpha provides three fixed actions:

- **Apply Desktop Configuration** — runs `sh instalar.sh`;
- **Refresh Nix Apps** — runs the installed `Refresh Nix Apps` utility when available;
- **Run Diagnostics** — runs `make diagnostico`.

The application opens as a normal KDE desktop application. It does not execute
arbitrary commands typed into the interface. Backend output is shown in the
activity log so the terminal remains optional, but it is still available for
recovery and advanced use.

## Development setup

The alpha uses Python and PySide6. On Alpine, install a Qt/PySide6 package
available for your release, or use a Nix development environment. A generic
Python setup is:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
./alpine-desktop-center
```

The current alpha assumes that `alpine-desktop` is already cloned in one of
these locations:

```text
~/alpine-desktop
~/Documents/alpine-desktop
~/Downloads/alpine-desktop
~/Music/alpine-desktop
```

For another location, set the backend explicitly:

```sh
export ALPINE_DESKTOP_BACKEND="$HOME/path/to/alpine-desktop"
./alpine-desktop-center
```

## Portable two-click mode

The Release includes `Alpine Desktop Center.desktop` in the project folder.
After extracting the Release, open that file with two clicks. It launches the
portable copy of the application from the same folder and does not require
installing a desktop entry globally.

KDE may ask you to mark the downloaded `.desktop` file as trusted. Choose
**Allow Launching** once. The application then opens normally and you can
choose an action from its window.

## Optional menu installation

Install the launcher and desktop entry into the user profile:

```sh
mkdir -p ~/.local/bin ~/.local/share/applications
cp alpine-desktop-center ~/.local/bin/
cp resources/alpine-desktop-center.desktop ~/.local/share/applications/
chmod +x ~/.local/bin/alpine-desktop-center
```

If the project directory is not on `PATH`, use the included installer once or
create a symlink from `~/.local/bin` to the launcher. After the KDE menu cache
refreshes, search for **Alpine Desktop Center** and open it with two clicks.

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
