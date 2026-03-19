# default-sysprep

[← Back to list](README.md)

## Overview

Performs system cleanup to prepare the ISO for distribution and reuse.
Removes machine-id, RPM DB, logs, temporary files, and more.

## Metadata

| Field | Value |
|-------|-------|
| Type | Selectable (`check = true`) |
| Default | ✓ (pre-selected) |
| Order | 200 (runs last) |
| Supported OS | All |
| Requires | — |

## Cleanup Targets

| Target | Description |
|--------|-------------|
| Core dumps | Removes `/core*` |
| RPM DB | Removes `/var/lib/rpm/__db*` |
| systemd random-seed | Removes `/var/lib/systemd/random-seed` |
| machine-id | Removes `/etc/machine-id` and recreates as empty file |
| Anaconda logs | Removes `anaconda-ks.cfg`, `ks-post.log`, `original-ks.cfg` |
| Log files | Removes `wtmp`, `btmp`, `lastlog`; truncates all files under `/var/log/` |
| Temp files | Removes `/tmp/*` and `/var/tmp/*` |
| Shell history | Removes `.bash_history` for root and all home users |
| dnf cache | Removes `/var/cache/dnf/*` |

> **Note:** `order = 200` ensures this plugin always runs last.
> Disabling this plugin will leave these files inside the ISO.
