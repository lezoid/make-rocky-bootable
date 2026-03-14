#!/usr/bin/env python3
"""
Rocky Linux Bootable ISO Builder v2 (Plugin Edition)
Reads plugins from plugins/ directory to dynamically generate kickstart files.
"""

import configparser
import argparse
import hashlib
import os
import sys
import subprocess
import getpass
import re
import tempfile
import tty
import termios
from pathlib import Path


# ---------------------------------------------------------------------------
# TUI checkbox selector
# ---------------------------------------------------------------------------

def _read_key() -> str:
    """Read a single keypress from stdin (raw mode). Returns a key string."""
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == '\x1b':            # ESC sequence (arrow keys etc.)
            ch2 = sys.stdin.read(1)
            ch3 = sys.stdin.read(1)
            return f'\x1b{ch2}{ch3}'
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def tui_radio(items: list, title: str = "Select one") -> int:
    """Interactive TUI radio button selector (single selection).

    Args:
        items: list of dicts with keys 'label', 'description'
    Returns:
        index of selected item (0-based)
    """
    cursor = 0

    RESET = '\033[0m'
    BOLD  = '\033[1m'
    CYAN  = '\033[96m'
    GREEN = '\033[92m'
    DIM   = '\033[2m'
    UP    = '\033[A'
    CLR   = '\033[2K'

    def _render():
        lines = []
        lines.append(f"{BOLD}{title}{RESET}")
        lines.append(f"{DIM}  ↑↓ Move   Enter: Confirm{RESET}")
        lines.append("")
        for i, item in enumerate(items):
            mark = f"{GREEN}●{RESET}" if i == cursor else "○"
            pointer = f"{CYAN}▶{RESET}" if i == cursor else " "
            label = f"{BOLD}{item['label']}{RESET}" if i == cursor else item['label']
            lines.append(f"  {pointer} ({mark}) {label}")
            if item.get('description'):
                lines.append(f"           {DIM}{item['description']}{RESET}")
        return lines

    rendered = _render()
    print('\n'.join(rendered))

    while True:
        key = _read_key()

        if key in ('\x1b[A', 'k'):
            cursor = (cursor - 1) % len(items)
        elif key in ('\x1b[B', 'j'):
            cursor = (cursor + 1) % len(items)
        elif key in ('\r', '\n'):
            break
        elif key == '\x03':
            raise KeyboardInterrupt

        new_rendered = _render()
        sys.stdout.write(UP * len(rendered))
        for line in new_rendered:
            sys.stdout.write(f'\r{CLR}{line}\n')
        sys.stdout.flush()
        rendered = new_rendered

    print()
    return cursor


