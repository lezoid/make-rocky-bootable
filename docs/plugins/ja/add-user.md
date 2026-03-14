# add-user

[← 一覧に戻る](README.md)

## 概要

一般ユーザーを作成します。sudo権限付与・root SSH無効化・初回ログイン起動サービスのオプションがあります。

## メタ情報

| 項目 | 値 |
|------|-----|
| 種別 | 選択式 (`check = true`) |
| デフォルト | — (未選択) |
| 適用順序 | 90 |
| 対応OS | 全OS |
| 依存プラグイン | — |

## プロンプト

ビルド時に以下の入力を求められます。

| フィールド | 種別 | デフォルト | 説明 |
|-----------|------|-----------|------|
| `name` | text | `user` | ユーザー名 |
| `password` | password | `user` | ユーザーパスワード |
| `sudoer` | boolean | `true` | wheel グループ (sudoers) に追加するか |
| `disable_root_ssh` | boolean | `false` | root の SSH ログインを無効化するか |
| `enable_firstboot_user_startup` | boolean | `false` | 初回ログイン時に `startup-user.sh` を実行するか |

## 設定内容

| 設定 | 内容 |
|------|------|
| ユーザー作成 | `useradd` でユーザーを作成し、パスワードを設定 |
| sudo権限 | `sudoer=true` の場合、wheel グループに追加 |
| root SSH | `disable_root_ssh=true` の場合、`/etc/ssh/sshd_config` を変更 |
| 起動サービス | `enable_firstboot_user_startup=true` の場合、`/etc/skel` に systemd ユーザーサービスを配置 |

`enable_firstboot_user_startup=true` の場合の動作:

| 項目 | 内容 |
|------|------|
| スクリプトパス | `/run/initramfs/live/scripts/make-rocky-bootable/plugins/add-user/startup-user.sh` |
| ログ出力先 | `~/.local/log/make-rocky-bootable/firstboot-user-startup.log` |
| 実行回数 | 初回ログイン時のみ（実行後にサービスファイルを自己削除） |

## カスタマイズ

リポジトリの以下のファイルを編集することで、初回ログイン時に任意の処理を一般ユーザーで自動実行できます。

```
plugins/features/post/add-user/ISO_DIR/startup-user.sh
```

> **Note:** `add-kde-gui-support` プラグインは `add-user` に依存しています。
> KDE プラグインを選択した場合、`add-user` が未選択でも自動的に追加されます。
