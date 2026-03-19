# カスタムプラグインの作成

[← 一覧に戻る](README.md)

## 配置場所

プラグインは `plugins/features/` 以下にディレクトリとして配置します。
ディレクトリ名がプラグイン名になります。

```
plugins/features/
├── packages/            # パッケージ操作が主目的のプラグイン
│   └── my-plugin/
│       └── metadata.ini
└── post/                # %post スクリプトが主目的のプラグイン
    └── my-plugin/
        ├── metadata.ini
        └── ISO_DIR/     # オプション: ISO内に配置するファイル群
```

## INI フォーマット

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

## [meta] フィールド一覧

| フィールド | 必須 | 説明 |
|-----------|------|------|
| `label` | ✓ | TUI・ログに表示されるプラグイン名 |
| `label.xx` | — | 言語コード `xx` での表示名 (例: `label.ja`) |
| `description` | — | プラグインの説明文 |
| `description.xx` | — | 言語コード `xx` での説明文 |
| `check` | ✓ | `true`: TUIで選択可能 / `false`: 常時適用 |
| `default` | — | `true`: デフォルトでチェック済み (`check=true` 時のみ有効) |
| `order` | — | 適用順序（小さいほど先）。省略時は `999` |
| `supported_os` | — | 対応OS IDをカンマ区切りで指定。省略時は全OS対応 |
| `requires` | — | 依存プラグイン名。未選択でも自動追加される |
| `requires.<os_id>` | — | OS別の依存プラグイン名。選択OSで `requires` と合わせて適用される |
| `image_size` | — | 必要なISOイメージサイズ (MB)。複数プラグインの最大値が使用される |
| `PLUGIN_ISO_DIR` | — | `true`: `ISO_DIR/` の中身を LiveCD の scripts 領域にコピー |

## ISO_DIR について

`PLUGIN_ISO_DIR = true` を設定し、プラグインディレクトリ内に `ISO_DIR/` フォルダを作成すると、
ビルド時に `ISO_DIR/` の中身が LiveCD の以下のパスにコピーされます。

```
ISO_DIR/ の中身  →  scripts/make-rocky-bootable/plugins/{plugin名}/
```

LiveCD起動後は `/run/initramfs/live/scripts/make-rocky-bootable/plugins/{plugin名}/` としてアクセスできます。

## [prompts] フィールド一覧

`フィールド名.属性 = 値` の形式で定義します。

| 属性 | 説明 |
|------|------|
| `type` | `text` / `password` / `boolean` |
| `label` | 入力時に表示するラベル |
| `label.xx` | 言語コード `xx` でのラベル |
| `note` | ラベルの前に表示する補足メモ |
| `note.xx` | 言語コード `xx` での補足メモ |
| `default` | デフォルト値 |
| `rule` | 入力バリデーションルール（現在は `linux_username` のみ対応） |
| `when_plugin` | 指定したプラグインが選択されている場合のみ表示 |

## トークン置換

`[post]` 内では収集したプロンプト値を参照できます。

| 記法 | 説明 |
|------|------|
| `${変数名}` | 変数の値に置換 |
| `${if_変数名}...${endif_変数名}` | 変数が真のときのみ出力 |
| `${if_プラグイン名}...${endif_プラグイン名}` | 指定プラグインが選択されている場合のみ出力 |

## [post] セクションの注意事項

- `[post]` 内に `[General]` や `[Service]` などの INI ライクな文字列を含む heredoc を書いても問題ありません。
  ビルドシステムは既知のセクション名 (`[meta]`・`[prompts]`・`[packages]`・`[packages.remove]`・`[post]`) のみをセクション境界として扱います。
- スクリプトは kickstart の `%post --log=/root/ks-post.log` 内で実行されます。
