# Creating Custom Plugins

[← Back to list](README.md)

## File Location

Plugins are placed as directories under `plugins/features/`.
The directory name becomes the plugin name.

```
plugins/features/
├── packages/            # Plugins primarily focused on package management
│   └── my-plugin/
│       └── metadata.ini
└── post/                # Plugins primarily focused on %post scripts
    └── my-plugin/
        ├── metadata.ini
        └── ISO_DIR/     # Optional: files to place inside the ISO
```

## INI Format

```ini
[meta]
label = Plugin Name
label.ja = プラグイン名
description = What this plugin does
description.ja = プラグインの説明
check = true
default = false
order = 100
supported_os = rocky9, rocky10
requires = add-user
image_size = 12288
PLUGIN_ISO_DIR = false

[prompts]
name.type = text
name.label = Username
name.label.ja = ユーザー名
name.default = user

enabled.type = boolean
enabled.label = Enable this feature?
enabled.label.ja = この機能を有効化しますか
enabled.default = false
enabled.note = Note about this option
enabled.note.ja = このオプションについての注意

secret.type = password
secret.label = Password
secret.label.ja = パスワード

[packages]
vim
curl

[packages.remove]
-iwl*-firmware

[post]
echo "Hello, ${name}"
${if_enabled}echo "Feature enabled"${endif_enabled}
```

## [meta] Fields

| Field | Required | Description |
|-------|----------|-------------|
| `label` | ✓ | Plugin name shown in TUI and logs |
| `label.xx` | — | Localized name for language code `xx` (e.g. `label.ja`) |
| `description` | — | Plugin description |
| `description.xx` | — | Localized description for language code `xx` |
| `check` | ✓ | `true`: selectable in TUI / `false`: always applied |
| `default` | — | `true`: pre-selected (only effective when `check=true`) |
| `order` | — | Application order (lower = earlier). Defaults to `999` |
| `supported_os` | — | Comma-separated list of supported OS IDs. Omit for all OSes |
| `requires` | — | Dependency plugin name. Auto-added if not selected |
| `requires.<os_id>` | — | OS-specific dependency plugin name. Merged with `requires` for the selected OS |
| `image_size` | — | Required ISO image size in MB. Largest value across plugins is used |
| `PLUGIN_ISO_DIR` | — | `true`: copy `ISO_DIR/` contents into the LiveCD scripts area |

## ISO_DIR

When `PLUGIN_ISO_DIR = true` is set and an `ISO_DIR/` folder exists inside the plugin directory,
the contents of `ISO_DIR/` are copied to the following path in the LiveCD during the build:

```
ISO_DIR/ contents  →  scripts/make-rocky-bootable/plugins/{plugin-name}/
```

After booting the LiveCD, the files are accessible at `/run/initramfs/live/scripts/make-rocky-bootable/plugins/{plugin-name}/`.

## [prompts] Fields

Defined as `field_name.attribute = value`.

| Attribute | Description |
|-----------|-------------|
| `type` | `text` / `password` / `boolean` |
| `label` | Label shown at input time |
| `label.xx` | Localized label for language code `xx` |
| `note` | Supplementary note displayed before the prompt |
| `note.xx` | Localized note for language code `xx` |
| `default` | Default value |
| `rule` | Input validation rule (currently supports `linux_username` only) |
| `when_plugin` | Only shown when the specified plugin is selected |

## Token Substitution

Collected prompt values can be referenced in `[post]`.

| Syntax | Description |
|--------|-------------|
| `${variable}` | Replaced with the variable's value |
| `${if_variable}...${endif_variable}` | Output only when variable is truthy |
| `${if_plugin-name}...${endif_plugin-name}` | Output only when the specified plugin is selected |

## Notes on [post] Section

- Heredocs containing INI-like strings (e.g. `[General]`, `[Service]`) are handled correctly.
  The build system only recognizes `[meta]`, `[prompts]`, `[packages]`, `[packages.remove]`, and `[post]` as section boundaries.
- Scripts run inside kickstart's `%post --log=/root/ks-post.log`.
