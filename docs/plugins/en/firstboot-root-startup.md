# firstboot-root-startup

[← Back to list](README.md)

## Overview

Sets up a systemd service that runs `startup-root.sh` as root exactly once on the first boot from the ISO.

## Metadata

| Field | Value |
|-------|-------|
| Type | Selectable (`check = true`) |
| Default | ✓ (pre-selected) |
| Order | 110 |
| Supported OS | All |
| Requires | — |

## Behavior

```
OS boot
  └─ After network.target
       └─ firstboot-root-startup.service runs
            └─ Executes startup-root.sh
                 └─ On completion, service file is self-deleted
                      (not executed on subsequent boots)
```

| Item | Value |
|------|-------|
| Script path | `/run/initramfs/live/scripts/make-rocky-bootable/plugins/firstboot-root-startup/startup-root.sh` |
| Log output | `/var/log/make-rocky-bootable/firstboot-root-startup.log` |
| Execution count | Once only (service file self-deletes after execution) |

## Customization

Edit the following file in the repository to run any custom process as root automatically on first boot:

```
plugins/features/post/firstboot-root-startup/ISO_DIR/startup-root.sh
```
