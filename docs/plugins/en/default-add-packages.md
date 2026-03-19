# default-add-packages

[← Back to list](README.md)

## Overview

Adds base packages required for a live boot ISO.

## Metadata

| Field | Value |
|-------|-------|
| Type | Always applied (`check = false`) |
| Order | 10 |
| Supported OS | All |

## Added Packages

| Package | Description |
|---------|-------------|
| `dracut-live` | dracut module for live boot |
| `memtest86+` | Memory test utility |
| `syslinux` | Boot loader |
| `*-logos` | OS logo packages |
| `firewalld` | Firewall daemon |
| `vi` | Text editor |
| `bash-completion` | Bash completion |