def tui_checkbox(items: list, title: str = "Select options", dependencies: dict = None) -> list:
    """Interactive TUI checkbox selector.

    Args:
        items: list of dicts with keys 'label', 'description', 'selected'
        dependencies: {item_name: [required_item_name, ...]}
    Returns:
        list of selected indices (0-based)
    """
    cursor = 0
    selections = [item['selected'] for item in items]
    dependencies = dependencies or {}
    index_by_name = {item['name']: i for i, item in enumerate(items)}
    reverse_dependencies = {item['name']: [] for item in items}
    for item_name, required_names in dependencies.items():
        for required_name in required_names:
            if required_name in reverse_dependencies:
                reverse_dependencies[required_name].append(item_name)

    RESET   = '\033[0m'
    BOLD    = '\033[1m'
    CYAN    = '\033[96m'
    GREEN   = '\033[92m'
    DIM     = '\033[2m'
    UP      = '\033[A'
    CLR     = '\033[2K'

    def _render():
        lines = []
        lines.append(f"{BOLD}{title}{RESET}")
        lines.append(f"{DIM}  ↑↓ Move   Space: Toggle   Enter: Confirm{RESET}")
        lines.append("")
        for i, item in enumerate(items):
            mark = f"{GREEN}✓{RESET}" if selections[i] else " "
            pointer = f"{CYAN}▶{RESET}" if i == cursor else " "
            label = f"{BOLD}{item['label']}{RESET}" if i == cursor else item['label']
            lines.append(f"  {pointer} [{mark}] {label}")
            if item.get('description'):
                lines.append(f"         {DIM}{item['description']}{RESET}")
        return lines

    # Initial render
    rendered = _render()
    print('\n'.join(rendered))

    def _select_with_dependencies(start_idx: int):
        stack = [items[start_idx]['name']]
        seen = set()
        while stack:
            item_name = stack.pop()
            if item_name in seen:
                continue
            seen.add(item_name)
            idx = index_by_name.get(item_name)
            if idx is None:
                continue
            selections[idx] = True
            for required_name in dependencies.get(item_name, []):
                if required_name in index_by_name:
                    stack.append(required_name)

    def _deselect_with_dependents(start_idx: int):
        stack = [items[start_idx]['name']]
        seen = set()
        while stack:
            item_name = stack.pop()
            if item_name in seen:
                continue
            seen.add(item_name)
            idx = index_by_name.get(item_name)
            if idx is None:
                continue
            selections[idx] = False
            for dependent_name in reverse_dependencies.get(item_name, []):
                if dependent_name in index_by_name:
                    stack.append(dependent_name)

    while True:
        key = _read_key()

        if key in ('\x1b[A', 'k'):   # Up arrow or k
            cursor = (cursor - 1) % len(items)
        elif key in ('\x1b[B', 'j'): # Down arrow or j
            cursor = (cursor + 1) % len(items)
        elif key == ' ':              # Space: toggle
            if selections[cursor]:
                _deselect_with_dependents(cursor)
            else:
                _select_with_dependencies(cursor)
        elif key in ('\r', '\n'):     # Enter: confirm
            break
        elif key == '\x03':           # Ctrl+C
            raise KeyboardInterrupt

        # Redraw: move cursor up, clear and reprint
        new_rendered = _render()
        # Move up by number of previously rendered lines
        sys.stdout.write(UP * len(rendered))
        for line in new_rendered:
            sys.stdout.write(f'\r{CLR}{line}\n')
        sys.stdout.flush()
        rendered = new_rendered

    print()
    return [i for i, s in enumerate(selections) if s]


# ---------------------------------------------------------------------------
# Plugin data model
# ---------------------------------------------------------------------------

class OSDefinition:
    """Represents an OS definition loaded from plugins/os/*/osdefine."""

    def __init__(self, path: Path):
        config = configparser.ConfigParser()
        config.read(path)
        section = config['os']
        self.id = section['id']
        self.display_name = section['display_name']
        self.iso_name_prefix = section.get(
            'iso_name_prefix',
            self.display_name.replace(' Linux ', '-').replace(' ', '-')
        )
        self.iso_url = section['iso_url']
        self.checksum_url = section['checksum_url']

    def __repr__(self):
        return f"<OSDefinition id={self.id}>"


