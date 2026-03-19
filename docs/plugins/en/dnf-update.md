# dnf-update

`dnf-update` is an optional post plugin that runs `dnf -y update` during Kickstart `%post`.

## Behavior

- Runs after `default-setting-os`
- Uses the `dnf.conf` tuning already written by `default-setting-os`
- Updates installed packages in the build VM before later post plugins run

## Notes

- This plugin is optional and is not selected by default
- Enabling it increases build time
- The build becomes more dependent on mirror and network conditions
- Supported on Rocky Linux 8 / 9 / 10
