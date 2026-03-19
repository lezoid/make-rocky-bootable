# add-xfce-gui-support

[← Back to list](README.md)

## Overview

Installs the XFCE desktop environment and XRDP.
Enables remote desktop access via RDP (port 3389).

## Metadata

| Field | Value |
|-------|-------|
| Type | Selectable (`check = true`) |
| Default | — (not selected) |
| Order | 50 |
| Supported OS | Rocky Linux 8, 9 |
| Requires | — |

## Settings

| Setting | Description |
|---------|-------------|
| Repository | Enables EPEL |
| Desktop | Installs XFCE group |
| Extra packages | `langpacks-ja`, `glibc-langpack-ja`, `ibus-mozc`, `firefox`, `chromium`, `xrdp` |
| Boot target | Sets graphical target as default |
| XRDP | Enables autostart, opens port 3389 |
| Input method | Adds IBus environment variables to `.bashrc` |

> **Note:** Simultaneous login via RDP and the physical graphical console with the same user is not supported.
