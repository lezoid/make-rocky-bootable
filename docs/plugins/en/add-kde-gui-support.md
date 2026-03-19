# add-kde-gui-support

[← Back to list](README.md)

## Overview

Installs KDE Plasma desktop environment and krdp RDP server.
Enables remote desktop access via RDP (port 3389).

> ⚠️ **Experimental support.**
> In virtualized environments (VMware, Hyper-V, VirtualBox, etc.), changing the screen resolution
> may cause the session to become unresponsive. Physical machines are recommended.

## Metadata

| Field | Value |
|-------|-------|
| Type | Selectable (`check = true`) |
| Default | — (not selected) |
| Order | 50 |
| Supported OS | Rocky Linux 10 |
| Requires | **add-user** (auto-added) |
| ISO image size | 12288 MB |

## Prompts

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enable_rdp` | boolean | `true` | Enable RDP server (also enables SDDM auto-login) |
| `install_mozc` | boolean | `true` | Install Fcitx5 + Mozc for Japanese input — shown only when `language-japanese-support` is selected |

> **Note:** Fcitx5 + Mozc is not available for the root user.

## Settings

| Setting | Description |
|---------|-------------|
| Repositories | Enables EPEL and CRB |
| Desktop | Installs KDE Plasma Workspaces group |
| Extra packages | `firefox` |
| Boot target | Enables SDDM, sets graphical target as default |
| Theme | Applies Breeze Dark theme to `/etc/skel` |
| Power management | Disables screen dimming and screen lock |
| RDP (`enable_rdp=true`) | Enables krdp autostart, opens port 3389, configures SDDM auto-login, generates TLS certificate |
| Japanese input (`install_mozc=true`) | Installs Fcitx5 + Mozc via Flatpak |
