# make-rocky-bootable

応答形式で手軽にカスタムブータブルISOを簡単に作成できるツールです :)

## 言語
- [英語 (English)](../README.md)
- [日本語 (Japanese)](README_JP.md)

## 目次
- [概要](#概要)
- [動作要件](#動作要件)
- [使い方](#使い方)
- [プラグインシステム](#プラグインシステム)
- [利用可能なプラグイン](#利用可能なプラグイン)
- [起動スクリプト](#起動スクリプト)
- [利用前の注意事項](#利用前の注意事項)

---

## 概要

`make-rocky-bootable` はプラグインベースのシステムを採用したRocky Linux用ブータブルISO作成ツールです。
対話形式のTUIでOSバージョン・機能・ブートモードを選択するだけで、カスタムISOを自動生成します。

**対応OSバージョン:**

| OS | GUI |
|----|-----|
| Rocky Linux 8 | XFCE + XRDP |
| Rocky Linux 9 | XFCE + XRDP |
| Rocky Linux 10 | KDE Plasma + krdp ⚠️ 実験的 |

> ⚠️ **Rocky Linux 10 + KDE Plasma は実験的サポートです。**
> 仮想化環境（VMware・Hyper-V・VirtualBoxなど）において解像度変更を行うと
> セッションが応答不能になる事象を確認しています。実機環境での利用を推奨します。

---

## 動作要件

ビルドホストは Rocky Linux 8 / 9 / 10 (KVM有効) を推奨します。

**必要パッケージ:**

```sh
dnf install -y qemu-kvm lorax lorax-lmc-virt wget isomd5sum syslinux-nonlinux
```

---

## 使い方

```sh
git clone https://github.com/lezoid/make-rocky-bootable.git
cd make-rocky-bootable
./build.py
```

実行するとTUIが起動し、以下の順に設定を行います。

1. **OSを選択** — Rocky Linux 8 / 9 / 10
2. **プラグインを選択** — インストールする機能をチェックボックスで選択
3. **プラグイン設定** — 選択したプラグインの設定値を入力（ユーザー名・パスワードなど）
4. **rootパスワードを設定**
5. **ブートモードを選択** — UEFI Boot / CSM/BIOS (MBR) Boot
6. **ISO ダウンロード・ビルド** — 自動でISOを取得してビルド

ビルドには **数十分から1時間程度** かかります。完了するとISOが `build-iso/` に出力されます。

### オプション

```sh
./build.py [オプション]

  --debug           デバッグモード: 生成されたkickstartを表示する
  --view-kickstart  kickstartの内容を確認するだけでビルドはしない
  --language LANG   表示言語を強制指定する (例: en, ja)
```

---

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

---

## 利用可能なプラグイン

プラグインの一覧・詳細・カスタムプラグインの作成方法については、プラグインドキュメントを参照してください。

**[→ プラグインドキュメント (日本語)](../docs/plugins/ja/README.md)**

---

## 起動スクリプト

`scripts/` 配下のファイルはISO作成時にrootイメージに組み込まれ、
LiveCDとして起動した際には **`/run/initramfs/live/scripts/`** としてアクセスできます。

```
リポジトリ上のパス                                    LiveCD上のパス
scripts/                                    →    /run/initramfs/live/scripts/
├── make-rocky-bootable/
│   └── plugins/                            →    /run/initramfs/live/scripts/make-rocky-bootable/plugins/
│       ├── firstboot-root-startup/         →    （firstboot-root-startupプラグイン有効時）
│       │   └── startup-root.sh            →    /run/initramfs/live/scripts/make-rocky-bootable/plugins/firstboot-root-startup/startup-root.sh
│       └── add-user/                       →    （add-userプラグイン有効時）
│           └── startup-user.sh            →    /run/initramfs/live/scripts/make-rocky-bootable/plugins/add-user/startup-user.sh
└── users/                                  →    /run/initramfs/live/scripts/users/
```

> `make-rocky-bootable/plugins/` 配下はビルド時に動的に生成され、ビルド完了後は自動クリーンアップされます。
> `users/` はユーザーが自由にファイルを配置できるディレクトリです（スタートアップスクリプトから参照するファイルの置き場として利用できます）。

スタートアップスクリプトは各プラグインの `ISO_DIR/` として管理されています。

```
plugins/features/post/firstboot-root-startup/ISO_DIR/startup-root.sh   # root用テンプレート
plugins/features/post/add-user/ISO_DIR/startup-user.sh                 # ユーザー用テンプレート
```

### startup-root.sh

**初回起動時に root で1回だけ自動実行されます。**

`firstboot-root-startup` プラグインを有効化すると、
systemd サービス (`firstboot-root-startup.service`) 経由で実行されます。
実行後はサービスファイル自体が自動削除されるため、2回目以降の起動では実行されません。

```
実行タイミング: OS起動 → network.target 到達後 → startup-root.sh 実行 → サービス自己削除
ログ出力先:    /var/log/make-rocky-bootable/firstboot-root-startup.log
```

### startup-user.sh

**一般ユーザーの初回ログイン時に1回だけ自動実行されます。**

`add-user` プラグインの「初回ログイン時の一般ユーザー起動サービスを有効化」を
有効にした場合のみ機能します。
ユーザーのsystemdサービスとして登録され、実行後は自己削除されます。

```
実行タイミング: ユーザーログイン → default.target 到達後 → startup-user.sh 実行 → サービス自己削除
ログ出力先:    ~/.local/log/make-rocky-bootable/firstboot-user-startup.log
```

Kickstartに不慣れな方でも、これらのスクリプトに処理を追記するだけで
独自ツールの実行やシステム設定の自動化が可能です。

---

## 利用前の注意事項

- 作成されたISOにはビルド時に設定したrootパスワードが含まれています。
- SELinux は `permissive` モードで動作します。
- SSHポートが開放されており、rootログインが許可されています。
- GUIプラグインを有効化した場合はRDPポート (3389) も開放されます。
- **本ISOは一時的な利用を想定しています。不特定多数がアクセスできる環境での利用は推奨しません。**
- KDE版はRDPと物理グラフィカル画面から同一ユーザーで同時ログインすることはできません。
