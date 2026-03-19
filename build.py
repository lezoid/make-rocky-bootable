#!/usr/bin/env python3
"""
Rocky Linux Bootable ISO Builder v2 (Plugin Edition)
Reads plugins from plugins/ directory to dynamically generate kickstart files.
"""

import configparser
import argparse
import hashlib
import os
import shutil
import sys
import subprocess
import getpass
import re
import tempfile
import tty
import termios
from pathlib import Path


# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------

def detect_language() -> str:
    """Detect user language from environment variables (LANGUAGE > LC_ALL > LANG).
    Returns a two-letter language code (e.g. 'ja', 'en')."""
    for var in ('LANGUAGE', 'LC_ALL', 'LANG'):
        val = os.environ.get(var, '').strip()
        if val:
            lang = val.split('_')[0].split('.')[0].lower()
            if lang and lang not in ('c', 'posix'):
                return lang
    return 'en'


# ---------------------------------------------------------------------------
# Localized UI strings
# ---------------------------------------------------------------------------

_LANG_UI = {
    'ja': {
        # TUI
        'select_os_title':          'ターゲットOSを選択:',
        'select_features_title':    'オプション機能を選択:',
        'select_boot_title':        'ブートモードを選択:',
        'select_liveboot_title':    'デフォルト起動モードを選択:',
        'liveboot_normal':          '通常起動',
        'liveboot_normal_desc':     'ライブイメージから直接起動します',
        'liveboot_ram':             'RAM展開起動',
        'liveboot_ram_desc':        '起動前にイメージ全体をRAMに展開します。起動後にDVDを取り出せます。多くのメモリが必要です。',
        'ok_liveboot':              '✓ デフォルト起動モード: {0}',
        'radio_hint':               '↑↓ 移動   Enter: 確定',
        'checkbox_hint':            '↑↓ 移動   Space: 切替   Enter: 確定',
        # Prompts
        'boolean_default':          'デフォルト: {0}',
        'password_empty':           'パスワードを入力してください。',
        'password_confirm':         '{0}を確認: ',
        'password_mismatch':        'パスワードが一致しません。',
        'err_invalid_username':     'ユーザー名が無効です。英小文字・数字・ハイフン・アンダースコアのみ使用できます。',
        # Dependency resolution
        'dependency_auto_add':      '  依存プラグインを自動追加: {0} ({1} が必要)',
        'dependency_not_found':     "警告: 依存プラグイン '{0}' が見つかりません ({1} が必要)",
        # Root password
        'root_password_title':      '[6/7] rootパスワードを設定:',
        'root_enter_password':      'rootパスワードを入力: ',
        'root_confirm_password':    'rootパスワードを確認: ',
        'root_password_empty':      'パスワードを入力してください。',
        'root_password_mismatch':   'パスワードが一致しません。',
        'root_password_set':        'rootパスワードを設定しました',
        # Step headers
        'step1':                    '[1/7] プラットフォームの互換性を確認中...',
        'step2':                    '[2/7] KVMモジュールを確認中...',
        'step3':                    '[3/7] 必要パッケージを確認中...',
        'step4':                    '[4/7] OSとプラグインを選択...',
        'step7':                    '[7/7] ISOファイルを確認中...',
        'plugin_config':            'プラグイン設定:',
        # OK messages (use .format(value) on result)
        'ok_platform':              '✓ プラットフォーム: {0}',
        'ok_kvm':                   '✓ KVMモジュール確認済み',
        'ok_packages':              '✓ 必要パッケージがすべてインストール済み',
        'ok_selected_os':           '\n✓ 選択: {0}',
        'ok_plugins_applied':       '\n✓ {0} 個のプラグインが適用されます:',
        'ok_bootmode':              '✓ ブートモード: {0}',
        'ok_iso_exists':            '✓ ISOが存在します: {0}',
        'ok_iso_downloaded':        '✓ ISOダウンロード完了: {0}',
        'ok_checksum':              '✓ チェックサム確認済み',
        'ok_dirs_cleaned':          '✓ ディレクトリのクリーンアップ完了',
        'ok_iso_created':           '✓ ISOの作成に成功しました!',
        # Process messages
        'downloading_iso':          'ISOをダウンロード中...',
        'verifying_checksum':       'チェックサムを確認中...',
        'computing_sha256':         'SHA256を計算中 (しばらくかかります)...',
        'cleaning_dirs':            'ビルドディレクトリをクリーンアップ中...',
        'generating_ks':            'プラグインからkickstartを生成中...',
        'building_iso':             '\nISOイメージをビルド中...',
        'building_iso_wait1':       '  数十分から1時間程度かかります。',
        'building_iso_wait2':       '  ビルドが完了するまでお待ちください。',
        'running_livemedia':        'livemedia-creatorを実行中 (しばらく時間がかかります)...',
        'log_file':                 'ログ: {0}',
        'embedding_checksum':       'ISOチェックサムを埋め込み中...',
        'deleting_corrupted':       '破損したISOを削除して再ダウンロードします...',
        # Result / summary
        'iso_path_label':           'ISO:       {0}',
        'bootmode_label':           'ブートモード: {0}',
        'security_reminder':        'セキュリティ注意事項:',
        'security_1':               '  - このISOには設定したrootパスワードが含まれています',
        'security_2':               '  - SELinuxは permissive モードです',
        'security_3':               '  - このISOは一時的な使用を目的としています',
        # Errors / warnings
        'err_platform':             'エラー: プラットフォーム情報を取得できません',
        'err_unsupported':          'エラー: サポートされていないプラットフォーム: {0}',
        'err_os_release':           'エラー: /etc/os-release が見つかりません',
        'err_kvm':                  'エラー: KVMカーネルモジュールがロードされていません。',
        'err_missing_packages':     'エラー: 不足しているパッケージ:',
        'err_download':             'エラー: ダウンロードに失敗しました。',
        'err_checksum':             'エラー: チェックサムの検証に失敗しました。',
        'err_remove_dir':           'エラー: {0} の削除に失敗しました',
        'err_remove_dir_hint':      'ヒント: {0} 配下にマウントが残っている可能性があります。"mount | grep {0}" で確認し、手動でアンマウントしてください。',
        'err_scripts_dir':          'エラー: scripts/ ディレクトリが見つかりません。',
        'err_livemedia':            'エラー: livemedia-creatorが失敗しました。',
        'warn_checksum_dl':         '警告: CHECKSUMファイルのダウンロードに失敗しました。スキップします。',
        'warn_no_sha256':           '警告: SHA256ハッシュが見つかりません。検証をスキップします。',
        'warn_checksum_mismatch':   '警告: チェックサムが一致しません!',
        'overwrite_prompt':         "'{0}' はすでに存在します。上書きしますか? (y/N): ",
        'aborted':                  '中止しました。',
    }
}


