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
- [Embedded Scripts and Files](#embedded-scripts-and-files)
- [Important Notes Before Use](#important-notes-before-use)

---

## Overview

`make-rocky-bootable` is a bootable ISO builder for Rocky Linux using a plugin-based system.
Plugins let you customize the bootable ISO with features such as GUI support, RDP enablement, and embedded startup scripts.
Even without Kickstart knowledge, you can generate a custom ISO by simply selecting the OS version, plugin features, and boot mode through the interactive TUI.

Plugins also support full-screen browser environments (kiosk mode).
It can be used to replace Windows-based terminals that simply display a specific web page in full-screen mode with a Rocky Linux based environment.

![kiosk-browser screenshot](README/res/screenshot1.png)

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
| add-user | Create a general user account + optionally disable root SSH login + optionally run startup-user.sh / startup-user-network.sh on first login | All | — | — | [→](docs/plugins/en/add-user.md) |
| add-xfce-gui-support | XFCE desktop + XRDP | Rocky 8, 9 | — | — | [→](docs/plugins/en/add-xfce-gui-support.md) |
| xfce-autologin | Configure automatic login for a specified user on XFCE desktop | Rocky 8, 9 | — | add-xfce-gui-support | [→](docs/plugins/en/xfce-autologin.md) |
| add-kde-gui-support | KDE Plasma desktop + krdp (RDP) | Rocky 10 ⚠️ | — | add-user | [→](docs/plugins/en/add-kde-gui-support.md) |
| kiosk-browser | Build and configure a kiosk browser environment with OS-specific hardening | Rocky 8, 9, 10 | — | add-user, add-xfce-gui-support or add-kde-gui-support | [→](docs/plugins/en/kiosk-browser.md) |
| firstboot-root-startup | Run startup-root.sh (basic) and/or startup-root-network.sh (after network) as root on first boot | All | — | — | [→](docs/plugins/en/firstboot-root-startup.md) |
| default-sysprep | System cleanup (sysprep) | All | ✓ | — | [→](docs/plugins/en/default-sysprep.md) |

For the full plugin list including always-applied plugins, plugin system details, and instructions on creating custom plugins, see the plugin documentation.

**[→ Plugin Documentation (English)](docs/plugins/en/README.md)**

---

## Embedded Scripts and Files

Files under `scripts/` are embedded into the root image during ISO creation and are accessible as **`/run/initramfs/live/scripts/`** when booted as a LiveCD.

### Repository Path Layout

```
Repository path                                       LiveCD path
scripts/                                    →    /run/initramfs/live/scripts/
├── make-rocky-bootable/
│   └── plugins/                            →    /run/initramfs/live/scripts/make-rocky-bootable/plugins/
│       ├── firstboot-root-startup/         →    (when firstboot-root-startup plugin is enabled)
│       │   ├── startup-root.sh            →    .../firstboot-root-startup/startup-root.sh
│       │   └── startup-root-network.sh    →    .../firstboot-root-startup/startup-root-network.sh
│       └── add-user/                       →    (when add-user plugin is enabled)
│           ├── startup-user.sh            →    .../add-user/startup-user.sh
│           └── startup-user-network.sh    →    .../add-user/startup-user-network.sh
└── users/                                  →    /run/initramfs/live/scripts/users/
```

> `make-rocky-bootable/plugins/` is generated dynamically at build time and automatically cleaned up after the build completes.
> `users/` is a directory where you can freely place files (e.g. resources referenced by startup scripts).

The standard embedded startup scripts (`firstboot-root-startup`, `add-user`) are placed under each plugin's `ISO_DIR/`:

```
plugins/features/post/firstboot-root-startup/ISO_DIR/startup-root.sh          # root startup template (basic)
plugins/features/post/firstboot-root-startup/ISO_DIR/startup-root-network.sh  # root startup template (after network)
plugins/features/post/add-user/ISO_DIR/startup-user.sh                        # user startup template (basic)
plugins/features/post/add-user/ISO_DIR/startup-user-network.sh                # user startup template (after network)
```

### firstboot-root-startup Plugin

**Runs automatically as root, exactly once on first boot.**

Two service variants can be enabled independently via plugin settings — both can be active simultaneously:

| Variant | Service | Script | Trigger |
|---------|---------|--------|---------|
| Basic | `firstboot-root-startup.service` | `startup-root.sh` | After `basic.target` |
| Network-wait | `firstboot-root-startup-network.service` | `startup-root-network.sh` | After `network-online.target` |

```
Log: /var/log/make-rocky-bootable/firstboot-root-startup.log
```

Each service self-deletes after execution and does not run on subsequent boots.

### add-user Plugin

**Runs automatically as the general user, exactly once on first login.**

Two service variants can be enabled independently via plugin settings — both can be active simultaneously:

| Variant | Service | Script | Trigger |
|---------|---------|--------|---------|
| Basic | `firstboot-user-startup.service` | `startup-user.sh` | After `default.target` |
| Network-wait | `firstboot-user-startup-network.service` | `startup-user-network.sh` | After `network-online.target` |

```
Log: ~/.local/log/make-rocky-bootable/firstboot-user-startup.log
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
