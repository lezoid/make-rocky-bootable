# Plugin List

Plugins are located in the `plugins/` directory.
This page summarizes the available plugins and how the plugin system works.

## Always-applied Plugins

Plugins with `check = false` are always applied regardless of user selection.

| Plugin | Description | Details |
|--------|-------------|---------|
| default-remove-packages | Remove unnecessary firmware packages | [→](default-remove-packages.md) |
| default-add-packages | Add base packages required for live boot | [→](default-add-packages.md) |
| default-setting-os | Basic OS settings: SSH, firewalld, dnf | [→](default-setting-os.md) |

## Selectable Plugins

Plugins with `check = true` can be selected via TUI at build time.
A ✓ in the "Default" column means the plugin is pre-selected.

| Plugin | Description | OS | Default | Requires | Details |
|--------|-------------|----|---------|----------|---------|
| language-japanese-support | Japanese locale, keyboard, and timezone | All | — | — | [→](language-japanese-support.md) |
| add-user | Create a general user account + optionally disable root SSH login + optionally run startup-user.sh / startup-user-network.sh on first login | All | — | — | [→](add-user.md) |
| add-xfce-gui-support | XFCE desktop + XRDP | Rocky 8, 9 | — | — | [→](add-xfce-gui-support.md) |
| xfce-autologin | Configure automatic login for a specified user on XFCE desktop | Rocky 8, 9 | — | add-xfce-gui-support | [→](xfce-autologin.md) |
| add-kde-gui-support | KDE Plasma desktop + krdp (RDP) | Rocky 10 ⚠️ | — | add-user | [→](add-kde-gui-support.md) |
| kiosk-browser | Build and configure the kiosk browser with OS-specific desktop hardening | Rocky 8, 9, 10 | — | add-user, add-xfce-gui-support or add-kde-gui-support | [→](kiosk-browser.md) |
| firstboot-root-startup | Run startup-root.sh (basic) and/or startup-root-network.sh (after network) as root on first boot | All | — | — | [→](firstboot-root-startup.md) |
| default-sysprep | System cleanup (sysprep) | All | ✓ | — | [→](default-sysprep.md) |

## Creating Custom Plugins

See the [Custom Plugin Guide](custom-plugin.md) for instructions on creating your own plugins.

## Plugin System

The tool's behavior can be customized through plugins.

### Directory Structure

```
plugins/
├── os/
│   ├── rocky8/osdefine      # Rocky Linux 8 definition
│   ├── rocky9/osdefine      # Rocky Linux 9 definition
│   └── rocky10/osdefine     # Rocky Linux 10 definition
└── features/
    ├── packages/            # Package add/remove plugins
    │   └── plugin-name/
    │       └── metadata.ini
    └── post/                # %post script plugins
        └── plugin-name/
            ├── metadata.ini
            └── ISO_DIR/     # Optional: files to place inside the ISO
```

### INI Format

```ini
[meta]
label = Plugin Name
label.ja = プラグイン名
description = What this plugin does
description.ja = プラグインの説明
check = true          # true: selectable in TUI / false: always applied
default = false       # true: pre-selected (only effective when check=true)
order = 100           # Application order (lower = earlier)
supported_os = rocky10  # Limit to specific OS IDs (omit for all OSes)
requires = add-user   # Dependency plugin name (auto-added if not selected)
PLUGIN_ISO_DIR = false  # true: copy ISO_DIR/ contents into the LiveCD scripts area

[prompts]
# Define fields for interactive user input
name.type = text
name.label = Username
name.label.ja = ユーザー名
name.default = user

password.type = password
password.label = Password for ${name}
password.label.ja = ${name}ユーザーのパスワードを入力してください

enabled.type = boolean
enabled.label = Enable this feature?
enabled.label.ja = この機能を有効化しますか
enabled.note = Note: requires restart
enabled.note.ja = ※ 再起動が必要です

[packages]
# Packages to add to %packages
vim

[packages.remove]
# Packages to exclude from %packages
-iwl*-firmware

[post]
# Shell script added to %post
# Reference prompt values with ${variable}
echo "Hello, ${name}"
```

### PLUGIN_ISO_DIR

By creating an `ISO_DIR/` folder inside a plugin directory and setting `PLUGIN_ISO_DIR = true` in `metadata.ini`,
the contents of `ISO_DIR/` will be copied to the following path in the LiveCD during the build:

```
ISO_DIR/ contents  →  scripts/make-rocky-bootable/plugins/{plugin-name}/
```

After booting the LiveCD, the files are accessible at **`/run/initramfs/live/scripts/make-rocky-bootable/plugins/{plugin-name}/`**.

### Token Substitution

Collected prompt values can be referenced in `[post]`:

| Syntax | Description |
|--------|-------------|
| `${variable}` | Replaced with the variable's value |
| `${if_variable}...${endif_variable}` | Output only when variable is truthy |

### OS-specific dependencies

`requires` can be combined with OS-specific dependency keys in `[meta]`.

```ini
[meta]
requires = add-user
requires.rocky9 = add-xfce-gui-support
requires.rocky10 = add-kde-gui-support
```

When the selected OS matches, `requires.<os_id>` is merged with `requires`.