def _ui(lang: str, key: str, default: str) -> str:
    """Return a localized UI string, falling back to default."""
    return _LANG_UI.get(lang, {}).get(key, default)


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


def tui_radio(items: list, title: str = "Select one",
              hint: str = "↑↓ Move   Enter: Confirm") -> int:
    """Interactive TUI radio button selector (single selection).

    Args:
        items: list of dicts with keys 'label', 'description'
        hint:  operation hint string shown below the title
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
        lines.append(f"{DIM}  {hint}{RESET}")
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


def tui_checkbox(items: list, title: str = "Select options",
                 hint: str = "↑↓ Move   Space: Toggle   Enter: Confirm",
                 dependencies: dict = None) -> list:
    """Interactive TUI checkbox selector.

    Args:
        items:        list of dicts with keys 'label', 'description', 'selected'
        hint:         operation hint string shown below the title
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
        lines.append(f"{DIM}  {hint}{RESET}")
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
        self.path = path          # plugin directory
        self.name = path.name
        self.meta = {}
        self.prompts = {}       # {field: {type, label, default}}
        self.packages = []
        self.packages_remove = []
        self.post = ""
        self._load(path / 'metadata.ini')

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
    def plugin_iso_dir(self) -> bool:
        """Whether this plugin has files to copy into the ISO scripts directory."""
        return self.meta.get('plugin_iso_dir', 'false').lower() == 'true'

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

    def requires_for_os(self, os_id: str) -> list:
        result = list(self.requires)
        os_specific = self.meta.get(f'requires.{os_id}', '').strip()
        if os_specific:
            for item in os_specific.split(','):
                req = item.strip()
                if req and req not in result:
                    result.append(req)
        return result

    def supports_os(self, os_id: str) -> bool:
        if self.supported_os is None:
            return True
        return os_id in self.supported_os

    # --- Localized accessors ---

    def get_label(self, lang: str = 'en') -> str:
        """Return label, preferring the localized version for `lang`."""
        if lang != 'en':
            localized = self.meta.get(f'label.{lang}')
            if localized:
                return localized
        return self.label

    def get_description(self, lang: str = 'en') -> str:
        """Return description, preferring the localized version for `lang`."""
        if lang != 'en':
            localized = self.meta.get(f'description.{lang}')
            if localized:
                return localized
        return self.description

    def get_prompt_label(self, field: str, lang: str = 'en') -> str:
        """Return the prompt label for `field`, preferring the localized version."""
        attrs = self.prompts.get(field, {})
        if lang != 'en':
            localized = attrs.get(f'label.{lang}')
            if localized:
                return localized
        return attrs.get('label', field)

    def get_prompt_note(self, field: str, lang: str = 'en') -> str:
        """Return the prompt note for `field`, preferring the localized version."""
        attrs = self.prompts.get(field, {})
        if lang != 'en':
            localized = attrs.get(f'note.{lang}')
            if localized:
                return localized
        return attrs.get('note', '')

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
        self.lang: str = detect_language()

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
        for meta_path in sorted(features_dir.rglob('metadata.ini')):
            plugin_dir = meta_path.parent
            try:
                p = Plugin(plugin_dir)
                if p.supports_os(os_id):
                    plugins.append(p)
            except Exception as e:
                print(f"Warning: Failed to load plugin {plugin_dir}: {e}")
        return plugins

    # --- Selection UI ---

    def select_os(self) -> OSDefinition:
        os_defs = self.load_os_definitions()
        if not os_defs:
            print("Error: No OS definitions found in plugins/os/")
            sys.exit(1)

        items = [{'label': od.display_name, 'description': None} for od in os_defs]
        title = _ui(self.lang, 'select_os_title', 'Select target OS:')
        hint  = _ui(self.lang, 'radio_hint', '↑↓ Move   Enter: Confirm')
        idx = tui_radio(items, title=title, hint=hint)
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
                'label': p.get_label(self.lang),
                'description': p.get_description(self.lang),
                'selected': p.default,
            }
            for p in selectable
        ]

        dependencies = {
            p.name: [req for req in p.requires_for_os(self.selected_os.id) if any(sp.name == req for sp in selectable)]
            for p in selectable
        }

        title = _ui(self.lang, 'select_features_title', 'Select optional features:')
        hint  = _ui(self.lang, 'checkbox_hint', '↑↓ Move   Space: Toggle   Enter: Confirm')
        chosen_indices = tui_checkbox(
            items,
            title=title,
            hint=hint,
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
                for req in plugin.requires_for_os(self.selected_os.id):
                    if req not in selected_names:
                        if req in plugin_map:
                            dep = plugin_map[req]
                            result.append(dep)
                            selected_names.add(req)
                            changed = True
                            print(_ui(self.lang, 'dependency_auto_add',
                                      '  Auto-adding dependency: {0} (required by {1})').format(dep.label, plugin.label))
                        else:
                            print(_ui(self.lang, 'dependency_not_found',
                                      "Warning: Required plugin '{0}' not found (needed by {1})").format(req, plugin.name))
        return result

    # --- Prompt collection ---

    def collect_prompts(self, plugin: Plugin) -> dict:
        """Interactively collect values for a plugin's [prompts] section."""
        values = {}
        if not plugin.prompts:
            return values

        selected_plugin_names = {p.name for p in self.selected_plugins}

        print(f"\n  [{plugin.get_label(self.lang)}] Configuration:")
        for field, attrs in plugin.prompts.items():
            when_plugin = attrs.get('when_plugin', '').strip()
            if when_plugin and when_plugin not in selected_plugin_names:
                continue

            ptype = attrs.get('type', 'text')
            label = plugin.get_prompt_label(field, self.lang)
            # Expand already-collected values in the label (e.g. ${name})
            for k, v in values.items():
                label = label.replace(f'${{{k}}}', str(v))
            default = attrs.get('default', '')

            note = plugin.get_prompt_note(field, self.lang)
            if note:
                print(f"      ※ {note}")

            if ptype == 'boolean':
                default_val = 'y' if default.lower() == 'true' else 'n'
                default_label = _ui(self.lang, 'boolean_default', 'default: {0}').format(default_val)
                answer = input(f"    {label} (y/n) [{default_label}]: ").strip().lower()
                values[field] = (default.lower() == 'true') if answer == '' else (answer == 'y')

            elif ptype == 'password':
                while True:
                    p1 = getpass.getpass(f"    {label}: ")
                    if not p1:
                        if default:
                            values[field] = default
                            break
                        print(f"    {_ui(self.lang, 'password_empty', 'Password cannot be empty.')}")
                        continue
                    confirm_label = _ui(self.lang, 'password_confirm', 'Confirm {0}: ').format(label)
                    p2 = getpass.getpass(f"    {confirm_label}")
                    if p1 != p2:
                        print(f"    {_ui(self.lang, 'password_mismatch', 'Passwords do not match.')}")
                        continue
                    values[field] = p1
                    break

            else:  # text
                validate = attrs.get('rule', '').strip()
                while True:
                    prompt = f"    {label}"
                    if default:
                        prompt += f" [{default}]"
                    prompt += ": "
                    answer = input(prompt).strip()
                    value = answer if answer else default
                    if validate == 'linux_username' and value:
                        if not re.match(r'^[a-z_][a-z0-9_.-]{0,30}$', value):
                            print(f"    {_ui(self.lang, 'err_invalid_username', 'Invalid username. Use lowercase letters, digits, hyphens, underscores only.')}")
                            continue
                    values[field] = value
                    break

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

        # auth (Rocky 7 and earlier only; removed in Rocky 8+)
        if os_version < 8:
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
        lang = self.engine.lang
        print(_ui(lang, 'step1', '[1/7] Checking platform compatibility...'))
        try:
            content = Path('/etc/os-release').read_text()
            m = re.search(r'PLATFORM_ID="([^"]+)"', content)
            if not m:
                print(_ui(lang, 'err_platform', 'Error: Cannot determine platform information'))
                sys.exit(1)
            platform = m.group(1)
            if platform not in ["platform:el8", "platform:el9", "platform:el10"]:
                print(_ui(lang, 'err_unsupported', 'Error: Unsupported platform: {0}').format(platform))
                sys.exit(1)
            print(_ui(lang, 'ok_platform', '✓ Platform: {0}').format(platform))
            print()
        except FileNotFoundError:
            print(_ui(lang, 'err_os_release', 'Error: /etc/os-release not found'))
            sys.exit(1)

    def check_kvm_module(self):
        lang = self.engine.lang
        print(_ui(lang, 'step2', '[2/7] Checking KVM module...'))
        result = subprocess.run(['lsmod'], capture_output=True, text=True)
        if 'kvm' not in result.stdout:
            print(_ui(lang, 'err_kvm', 'Error: KVM kernel module is not loaded.'))
            sys.exit(1)
        print(_ui(lang, 'ok_kvm', '✓ KVM module loaded'))
        print()

    def check_required_packages(self):
        lang = self.engine.lang
        print(_ui(lang, 'step3', '[3/7] Checking required packages...'))
        required = ['qemu-kvm', 'lorax', 'lorax-lmc-virt', 'wget', 'isomd5sum', 'syslinux-nonlinux']
        missing = [
            p for p in required
            if subprocess.run(['rpm', '-q', p],
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL).returncode != 0
        ]
        if missing:
            print(_ui(lang, 'err_missing_packages', 'Error: Missing packages:'))
            for p in missing:
                print(f"  - {p}")
            sys.exit(1)
        print(_ui(lang, 'ok_packages', '✓ All required packages installed'))
        print()

    def select_os_and_plugins(self):
        lang = self.engine.lang
        print(_ui(lang, 'step4', '[4/7] Select OS and features...'))
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

        print(_ui(lang, 'ok_selected_os', '\n✓ Selected: {0}').format(selected_os.display_name))
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

        print(_ui(lang, 'ok_plugins_applied', '\n✓ {0} plugin(s) will be applied:').format(len(selected)))
        for p in selected:
            print(f"    [{p.order:>3}] {p.name}")
        print()

    def collect_all_prompts(self):
        lang = self.engine.lang
        print(_ui(lang, 'plugin_config', 'Plugin configuration:'))
        self.engine.collect_all_prompts()
        print()

    def select_bootmode(self):
        lang = self.engine.lang
        bootmodes = [
            {'label': 'UEFI Boot',            'description': None},
            {'label': 'CSM/BIOS (MBR) Boot',  'description': None},
        ]
        title = _ui(lang, 'select_boot_title', 'Select boot mode:')
        hint  = _ui(lang, 'radio_hint', '↑↓ Move   Enter: Confirm')
        idx = tui_radio(bootmodes, title=title, hint=hint)
        self.bootmode = ['uefi', 'mbr'][idx]
        print(_ui(lang, 'ok_bootmode', '✓ Boot mode: {0}').format(self.bootmode))
        print()

        livemodes = [
            {
                'label':       _ui(lang, 'liveboot_normal', 'Normal Boot'),
                'description': _ui(lang, 'liveboot_normal_desc', 'Boot directly from the live image'),
            },
            {
                'label':       _ui(lang, 'liveboot_ram', 'Load to RAM'),
                'description': _ui(lang, 'liveboot_ram_desc', 'Copy entire image to RAM before booting. DVD can be ejected after boot. Requires extra memory.'),
            },
        ]
        title2 = _ui(lang, 'select_liveboot_title', 'Select default live boot mode:')
        idx2 = tui_radio(livemodes, title=title2, hint=hint)
        self.live_bootmode = ['normal', 'ram'][idx2]
        print(_ui(lang, 'ok_liveboot', '✓ Default live boot mode: {0}').format(self.live_bootmode))
        print()

    def input_root_password(self):
        lang = self.engine.lang
        print(_ui(lang, 'root_password_title', '[6/7] Set root password:'))
        print()
        while True:
            p1 = getpass.getpass(_ui(lang, 'root_enter_password', 'Enter root password: '))
            if not p1:
                print(_ui(lang, 'root_password_empty', 'Password cannot be empty.'))
                continue
            p2 = getpass.getpass(_ui(lang, 'root_confirm_password', 'Confirm root password: '))
            if p1 != p2:
                print(_ui(lang, 'root_password_mismatch', 'Passwords do not match.'))
                continue
            self.engine.global_vars['root_password'] = p1
            print("✓ " + _ui(lang, 'root_password_set', 'Root password set'))
            print()
            break

    def download_iso_if_needed(self):
        lang = self.engine.lang
        print(_ui(lang, 'step7', '[7/7] Checking ISO file...'))
        if self.iso_path.exists():
            print(_ui(lang, 'ok_iso_exists', '✓ ISO already exists: {0}').format(self.iso_path))
            print()
            if self._verify_checksum():
                return
            print(_ui(lang, 'deleting_corrupted', 'Deleting corrupted ISO and re-downloading...'))
            self.iso_path.unlink(missing_ok=True)

        print(_ui(lang, 'downloading_iso', 'Downloading ISO...'))
        self.iso_path.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(['wget', '-c', '-P', str(self.iso_path.parent), self.iso_url])
        if result.returncode != 0:
            print(_ui(lang, 'err_download', 'Error: Download failed.'))
            sys.exit(1)
        print(_ui(lang, 'ok_iso_downloaded', '✓ ISO downloaded: {0}').format(self.iso_path))
        print()

        if not self._verify_checksum():
            print(_ui(lang, 'err_checksum', 'Error: Checksum verification failed.'))
            self.iso_path.unlink(missing_ok=True)
            sys.exit(1)

    def _verify_checksum(self) -> bool:
        lang = self.engine.lang
        print(_ui(lang, 'verifying_checksum', 'Verifying checksum...'))
        checksum_path = self.iso_path.with_suffix('.iso.CHECKSUM')
        result = subprocess.run(['wget', '-q', '-O', str(checksum_path), self.checksum_url])
        if result.returncode != 0:
            print(_ui(lang, 'warn_checksum_dl', 'Warning: Failed to download CHECKSUM file. Skipping.'))
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
            print(_ui(lang, 'warn_no_sha256', 'Warning: SHA256 hash not found. Skipping verification.'))
            return True

        print(_ui(lang, 'computing_sha256', 'Computing SHA256 (this may take a moment)...'))
        sha256 = hashlib.sha256()
        with open(self.iso_path, 'rb') as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b''):
                sha256.update(chunk)

        if sha256.hexdigest() != expected_hash:
            print(_ui(lang, 'warn_checksum_mismatch', 'Warning: Checksum mismatch!'))
            return False

        print(_ui(lang, 'ok_checksum', '✓ Checksum verified'))
        print()
        return True

    def cleanup_directories(self):
        lang = self.engine.lang
        print(_ui(lang, 'cleaning_dirs', 'Cleaning up build directories...'))

        build_iso_dir = self.script_dir / 'build-iso'
        if build_iso_dir.exists():
            result = subprocess.run(['sudo', 'rm', '-rf', str(build_iso_dir)])
            if result.returncode != 0:
                print(_ui(lang, 'err_remove_dir', 'Error: Failed to remove {0}').format(build_iso_dir))
                sys.exit(1)

        tmp_dir = self.script_dir / 'tmp'
        if tmp_dir.exists():
            for item in tmp_dir.iterdir():
                if item.name != '.gitkeep':
                    result = subprocess.run(['sudo', 'rm', '-rf', str(item)])
                    if result.returncode != 0:
                        print(_ui(lang, 'err_remove_dir', 'Error: Failed to remove {0}').format(item))
                        print(_ui(lang, 'err_remove_dir_hint', 'Hint: A filesystem may still be mounted under {0}. Please check with "mount | grep {0}" and unmount manually.').format(item))
                        sys.exit(1)

        print(_ui(lang, 'ok_dirs_cleaned', '✓ Directories cleaned'))

    def _plugin_scripts_dir(self) -> Path:
        return self.script_dir / 'scripts' / 'make-rocky-bootable' / 'plugins'

    def cleanup_plugin_iso_dirs(self):
        plugins_dir = self._plugin_scripts_dir()
        if not plugins_dir.exists():
            return
        for item in plugins_dir.iterdir():
            if item.name != '.gitkeep':
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()

    def copy_plugin_iso_dirs(self):
        for plugin in self.engine.selected_plugins:
            if not plugin.plugin_iso_dir:
                continue
            iso_dir = plugin.path / 'ISO_DIR'
            if not iso_dir.exists():
                continue
            dest = self._plugin_scripts_dir() / plugin.name
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copytree(str(iso_dir), str(dest), dirs_exist_ok=True)

    def generate_kickstart(self) -> str:
        lang = self.engine.lang
        if not (self.script_dir / 'scripts').exists():
            print(_ui(lang, 'err_scripts_dir', 'Error: scripts/ directory not found.'))
            sys.exit(1)

        is_uefi = self.bootmode == 'uefi'

        print(_ui(lang, 'generating_ks', 'Generating kickstart from plugins...'))
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
        lang = self.engine.lang
        print(_ui(lang, 'building_iso', '\nBuilding ISO image...'))
        print(_ui(lang, 'building_iso_wait1', '  This process takes approximately 30 minutes to 1 hour.'))
        print(_ui(lang, 'building_iso_wait2', '  Please wait until the build completes.'))
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
                prompt = _ui(lang, 'overwrite_prompt', "'{0}' already exists. Overwrite? (y/N): ").format(iso_name)
                answer = input(prompt).strip().lower()
                if answer != 'y':
                    print(_ui(lang, 'aborted', 'Aborted.'))
                    sys.exit(0)

            image_size = max(
                [8704] + [p.image_size for p in self.engine.selected_plugins if p.image_size is not None]
            )
            extra_opts = ['--virt-uefi'] if is_uefi else []
            log_path = f'{self.script_dir}/logs/livemedia-creator.log'

            # Copy tmpl to a temp dir and substitute @DEFAULTBOOT@ placeholders
            tmpl_tmp = Path(tempfile.mkdtemp(prefix='tmpl-', dir=self.script_dir / 'tmp'))
            shutil.copytree(self.script_dir / 'tmpl', tmpl_tmp / 'tmpl')
            is_ram = getattr(self, 'live_bootmode', 'normal') == 'ram'
            grub_idx  = '1' if is_ram else '0'
            iso_normal = 'menu default' if not is_ram else ''
            iso_ram    = 'menu default' if is_ram else ''
            for cfg, replacements in [
                (
                    tmpl_tmp / 'tmpl/live/config_files/x86/grub2-efi.cfg',
                    [('@DEFAULTBOOT_IDX@', grub_idx)],
                ),
                (
                    tmpl_tmp / 'tmpl/live/config_files/x86/isolinux.cfg',
                    [('@DEFAULTBOOT_NORMAL@', iso_normal), ('@DEFAULTBOOT_RAM@', iso_ram)],
                ),
            ]:
                text = cfg.read_text()
                for placeholder, value in replacements:
                    text = text.replace(placeholder, value)
                cfg.write_text(text)

            cmd = [
                'sudo', 'livemedia-creator',
                '--make-iso',
                f'--ks={temp_ks}',
                f'--iso={self.iso_path}',
                f'--iso-name={iso_name}',
                '--iso-only',
                f'--resultdir={self.script_dir}/build-iso',
                f'--logfile={log_path}',
                '--project=Rocky Linux',
                f'--releasever={self.os_version}',
                f'--tmp={self.script_dir}/tmp',
                f'--image-size={image_size}',
                f'--lorax-templates={tmpl_tmp}/tmpl',
            ] + extra_opts

            print(_ui(lang, 'running_livemedia', 'Running livemedia-creator (this may take a while)...'))
            print(_ui(lang, 'log_file', 'Log: {0}').format(log_path))
            print()
            result = subprocess.run(cmd)

            shutil.rmtree(tmpl_tmp, ignore_errors=True)

            if result.returncode != 0:
                print(_ui(lang, 'err_livemedia', 'Error: livemedia-creator failed.'))
                sys.exit(1)

            print(_ui(lang, 'embedding_checksum', 'Embedding ISO checksum...'))
            subprocess.run(['sudo', 'implantisomd5', '--force', str(output_iso)])

            print()
            print("=" * 70)
            print(_ui(lang, 'ok_iso_created', '✓ ISO created successfully!'))
            print("=" * 70)
            print()
            print(_ui(lang, 'iso_path_label', 'ISO:       {0}').format(output_iso))
            print(_ui(lang, 'bootmode_label', 'Boot mode: {0}').format(self.bootmode))
            print()
            print(_ui(lang, 'security_reminder', 'SECURITY REMINDER:'))
            print(_ui(lang, 'security_1', '  - The ISO uses the custom root password you provided'))
            print(_ui(lang, 'security_2', '  - SELinux is in permissive mode'))
            print(_ui(lang, 'security_3', '  - This ISO is intended for temporary use only'))
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
            self.cleanup_plugin_iso_dirs()
            self.copy_plugin_iso_dirs()
            try:
                self.build_iso()
            finally:
                self.cleanup_plugin_iso_dirs()
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
    parser.add_argument('--language', metavar='LANG',
                        help='Force display language (e.g. en, ja). Overrides environment variables.')
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
    if args.language:
        builder.engine.lang = args.language.lower()
    builder.run()


if __name__ == "__main__":
    main()
