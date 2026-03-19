# kiosk-browser

This plugin builds and installs `rocky-kiosk-browser` during image creation and configures it as the kiosk browser for the user created by `add-user`.

## What it does

- clones `https://github.com/lezoid/rocky-kiosk-browser.git` during `%post`
- builds the browser with Qt WebEngine
- installs the browser under `/opt/make-rocky-bootable/kiosk-browser/`
- creates user services for startup and session hardening
- copies `domain-policy.json` and `page-list.json` from `ISO_DIR/config/` into a user-local runtime directory before launch

## Runtime files

- browser binary: `/opt/make-rocky-bootable/kiosk-browser/bin/kiosk-browser`
- launcher: `/opt/make-rocky-bootable/kiosk-browser/bin/run-kiosk-browser.sh`
- runtime config sync target: `~/.local/share/make-rocky-bootable/kiosk-browser/config/`
- logs: `~/.local/log/make-rocky-bootable/`

## Browser source

- source repository: `https://github.com/lezoid/rocky-kiosk-browser.git`
- build happens during image creation, so internet connectivity is required
- the `user_agent` prompt defaults to an Edge-compatible User-Agent string

## OS-specific behavior

- Rocky 8 / Rocky 9
  - requires `add-xfce-gui-support`
  - applies XFCE / xfwm shortcut hardening
- Rocky 10
  - requires `add-kde-gui-support`
  - applies KDE shortcut hardening through `kglobalshortcutsrc`

## Plugin files

- `metadata.ini`
- `ISO_DIR/config/domain-policy.json`
- `ISO_DIR/config/domain-policy.json.example`
- `ISO_DIR/config/page-list.json`
- `ISO_DIR/config/page-list.json.example`

## Notes

- the waiting screen is embedded in the browser and switches language by runtime locale
- domain policy and page list are edited as JSON files in `ISO_DIR/config/`
- the generated launcher always syncs those JSON files into the user-local runtime directory before startup
