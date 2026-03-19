# プラグイン一覧

make-rocky-bootable のプラグインは `plugins/` ディレクトリに配置されています。
このページでは利用可能なプラグイン一覧と、プラグインシステムの仕組みをまとめています。

## 常時適用プラグイン

`check = false` のプラグインはユーザーの選択によらず常に適用されます。

| プラグイン名 | 概要 | 詳細 |
|------------|------|------|
| default-remove-packages | 不要なファームウェアパッケージを除外 | [→](default-remove-packages.md) |
| default-add-packages | ライブブートに必要な基本パッケージを追加 | [→](default-add-packages.md) |
| default-setting-os | SSH・firewalld・dnf の基本設定 | [→](default-setting-os.md) |

## 選択式プラグイン

`check = true` のプラグインはビルド時に TUI で選択を可能とします。
「デフォルト」列が ✓ のものは初期状態でチェック済みです。
依存関係を持つプラグインは、必要なプラグインが自動的に追加されます。

| プラグイン名 | 概要 | 対応OS | デフォルト | 依存 | 詳細 |
|------------|------|--------|-----------|------|------|
| language-japanese-support | 日本語ロケール・キーボード・タイムゾーン設定 | 全OS | — | — | [→](language-japanese-support.md) |
| add-user | 一般ユーザーの作成 + root SSH ログイン無効化 (任意) + startup-user.sh / startup-user-network.sh を初回ログイン時に実行 (任意) | 全OS | — | — | [→](add-user.md) |
| add-xfce-gui-support | XFCE デスクトップ + XRDP | Rocky 8, 9 | — | — | [→](add-xfce-gui-support.md) |
| xfce-autologin | XFCE デスクトップで指定ユーザーの自動ログインを設定する | Rocky 8, 9 | — | add-xfce-gui-support | [→](xfce-autologin.md) |
| add-kde-gui-support | KDE Plasma デスクトップ + krdp (RDP) | Rocky 10 ⚠️ | — | add-user | [→](add-kde-gui-support.md) |
| kiosk-browser | kiosk ブラウザを build・導入し、OS ごとのデスクトップ抑止設定を行う | Rocky 8, 9, 10 | — | add-user, add-xfce-gui-support または add-kde-gui-support | [→](kiosk-browser.md) |
| firstboot-root-startup | 初回起動時に startup-root.sh (通常) および/または startup-root-network.sh (ネットワーク待機) を root で実行 | 全OS | — | — | [→](firstboot-root-startup.md) |
| default-sysprep | システムクリーンアップ (sysprep) | 全OS | ✓ | — | [→](default-sysprep.md) |

## 独自プラグインの作成

独自プラグインの作成方法については [カスタムプラグイン作成ガイド](custom-plugin.md) を参照してください。

## プラグインシステム

本ツールはプラグインによって動作をカスタマイズできます。

### ディレクトリ構成

```
plugins/
├── os/
│   ├── rocky8/osdefine      # Rocky Linux 8 の定義
│   ├── rocky9/osdefine      # Rocky Linux 9 の定義
│   └── rocky10/osdefine     # Rocky Linux 10 の定義
└── features/
    ├── packages/            # パッケージ追加・削除プラグイン
    │   └── plugin-name/
    │       └── metadata.ini
    └── post/                # %post スクリプトプラグイン
        └── plugin-name/
            ├── metadata.ini
            └── ISO_DIR/     # オプション: ISO内に配置するファイル群
```

### プラグインのINI形式

```ini
[meta]
label = Plugin Name
label.ja = プラグイン名
description = What this plugin does
description.ja = プラグインの説明
check = true          # true: TUIで選択可能, false: 常時適用
default = false       # true: デフォルトでチェック済み
order = 100           # 適用順序（数値が小さいほど先）
supported_os = rocky10  # 対応OSを限定する場合に指定（省略時は全OS対応）
requires = add-user   # 依存プラグイン名（自動で有効化される）
PLUGIN_ISO_DIR = false  # true: ISO_DIR/ の中身を LiveCD の scripts 領域にコピー

[prompts]
# ユーザー入力を受け付けるフィールドを定義する
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
# %packages に追加するパッケージ
vim

[packages.remove]
# %packages から除外するパッケージ
-iwl*-firmware

[post]
# %post スクリプトに追加するシェルスクリプト
# ${変数名} でプロンプト入力値を参照できる
echo "Hello, ${name}"
```

### PLUGIN_ISO_DIR

プラグインディレクトリ内に `ISO_DIR/` フォルダを作成し、`metadata.ini` に `PLUGIN_ISO_DIR = true` を設定すると、
ビルド時に `ISO_DIR/` の中身が LiveCD の以下のパスにコピーされます。

```
ISO_DIR/ の中身  →  scripts/make-rocky-bootable/plugins/{plugin名}/
```

LiveCD起動後は **`/run/initramfs/live/scripts/make-rocky-bootable/plugins/{plugin名}/`** としてアクセスできます。

### トークン置換

`[post]` 内では以下の記法でプロンプト入力値を参照できます。

| 記法 | 説明 |
|------|------|
| `${変数名}` | 変数の値に置換 |
| `${if_変数名}...${endif_変数名}` | 変数が真のときのみ出力 |

### OS別依存

`[meta]` では `requires` に加えて OS 別依存キーを指定できます。

```ini
[meta]
requires = add-user
requires.rocky9 = add-xfce-gui-support
requires.rocky10 = add-kde-gui-support
```

選択OSが一致した場合、`requires.<os_id>` は `requires` と合わせて適用されます。
