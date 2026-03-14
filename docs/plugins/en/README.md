# Plugin List

Plugins are located in the `plugins/` directory.
See individual pages for details on each plugin.

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
| add-user | Create a general user account | All | — | — | [→](add-user.md) |
| add-xfce-gui-support | XFCE desktop + XRDP | Rocky 8, 9 | — | — | [→](add-xfce-gui-support.md) |
| add-kde-gui-support | KDE Plasma desktop + krdp (RDP) | Rocky 10 ⚠️ | — | add-user | [→](add-kde-gui-support.md) |
| firstboot-root-startup | Run startup-root.sh as root on first boot | All | ✓ | — | [→](firstboot-root-startup.md) |
| default-sysprep | System cleanup (sysprep) | All | ✓ | — | [→](default-sysprep.md) |

## Creating Custom Plugins

See the [Custom Plugin Guide](custom-plugin.md) for instructions on creating your own plugins.
