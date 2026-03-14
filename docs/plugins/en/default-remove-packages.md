# default-remove-packages

[← Back to list](README.md)

## Overview

Removes unnecessary packages to reduce the ISO image size.
Excludes wireless firmware packages (`iwl*-firmware`).

## Metadata

| Field | Value |
|-------|-------|
| Type | Always applied (`check = false`) |
| Order | 5 |
| Supported OS | All |

## Removed Packages

| Package | Description |
|---------|-------------|
| `-iwl*-firmware` | Firmware for Intel wireless adapters |
