# make-rocky-bootable

An interactive tool for easily creating custom bootable ISO images. :)

## Languages
- [Japanese (日本語)](README/README_JP.md)

## Table of Contents
- [Overview](#overview)
- [Requirements](#requirements)
- [Usage](#usage)
- [Plugin System](#plugin-system)
- [Available Plugins](#available-plugins)
- [Startup Scripts](#startup-scripts)
- [Important Notes Before Use](#important-notes-before-use)

---

## Overview

`make-rocky-bootable` is a bootable ISO builder for Rocky Linux using a plugin-based system.
Simply select the OS version, features, and boot mode through an interactive TUI to automatically generate a custom ISO.

**Supported OS versions:**

| OS | GUI |
|----|-----|
| Rocky Linux 8 | XFCE + XRDP |
| Rocky Linux 9 | XFCE + XRDP |
| Rocky Linux 10 | KDE Plasma + krdp ⚠️ Experimental |

> ⚠️ **Rocky Linux 10 + KDE Plasma is experimental.**
> In virtualized environments (VMware, Hyper-V, VirtualBox, etc.), changing the screen resolution
> may cause the session to become unresponsive. Physical machines are recommended.

---

## Requirements

A Rocky Linux 8 / 9 / 10 host with KVM enabled is recommended.

**Required packages:**

```sh
dnf install -y qemu-kvm lorax lorax-lmc-virt wget isomd5sum syslinux-nonlinux
```

---

## Usage

```sh
git clone https://github.com/lezoid/make-rocky-bootable.git
cd make-rocky-bootable
./build.py
```

The TUI will launch and prompt you to configure the following in order:

1. **Select OS** — Rocky Linux 8 / 9 / 10
2. **Select plugins** — Choose features to install via checkbox
3. **Plugin settings** — Enter values for selected plugins (username, password, etc.)
4. **Set root password**
5. **Select boot mode** — UEFI Boot / CSM/BIOS (MBR) Boot
6. **ISO download & build** — Automatically fetches and builds the ISO

The build takes **approximately 30 minutes to 1 hour**. When complete, the ISO is output to `build-iso/`.

### Options

```sh
./build.py [options]

  --debug           Debug mode: show generated kickstart
  --view-kickstart  Print the kickstart only; skip ISO download and build
  --language LANG   Force display language (e.g. en, ja)
```

---

## Plugin System

The tool's behavior can be customized through plugins.

### Directory Structure

```
plugins/
├── os/
│   ├── rocky8/osdefine      # Rocky Linux 8 definition
│   ├── rocky9/osdefine      # Rocky Linux 9 definition
│   └── rocky10/osdefine     # Rocky Linux 10 definition
└── features/
    ├── packages/            # Package add/remove plugins
    │   └── plugin-name/
    │       └── metadata.ini
    └── post/                # %post script plugins
        └── plugin-name/
            ├── metadata.ini
            └── ISO_DIR/     # Optional: files to place inside the ISO
```

### INI Format

```ini
[meta]
label = Plugin Name
label.ja = プラグイン名
description = What this plugin does
description.ja = プラグインの説明
check = true          # true: selectable in TUI / false: always applied
default = false       # true: pre-selected (only effective when check=true)
order = 100           # Application order (lower = earlier)
supported_os = rocky10  # Limit to specific OS IDs (omit for all OSes)
requires = add-user   # Dependency plugin name (auto-added if not selected)
PLUGIN_ISO_DIR = false  # true: copy ISO_DIR/ contents into the LiveCD scripts area

[prompts]
# Define fields for interactive user input
name.type = text
name.label = Username
name.label.ja = ユーザー名
name.default = user

password.type = password
password.label = Password for ${name}
password.label.ja = ${name}ユーザーのパスワードを入力してください

enabled.type = boolean
enabled.label = Enable this feature?
enabled.label.ja = この機能を有効化しますか
enabled.note = Note: requires restart
enabled.note.ja = ※ 再起動が必要です

[packages]
# Packages to add to %packages
vim

[packages.remove]
# Packages to exclude from %packages
-iwl*-firmware

[post]
# Shell script added to %post
# Reference prompt values with ${variable}
echo "Hello, ${name}"
```

### PLUGIN_ISO_DIR

By creating an `ISO_DIR/` folder inside a plugin directory and setting `PLUGIN_ISO_DIR = true` in `metadata.ini`,
the contents of `ISO_DIR/` will be copied to the following path in the LiveCD during the build:

```
ISO_DIR/ contents  →  scripts/make-rocky-bootable/plugins/{plugin-name}/
```

After booting the LiveCD, the files are accessible at **`/run/initramfs/live/scripts/make-rocky-bootable/plugins/{plugin-name}/`**.

### Token Substitution

Collected prompt values can be referenced in `[post]`:

| Syntax | Description |
|--------|-------------|
| `${variable}` | Replaced with the variable's value |
| `${if_variable}...${endif_variable}` | Output only when variable is truthy |

---

## Available Plugins

For the full plugin list, details, and instructions on creating custom plugins, see the plugin documentation.

**[→ Plugin Documentation (English)](docs/plugins/en/README.md)**

---

## Startup Scripts

Files under `scripts/` are embedded into the root image during ISO creation and are accessible as **`/run/initramfs/live/scripts/`** when booted as a LiveCD.

```
Repository path                                       LiveCD path
scripts/                                    →    /run/initramfs/live/scripts/
├── make-rocky-bootable/
│   └── plugins/                            →    /run/initramfs/live/scripts/make-rocky-bootable/plugins/
│       ├── firstboot-root-startup/         →    (when firstboot-root-startup plugin is enabled)
│       │   └── startup-root.sh            →    /run/initramfs/live/scripts/make-rocky-bootable/plugins/firstboot-root-startup/startup-root.sh
│       └── add-user/                       →    (when add-user plugin is enabled)
│           └── startup-user.sh            →    /run/initramfs/live/scripts/make-rocky-bootable/plugins/add-user/startup-user.sh
└── users/                                  →    /run/initramfs/live/scripts/users/
```

> `make-rocky-bootable/plugins/` is generated dynamically at build time and automatically cleaned up after the build completes.
> `users/` is a directory where you can freely place files (e.g. resources referenced by startup scripts).

The startup scripts are managed as `ISO_DIR/` content within their respective plugins:

```
plugins/features/post/firstboot-root-startup/ISO_DIR/startup-root.sh   # root startup template
plugins/features/post/add-user/ISO_DIR/startup-user.sh                 # user startup template
```

### startup-root.sh

**Runs automatically as root, exactly once on first boot.**

When the `firstboot-root-startup` plugin is enabled, it runs via a systemd service (`firstboot-root-startup.service`).
After execution, the service file is self-deleted, so it does not run on subsequent boots.

```
Execution: OS boot → After network.target → startup-root.sh runs → service self-deletes
Log:       /var/log/make-rocky-bootable/firstboot-root-startup.log
```

### startup-user.sh

**Runs automatically as the general user, exactly once on first login.**

Only active when the "Enable first-login user startup service" option in the `add-user` plugin is enabled.
Registered as a user systemd service and self-deleted after execution.

```
Execution: User login → After default.target → startup-user.sh runs → service self-deletes
Log:       ~/.local/log/make-rocky-bootable/firstboot-user-startup.log
```

Even users unfamiliar with Kickstart can automate custom tool execution and system configuration
by simply adding their processes to these scripts.

---

## Important Notes Before Use

- The created ISO contains the root password configured at build time.
- SELinux operates in `permissive` mode.
- The SSH port is open and root login is permitted.
- If a GUI plugin is enabled, the RDP port (3389) is also opened.
- **This ISO is intended for temporary use. Use in environments accessible by the general public is not recommended.**
- The KDE version does not support simultaneous login by the same user from both RDP and the physical graphical display.