class Plugin:
    """Represents a single feature plugin loaded from an INI file."""

    def __init__(self, path: Path):
        self.path = path
        self.name = path.name
        self.meta = {}
        self.prompts = {}       # {field: {type, label, default}}
        self.packages = []
        self.packages_remove = []
        self.post = ""
        self._load(path)

    def _load(self, path: Path):
        raw_text = path.read_text(encoding='utf-8')

        # Read [post] section from raw text BEFORE configparser sees it.
        # The [post] content may contain INI-style headers (e.g. [General])
        # inside heredocs, which would confuse configparser.
        self.post = self._read_section_raw_from_text(raw_text, 'post')

        # Strip [post] section so configparser won't choke on its content.
        clean_text = self._strip_section(raw_text, 'post')

        config = configparser.ConfigParser(allow_no_value=True)
        config.read_string(clean_text)

        if 'meta' in config:
            self.meta = dict(config['meta'])

        if 'prompts' in config:
            self._parse_prompts(dict(config['prompts']))

        if 'packages' in config:
            for key in config['packages']:
                if key:
                    self.packages.append(key)

        if 'packages.remove' in config:
            for key in config['packages.remove']:
                if key:
                    self.packages_remove.append(key)

    # Known plugin section headers — only these are treated as section boundaries.
    # This prevents heredoc content like [General] or [Service] from being
    # mistaken for INI section headers during parsing.
    _PLUGIN_SECTIONS = frozenset([
        '[meta]', '[prompts]', '[packages]', '[packages.remove]', '[post]'
    ])

    def _is_plugin_section(self, line: str) -> bool:
        return line.strip().lower() in self._PLUGIN_SECTIONS

    def _read_section_raw_from_text(self, text: str, section_name: str) -> str:
        """Read a section's content from raw text preserving exact formatting.
        Only known plugin section headers are treated as boundaries."""
        lines = text.splitlines()
        in_section = False
        result = []
        header = f'[{section_name}]'
        for line in lines:
            if line.strip().lower() == header:
                in_section = True
                continue
            if in_section:
                if self._is_plugin_section(line):
                    break
                result.append(line)
        return '\n'.join(result).strip()

    def _strip_section(self, text: str, section_name: str) -> str:
        """Remove a section and all its content from raw INI text.
        Only known plugin section headers are treated as boundaries."""
        lines = text.splitlines()
        result = []
        in_section = False
        header = f'[{section_name}]'
        for line in lines:
            if line.strip().lower() == header:
                in_section = True
                continue
            if in_section:
                if self._is_plugin_section(line):
                    in_section = False
                    result.append(line)
                # else: skip — part of the stripped section
            else:
                result.append(line)
        return '\n'.join(result)

    def _parse_prompts(self, raw: dict):
        """Convert flat 'field.attr = value' entries into structured dict."""
        fields = {}
        for key, value in raw.items():
            if '.' in key:
                field, attr = key.split('.', 1)
                fields.setdefault(field, {})[attr] = value or ''
        self.prompts = fields

    # --- Convenience properties ---

    @property
    def label(self) -> str:
        return self.meta.get('label', self.name)

    @property
    def description(self) -> str:
        return self.meta.get('description', '')

    @property
    def check(self) -> bool:
        return self.meta.get('check', 'false').lower() == 'true'

    @property
    def default(self) -> bool:
        """Whether this plugin is pre-selected in the checkbox UI."""
        return self.meta.get('default', 'false').lower() == 'true'

    @property
    def order(self) -> int:
        return int(self.meta.get('order', '999'))

    @property
    def image_size(self):
        val = self.meta.get('image_size', '').strip()
        if not val:
            return None
        return int(val)

    @property
    def supported_os(self):
        """List of supported OS ids, or None meaning all OSes."""
        val = self.meta.get('supported_os', '').strip()
        if not val:
            return None
        return [s.strip() for s in val.split(',')]

    @property
    def requires(self) -> list:
        val = self.meta.get('requires', '').strip()
        if not val:
            return []
        return [s.strip() for s in val.split(',')]

    def supports_os(self, os_id: str) -> bool:
        if self.supported_os is None:
            return True
        return os_id in self.supported_os

    def __repr__(self):
        return f"<Plugin name={self.name} order={self.order}>"


# ---------------------------------------------------------------------------
# Plugin engine
# ---------------------------------------------------------------------------

