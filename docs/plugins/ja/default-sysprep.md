# default-sysprep

[← 一覧に戻る](README.md)

## 概要

ISOイメージを配布・再利用可能な状態にするためのシステムクリーンアップを行います。
machine-id・RPM DB・ログ・一時ファイルなどを削除します。

## メタ情報

| 項目 | 値 |
|------|-----|
| 種別 | 選択式 (`check = true`) |
| デフォルト | ✓ (選択済み) |
| 適用順序 | 200 (最後に実行) |
| 対応OS | 全OS |
| 依存プラグイン | — |

## クリーンアップ内容

| 対象 | 内容 |
|------|------|
| コアダンプ | `/core*` を削除 |
| RPM DB | `/var/lib/rpm/__db*` を削除 |
| systemd random-seed | `/var/lib/systemd/random-seed` を削除 |
| machine-id | `/etc/machine-id` を削除して空ファイルを再作成 |
| anaconda ログ | `/root/anaconda-ks.cfg`・`/root/ks-post.log`・`/root/original-ks.cfg` を削除 |
| ログファイル | `/var/log/wtmp`・`/var/log/btmp`・`/var/log/lastlog` を削除、`/var/log/` 以下を切り詰め |
| 一時ファイル | `/tmp/*`・`/var/tmp/*` を削除 |
| シェル履歴 | `/root/.bash_history`・`/home/*/.bash_history` を削除 |
| dnf キャッシュ | `/var/cache/dnf/*` を削除 |

> **Note:** `order = 200` により常に最後に実行されます。
> このプラグインを無効化すると、これらのファイルがISO内に残ります。
