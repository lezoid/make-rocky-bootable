# add-user

[← Back to list](README.md)

## Overview

Creates a general user account with optional sudo privileges, root SSH restriction, and first-login startup service.

## Metadata

| Field | Value |
|-------|-------|
| Type | Selectable (`check = true`) |
| Default | — (not selected) |
| Order | 90 |
| Supported OS | All |
| Requires | — |

## Prompts

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | text | `user` | Username |
| `password` | password | `user` | User password |
| `sudoer` | boolean | `true` | Add to wheel group (sudoers) |
| `disable_root_ssh` | boolean | `false` | Disable root SSH login |
| `enable_firstboot_user_startup` | boolean | `false` | Run `startup-user.sh` on first login |

## Settings

| Setting | Description |
|---------|-------------|
| User creation | Creates user with `useradd` and sets password |
| sudo | Adds to wheel group if `sudoer=true` |
| Root SSH | Modifies `/etc/ssh/sshd_config` if `disable_root_ssh=true` |
| Startup service | Places a systemd user service in `/etc/skel` if `enable_firstboot_user_startup=true` |

When `enable_firstboot_user_startup=true`:

| Item | Value |
|------|-------|
| Script path | `/run/initramfs/live/scripts/make-rocky-bootable/plugins/add-user/startup-user.sh` |
| Log output | `~/.local/log/make-rocky-bootable/firstboot-user-startup.log` |
| Execution count | Once only (service file self-deletes after execution) |

## Customization

Edit the following file in the repository to run any custom process as the general user automatically on first login:

```
plugins/features/post/add-user/ISO_DIR/startup-user.sh
```

> **Note:** `add-kde-gui-support` depends on `add-user`.
> If KDE is selected without `add-user`, it will be added automatically.