class PluginEngine:
    """Loads plugins, manages selection, resolves dependencies, assembles KS."""

    def __init__(self, script_dir: Path):
        self.script_dir = script_dir
        self.plugins_dir = script_dir / 'plugins'
        self.selected_os: OSDefinition = None
        self.selected_plugins: list = []
        # prompt_values: merged flat dict of all collected prompt answers
        self.prompt_values: dict = {}
        self.global_vars: dict = {}
        self.debug: bool = False

    # --- Loading ---

    def load_os_definitions(self) -> list:
        os_dir = self.plugins_dir / 'os'
        if not os_dir.exists():
            return []
        defs = []
        for osdefine in sorted(os_dir.glob('*/osdefine')):
            try:
                defs.append(OSDefinition(osdefine))
            except Exception as e:
                print(f"Warning: Failed to load {osdefine}: {e}")
        return defs

    def load_feature_plugins(self, os_id: str) -> list:
        features_dir = self.plugins_dir / 'features'
        if not features_dir.exists():
            return []
        plugins = []
        for path in sorted(features_dir.rglob('*')):
            if path.is_file():
                try:
                    p = Plugin(path)
                    if p.supports_os(os_id):
                        plugins.append(p)
                except Exception as e:
                    print(f"Warning: Failed to load plugin {path}: {e}")
        return plugins

    # --- Selection UI ---

    def select_os(self) -> OSDefinition:
        os_defs = self.load_os_definitions()
        if not os_defs:
            print("Error: No OS definitions found in plugins/os/")
            sys.exit(1)

        items = [{'label': od.display_name, 'description': None} for od in os_defs]
        idx = tui_radio(items, title="Select target OS:")
        return os_defs[idx]

    def select_plugins(self, all_plugins: list) -> list:
        """Present check=true plugins via TUI checkbox selector."""
        silent = [p for p in all_plugins if not p.check]
        selectable = [p for p in all_plugins if p.check]

        if not selectable:
            return silent

        items = [
            {
                'name': p.name,
                'label': p.label,
                'description': p.description,
                'selected': p.default,
            }
            for p in selectable
        ]

        dependencies = {
            p.name: [req for req in p.requires if any(sp.name == req for sp in selectable)]
            for p in selectable
        }

        chosen_indices = tui_checkbox(
            items,
            title="Select optional features:",
            dependencies=dependencies,
        )
        selected = [selectable[i] for i in chosen_indices]
        return silent + selected

    # --- Dependency resolution ---

    def resolve_dependencies(self, selected: list, all_plugins: list) -> list:
        plugin_map = {p.name: p for p in all_plugins}
        result = list(selected)
        selected_names = {p.name for p in selected}

        changed = True
        while changed:
            changed = False
            for plugin in list(result):
                for req in plugin.requires:
                    if req not in selected_names:
                        if req in plugin_map:
                            dep = plugin_map[req]
                            result.append(dep)
                            selected_names.add(req)
                            changed = True
                            print(f"  Auto-adding dependency: {dep.label} (required by {plugin.label})")
                        else:
                            print(f"Warning: Required plugin '{req}' not found (needed by {plugin.name})")
        return result

    # --- Prompt collection ---

    def collect_prompts(self, plugin: Plugin) -> dict:
        """Interactively collect values for a plugin's [prompts] section."""
        values = {}
        if not plugin.prompts:
            return values

        selected_plugin_names = {p.name for p in self.selected_plugins}

        print(f"\n  [{plugin.label}] Configuration:")
        for field, attrs in plugin.prompts.items():
            when_plugin = attrs.get('when_plugin', '').strip()
            if when_plugin and when_plugin not in selected_plugin_names:
                continue

            ptype = attrs.get('type', 'text')
            label = attrs.get('label', field)
            default = attrs.get('default', '')

            if ptype == 'boolean':
                default_yn = 'Y/n' if default.lower() == 'true' else 'y/N'
                answer = input(f"    {label}? ({default_yn}): ").strip().lower()
                values[field] = (default.lower() == 'true') if answer == '' else (answer == 'y')

            elif ptype == 'password':
                while True:
                    p1 = getpass.getpass(f"    {label}: ")
                    if not p1:
                        if default:
                            values[field] = default
                            break
                        print("    Password cannot be empty.")
                        continue
                    p2 = getpass.getpass(f"    Confirm {label}: ")
                    if p1 != p2:
                        print("    Passwords do not match.")
                        continue
                    values[field] = p1
                    break

            else:  # text
                prompt = f"    {label}"
                if default:
                    prompt += f" [{default}]"
                prompt += ": "
                answer = input(prompt).strip()
                values[field] = answer if answer else default

        return values

    def collect_all_prompts(self):
        """Collect prompts for all selected plugins, merging into shared namespace."""
        for plugin in self.selected_plugins:
            if plugin.prompts:
                values = self.collect_prompts(plugin)
                # Merge into shared namespace (later plugins can override)
                self.prompt_values.update(values)

    # --- Token substitution ---

    def substitute_tokens(self, text: str) -> str:
        """Replace ${var} tokens using merged prompt values and global vars."""
        values = {}
        values.update(self.global_vars)
        values.update(self.prompt_values)
        for plugin in self.selected_plugins:
            values[plugin.name] = True

        # Handle ${if_varname}...${endif_varname} inline conditionals
        def replace_conditional(m):
            varname = m.group(1)
            content = m.group(2)
            val = values.get(varname, False)
            return content if val else ''

        conditional_pattern = r'\$\{if_([\w-]+)\}(.*?)\$\{endif_\1\}'
        while True:
            new_text = re.sub(
                conditional_pattern,
                replace_conditional,
                text,
                flags=re.DOTALL
            )
            if new_text == text:
                break
            text = new_text

        # Replace ${var} tokens
        def replace_var(m):
            varname = m.group(1)
            return str(values.get(varname, m.group(0)))

        return re.sub(r'\$\{([\w-]+)\}', replace_var, text)

    # --- Kickstart assembly ---

    def assemble_kickstart(self, is_uefi: bool, os_version: int) -> str:
        lines = []

        # Header
        uefi_str = 'UEFI' if is_uefi else 'MBR'
        lines.append(f"#version=RHEL{os_version} {uefi_str}")
        lines.append("")

        # Language: default en_US.UTF-8; locale is set by language plugins in %post
        lines.append("lang en_US.UTF-8")
        lines.append("")

        # Keyboard: default us; layout is set by language plugins in %post
        lines.append("keyboard us")
        lines.append("")
        # Timezone: default UTC; set by language plugins in %post
        lines.append("timezone UTC --utc")
        lines.append("")

        # Root password
        root_pw = self.global_vars.get('root_password', 'password')
        lines.append(f"rootpw --plaintext {root_pw}")
        lines.append("")

        # Network / SELinux
        lines.append("network --bootproto=dhcp --device=link --activate")
        lines.append("")
        lines.append("selinux --permissive")
        lines.append("")

        # auth (Rocky <= 9 only)
        if os_version <= 9:
            lines.append("auth --useshadow --passalgo=sha512")
            lines.append("")

        # Disk partitioning
        if is_uefi:
            lines.append("bootloader --location=none")
            lines.append("clearpart --all --initlabel")
            lines.append("reqpart")
            lines.append("part / --size=6656 --grow")
        else:
            lines.append("clearpart --all --initlabel")
            lines.append('part / --fstype="xfs" --grow --size=8192')
            lines.append("bootloader --location=mbr")
        lines.append("")

        # %packages
        lines.append("%packages")
        if is_uefi:
            lines.extend(["shim", "grub2", "grub2-efi", "grub2-efi-*-cdboot", "efibootmgr"])

        for plugin in self.selected_plugins:
            for pkg in plugin.packages:
                lines.append(pkg)
        for plugin in self.selected_plugins:
            for pkg in plugin.packages_remove:
                lines.append(pkg)

        lines.append("%end")
        lines.append("")

        # %post
        lines.append("%post --log=/root/ks-post.log")
        lines.append("")
        lines.append("df -h")
        lines.append("")

        for plugin in self.selected_plugins:
            if plugin.post:
                lines.append(f"##############################################################")
                lines.append(f"### Plugin: {plugin.name}")
                lines.append(f"##############################################################")
                lines.append(self.substitute_tokens(plugin.post))
                lines.append("")

        lines.append("df -h")
        lines.append("")

        lines.append("%end")
        lines.append("shutdown")
        lines.append("")

        return '\n'.join(lines)


