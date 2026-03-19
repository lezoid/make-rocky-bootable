# language-japanese-support

[← Back to list](README.md)

## Overview

Configures Japanese locale, keyboard layout, and timezone.

## Metadata

| Field | Value |
|-------|-------|
| Type | Selectable (`check = true`) |
| Default | — (not selected) |
| Order | 20 |
| Supported OS | All |
| Requires | — |

## Added Packages

| Package | Description |
|---------|-------------|
| `langpacks-ja` | Japanese language pack |
| `glibc-langpack-ja` | glibc Japanese locale |

## Settings

| Setting | Description |
|---------|-------------|
| Locale | Sets `LANG=ja_JP.UTF-8` in `/etc/locale.conf` |
| Console keyboard | Sets `KEYMAP=jp106` in `/etc/vconsole.conf` |
| X11 keyboard | Writes `XkbLayout jp` to `/etc/X11/xorg.conf.d/00-keyboard.conf` |
| Timezone | Symlinks `/etc/localtime` to `Asia/Tokyo` |

> **Note:** The kickstart header defaults to `lang en_US.UTF-8` / `keyboard us` / `timezone UTC`.
> This plugin switches to the Japanese environment in `%post` only when selected.
