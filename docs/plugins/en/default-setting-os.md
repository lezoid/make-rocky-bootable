# default-setting-os

[← Back to list](README.md)

## Overview

Applies basic OS settings for SSH, firewalld, and dnf.

## Metadata

| Field | Value |
|-------|-------|
| Type | Always applied (`check = false`) |
| Order | 15 |
| Supported OS | All |

## Settings

| Setting | Description |
|---------|-------------|
| dnf | Appends `fastestmirror=True` and timeout/retry settings to `/etc/dnf/dnf.conf` |
| SSH | Enables root login (`PermitRootLogin yes`) |
| firewalld | Enabled at startup |