# ---------------------------------------------------------------------------
# Main builder
# ---------------------------------------------------------------------------

class ISOBuilder2:

    def __init__(self):
        self.script_dir = Path(__file__).parent.resolve()
        self.engine = PluginEngine(self.script_dir)
        self.iso_path = None
        self.iso_url = None
        self.checksum_url = None
        self.bootmode = None
        self.debug = False
        self.view_kickstart = False
        self.os_version = None

    def display_banner(self):
        print("=" * 70)
        print("  Rocky Linux Bootable ISO Builder v2 (Plugin Edition)")
        print("=" * 70)
        print()

    def check_platform(self):
        print("[1/7] Checking platform compatibility...")
        try:
            content = Path('/etc/os-release').read_text()
            m = re.search(r'PLATFORM_ID="([^"]+)"', content)
            if not m:
                print("Error: Cannot determine platform information")
                sys.exit(1)
            platform = m.group(1)
            if platform not in ["platform:el8", "platform:el9", "platform:el10"]:
                print(f"Error: Unsupported platform: {platform}")
                sys.exit(1)
            print(f"✓ Platform: {platform}")
            print()
        except FileNotFoundError:
            print("Error: /etc/os-release not found")
            sys.exit(1)

    def check_kvm_module(self):
        print("[2/7] Checking KVM module...")
        result = subprocess.run(['lsmod'], capture_output=True, text=True)
        if 'kvm' not in result.stdout:
            print("Error: KVM kernel module is not loaded.")
            sys.exit(1)
        print("✓ KVM module loaded")
        print()

    def check_required_packages(self):
        print("[3/7] Checking required packages...")
        required = ['qemu-kvm', 'lorax', 'lorax-lmc-virt', 'wget', 'isomd5sum', 'syslinux-nonlinux']
        missing = [
            p for p in required
            if subprocess.run(['rpm', '-q', p],
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL).returncode != 0
        ]
        if missing:
            print("Error: Missing packages:")
            for p in missing:
                print(f"  - {p}")
            sys.exit(1)
        print("✓ All required packages installed")
        print()

    def select_os_and_plugins(self):
        print("[4/7] Select OS and features...")
        print()

        engine = self.engine

        # OS selection
        selected_os = engine.select_os()
        engine.selected_os = selected_os
        self.iso_url = selected_os.iso_url
        self.checksum_url = selected_os.checksum_url

        m = re.search(r'\d+', selected_os.id)
        self.os_version = int(m.group()) if m else 9
        self.iso_path = self.script_dir / 'isos' / Path(selected_os.iso_url).name

        print(f"\n✓ Selected: {selected_os.display_name}")
        print()

        # Load plugins for selected OS
        all_plugins = engine.load_feature_plugins(selected_os.id)

        # User selection (check=true plugins)
        selected = engine.select_plugins(all_plugins)

        # Dependency resolution
        print()
        selected = engine.resolve_dependencies(selected, all_plugins)

        # Sort by order, then filename
        selected.sort(key=lambda p: (p.order, p.name))
        engine.selected_plugins = selected

        print(f"\n✓ {len(selected)} plugin(s) will be applied:")
        for p in selected:
            print(f"    [{p.order:>3}] {p.name}")
        print()

    def collect_all_prompts(self):
        print("Plugin configuration:")
        self.engine.collect_all_prompts()
        print()

    def select_bootmode(self):
        bootmodes = [
            {'label': 'uefi', 'description': 'UEFI boot'},
            {'label': 'mbr',  'description': 'CSM/BIOS (MBR) boot'},
        ]
        idx = tui_radio(bootmodes, title="Select boot mode:")
        self.bootmode = bootmodes[idx]['label']
        print(f"✓ Boot mode: {self.bootmode}")
        print()

    def input_root_password(self):
        print("[6/7] Set root password:")
        print()
        while True:
            p1 = getpass.getpass("Enter password: ")
            if not p1:
                print("Password cannot be empty.")
                continue
            p2 = getpass.getpass("Confirm password: ")
            if p1 != p2:
                print("Passwords do not match.")
                continue
            self.engine.global_vars['root_password'] = p1
            print("✓ Root password set")
            print()
            break

    def download_iso_if_needed(self):
        print("[7/7] Checking ISO file...")
        if self.iso_path.exists():
            print(f"✓ ISO already exists: {self.iso_path}")
            print()
            if self._verify_checksum():
                return
            print("Deleting corrupted ISO and re-downloading...")
            self.iso_path.unlink(missing_ok=True)

        print("Downloading ISO...")
        self.iso_path.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(['wget', '-c', '-P', str(self.iso_path.parent), self.iso_url])
        if result.returncode != 0:
            print("Error: Download failed.")
            sys.exit(1)
        print(f"✓ ISO downloaded: {self.iso_path}")
        print()

        if not self._verify_checksum():
            print("Error: Checksum verification failed.")
            self.iso_path.unlink(missing_ok=True)
            sys.exit(1)

    def _verify_checksum(self) -> bool:
        print("Verifying checksum...")
        checksum_path = self.iso_path.with_suffix('.iso.CHECKSUM')
        result = subprocess.run(['wget', '-q', '-O', str(checksum_path), self.checksum_url])
        if result.returncode != 0:
            print("Warning: Failed to download CHECKSUM file. Skipping.")
            return True

        checksum_text = checksum_path.read_text()
        checksum_path.unlink(missing_ok=True)

        expected_hash = None
        for line in checksum_text.splitlines():
            if 'SHA256' in line and self.iso_path.name in line:
                m = re.search(r'=\s*([0-9a-fA-F]{64})', line)
                if m:
                    expected_hash = m.group(1).lower()
                    break

        if not expected_hash:
            print("Warning: SHA256 hash not found. Skipping verification.")
            return True

        print("Computing SHA256 (this may take a moment)...")
        sha256 = hashlib.sha256()
        with open(self.iso_path, 'rb') as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b''):
                sha256.update(chunk)

        if sha256.hexdigest() != expected_hash:
            print("Warning: Checksum mismatch!")
            return False

        print("✓ Checksum verified")
        print()
        return True

    def cleanup_directories(self):
        print("Cleaning up build directories...")

        build_iso_dir = self.script_dir / 'build-iso'
        if build_iso_dir.exists():
            result = subprocess.run(['sudo', 'rm', '-rf', str(build_iso_dir)])
            if result.returncode != 0:
                print(f"Error: Failed to remove {build_iso_dir}")
                sys.exit(1)

        tmp_dir = self.script_dir / 'tmp'
        if tmp_dir.exists():
            for item in tmp_dir.iterdir():
                if item.name != '.gitkeep':
                    result = subprocess.run(['sudo', 'rm', '-rf', str(item)])
                    if result.returncode != 0:
                        print(f"Error: Failed to remove {item}")
                        sys.exit(1)

        print("✓ Directories cleaned")

    def generate_kickstart(self) -> str:
        if not (self.script_dir / 'scripts').exists():
            print("Error: scripts/ directory not found.")
            sys.exit(1)

        is_uefi = self.bootmode == 'uefi'

        print("Generating kickstart from plugins...")
        self.engine.debug = self.debug
        return self.engine.assemble_kickstart(is_uefi, self.os_version)

    def print_kickstart(self, ks_content: str):
        print("=" * 70)
        print("  Generated kickstart:")
        print("=" * 70)
        for i, line in enumerate(ks_content.splitlines(), 1):
            print(f"{i:4}: {line}")
        print("=" * 70)
        print()

    def build_iso(self):
        print("\nBuilding ISO image...")
        print()

        is_uefi = self.bootmode == 'uefi'
        iso_name = f'{self.engine.selected_os.iso_name_prefix}-liveboot-{self.bootmode}-x86_64.iso'
        ks_content = self.generate_kickstart()

        tmp_dir = self.script_dir / 'tmp'
        tmp_dir.mkdir(parents=True, exist_ok=True)
        fd, temp_ks = tempfile.mkstemp(suffix='.ks', prefix='generated_', dir=tmp_dir)
        with os.fdopen(fd, 'w') as f:
            f.write(ks_content)

        if self.debug:
            print("  [DEBUG]")
            self.print_kickstart(ks_content)

        try:
            output_iso = self.script_dir / 'build-iso' / iso_name
            if output_iso.exists():
                answer = input(f"'{iso_name}' already exists. Overwrite? (y/N): ").strip().lower()
                if answer != 'y':
                    print("Aborted.")
                    sys.exit(0)

            image_size = max(
                [8704] + [p.image_size for p in self.engine.selected_plugins if p.image_size is not None]
            )
            extra_opts = ['--virt-uefi'] if is_uefi else []
            cmd = [
                'sudo', 'livemedia-creator',
                '--make-iso',
                f'--ks={temp_ks}',
                f'--iso={self.iso_path}',
                f'--iso-name={iso_name}',
                '--iso-only',
                f'--resultdir={self.script_dir}/build-iso',
                f'--logfile={self.script_dir}/logs/livemedia-creator.log',
                '--project=Rocky Linux',
                f'--releasever={self.os_version}',
                f'--tmp={self.script_dir}/tmp',
                f'--image-size={image_size}',
                f'--lorax-templates={self.script_dir}/tmpl',
            ] + extra_opts

            print("Running livemedia-creator (this may take a while)...")
            print(f"Log: {self.script_dir}/logs/livemedia-creator.log")
            print()
            result = subprocess.run(cmd)

            if result.returncode != 0:
                print("Error: livemedia-creator failed.")
                sys.exit(1)

            print("Embedding ISO checksum...")
            subprocess.run(['sudo', 'implantisomd5', '--force', str(output_iso)])

            print()
            print("=" * 70)
            print("✓ ISO created successfully!")
            print("=" * 70)
            print()
            print(f"ISO:       {output_iso}")
            print(f"Boot mode: {self.bootmode}")
            print()
            print("SECURITY REMINDER:")
            print("  - The ISO uses the custom root password you provided")
            print("  - SELinux is in permissive mode")
            print("  - This ISO is intended for temporary use only")
            print()

        finally:
            if os.path.exists(temp_ks):
                os.unlink(temp_ks)

    def run(self):
        try:
            self.display_banner()
            self.check_platform()
            self.check_kvm_module()
            self.check_required_packages()
            self.select_os_and_plugins()
            self.collect_all_prompts()
            self.input_root_password()
            self.select_bootmode()
            if self.view_kickstart:
                ks_content = self.generate_kickstart()
                self.print_kickstart(ks_content)
                return
            self.download_iso_if_needed()
            self.cleanup_directories()
            self.build_iso()
        except KeyboardInterrupt:
            print("\n\nOperation cancelled.")
            sys.exit(1)
        except Exception as e:
            print(f"\nUnexpected error: {e}")
            raise


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Rocky Linux Bootable ISO Builder v2 (Plugin Edition)'
    )
    parser.add_argument('--debug', action='store_true',
                        help='Debug mode: show generated kickstart and preserve logs inside ISO')
    parser.add_argument('--view-kickstart', action='store_true',
                        help='Generate and print the kickstart only; skip ISO download and build')
    args = parser.parse_args()

    if os.geteuid() == 0:
        print("Warning: This script should not be run as root initially.")
        print("It will request sudo privileges when needed.")
        print()
        if input("Continue anyway? (y/N): ").strip().lower() != 'y':
            sys.exit(0)

    builder = ISOBuilder2()
    builder.debug = args.debug
    builder.view_kickstart = args.view_kickstart
    builder.run()


if __name__ == "__main__":
    main()
