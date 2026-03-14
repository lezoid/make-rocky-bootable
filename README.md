# make-rocky-bootable

An interactive tool for easily creating custom bootable ISO images. :)
You can create Live images that include a GUI and your own scripts.

![screenshot](README/res/screenshot0.png)

## Languages
- [English](README.md)
- [Japanese (日本語)](README/README_JP.md)

## Table of Contents
- [Overview](#overview)
- [Requirements](#requirements)
- [Usage](#usage)
- [Available Plugins](#available-plugins)
- [Startup Scripts](#startup-scripts)
- [Important Notes Before Use](#important-notes-before-use)

---

## Overview

`make-rocky-bootable` is a bootable ISO builder for Rocky Linux using a plugin-based system.
Plugins let you customize the bootable ISO with features such as GUI support, RDP enablement, and embedded startup scripts.
Even without Kickstart knowledge, you can generate a custom ISO by simply selecting the OS version, plugin features, and boot mode through the interactive TUI.

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

## Available Plugins

make-rocky-bootable lets you customize LiveCD functionality through plugins.
In addition to required OS-wide base plugins, selectable feature plugins can be chosen through the TUI during the build.

### Selectable Plugins

Plugins with `check = true` can be selected via TUI at build time.
A ✓ in the "Default" column means the plugin is pre-selected.

| Plugin | Description | OS | Default | Requires | Details |
|--------|-------------|----|---------|----------|---------|
| language-japanese-support | Japanese locale, keyboard, and timezone | All | — | — | [→](docs/plugins/en/language-japanese-support.md) |
| add-user | Create a general user account | All | — | — | [→](docs/plugins/en/add-user.md) |
| add-xfce-gui-support | XFCE desktop + XRDP | Rocky 8, 9 | — | — | [→](docs/plugins/en/add-xfce-gui-support.md) |
| add-kde-gui-support | KDE Plasma desktop + krdp (RDP) | Rocky 10 ⚠️ | — | add-user | [→](docs/plugins/en/add-kde-gui-support.md) |
| firstboot-root-startup | Run startup-root.sh as root on first boot | All | ✓ | — | [→](docs/plugins/en/firstboot-root-startup.md) |
| default-sysprep | System cleanup (sysprep) | All | ✓ | — | [→](docs/plugins/en/default-sysprep.md) |

For the full plugin list including always-applied plugins, plugin system details, and instructions on creating custom plugins, see the plugin documentation.

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
