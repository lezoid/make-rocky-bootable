# プラグインシステム 要件定義

作成日: 2026-03-14

---

## 概要

kickstartファイルの肥大化を防ぐため、各種処理をプラグインとして分割管理する。
build2.pyはpluginディレクトリを参照し、ユーザーの選択に応じてkickstartを動的に生成する。

---

## ディレクトリ構造

```
plugins/
  os/
    rocky8/
      osdefine              # OSメタ定義（ISOのURL等）
    rocky9/
      osdefine
    rocky10/
      osdefine
  features/                 # 機能プラグイン置き場
    packages/
      default-add-packages  # 基本追加パッケージ
      default-remove-packages  # デフォルト除外パッケージ
      language-japanese-support
    post/
      default-setting-os    # OS共通設定
      add-xfce-gui-support  # Rocky8/9 GUI (supported_os = rocky8, rocky9)
      add-kde-gui-support   # Rocky10 GUI (supported_os = rocky10)
      add-user              # 一般ユーザー作成
```

---

## osdefine フォーマット（INI）

```ini
[os]
id = rocky10                        # supported_os フィールドの照合キー
display_name = Rocky Linux 10       # OS選択UIに表示する名前
iso_url = https://ftp.iij.ad.jp/pub/linux/rocky/10/isos/x86_64/Rocky-10-latest-x86_64-dvd.iso
checksum_url = https://ftp.iij.ad.jp/pub/linux/rocky/10/isos/x86_64/Rocky-10-latest-x86_64-dvd.iso.CHECKSUM
```

- `id` は小文字・ハイフンなしで統一（例: rocky8, rocky9, rocky10）

---

## プラグイン フォーマット（INI）

```ini
[meta]
label = Create General User         # UIに表示するラベル
description = 一般ユーザーを作成する  # 説明文（省略可）
check = true                        # true=ユーザー選択 / false=サイレント強制適用
default = true                      # check=true のとき、デフォルトで選択済みにするか
order = 30                          # kickstartへの適用順序（昇順）
                                    # 同値の場合はファイル名昇順
supported_os = rocky8, rocky9, rocky10  # 省略時は全OS対象
                                        # osdefine の id と照合
requires = some-other-plugin        # 依存プラグイン名（省略可）

[prompts]
# ユーザー入力が必要なフィールドを定義
# type: text / password / boolean
name.type = text
name.label = Username
name.default = user

password.type = password
password.label = Password
password.default = user

sudoer.type = boolean
sudoer.label = Add to wheel (sudoers)?
sudoer.default = true

disable_root_ssh.type = boolean
disable_root_ssh.label = Disable root SSH login?
disable_root_ssh.default = false

[packages]
# %packages セクションに追加するパッケージ（1行1パッケージ）
some-package

[packages.remove]
# %packages セクションから除外するパッケージ
-unwanted-package

[post]
# %post セクションに追加するスクリプト
# ${変数名} でプロンプト入力値やグローバル変数を参照可能
useradd ${name}
echo "${name}:${password}" | chpasswd
```

### check フラグの挙動

| 値 | 挙動 |
|---|---|
| `true` | ユーザーにチェックボックスで選択させる |
| `false` | UIに表示せずサイレントで強制適用 |

---

## グローバル変数（ビルド設定）

以下の変数はプラグイン内で `${変数名}` として参照可能。

| 変数名 | 内容 |
|---|---|
| `${root_password}` | rootパスワード |
| `${uefi}` | UEFI/MBR（true/false） |

### 入力方式

- デフォルト: インタラクティブプロンプト（対話式）
- `--config build.ini` 引数指定時: 設定ファイルから読み込み（無人実行）

---

## build2.py 処理フロー

```
Step 0: plugins/os/*/osdefine をスキャン
        → OS選択UIを表示（例: 1) Rocky Linux 8 / 2) Rocky Linux 9 / 3) Rocky Linux 10）

Step 1: 選択OS の id を取得
        plugins/features/**/* をスキャン
        → supported_os でフィルタリング（省略プラグインは全OS対象）

Step 2: フィルタ済みプラグインを check フラグで分類
        → check=true: チェックボックスUIでユーザーに選択させる
        → check=false: サイレント適用（ユーザーに見せない）

Step 3: 選択されたプラグインの依存関係を解決（requires）
        → 未選択の依存プラグインは自動追加

Step 4: [prompts] を持つプラグインのユーザー入力を収集

Step 5: order 昇順にプラグインをソート（同値はファイル名昇順）
        → kickstart を組み立て
          - %packages: [packages] セクションを結合
          - %packages: [packages.remove] セクションを結合
          - %post: [post] セクションをorder順に結合

Step 6: ${変数} トークンをプロンプト入力値・グローバル変数で置換

Step 7: kickstartファイルを出力してビルド実行
```

---

## 移行方針

- `template.ks.j2` はプラグインシステム完成後に廃止
- 移行期間中は `build.py`（Jinja2テンプレート方式）と `build2.py`（プラグイン方式）を並走
- `build2.py` が安定したら `build.py` を置き換え

---

## 未決事項

- なし

---

## 変更履歴

| 日付 | 内容 |
|---|---|
| 2026-03-14 | 初版作成 |
