# firstboot-root-startup

[← 一覧に戻る](README.md)

## 概要

ISOから初回起動した際に、`startup-root.sh` を root 権限で1回だけ自動実行するサービスを設定します。

## メタ情報

| 項目 | 値 |
|------|-----|
| 種別 | 選択式 (`check = true`) |
| デフォルト | ✓ (選択済み) |
| 適用順序 | 110 |
| 対応OS | 全OS |
| 依存プラグイン | — |

## 動作

```
OS起動
  └─ network.target 到達後
       └─ firstboot-root-startup.service 実行
            └─ startup-root.sh を実行
                 └─ 実行完了後、サービスファイルを自己削除
                      (2回目以降の起動では実行されない)
```

| 項目 | 内容 |
|------|------|
| スクリプトパス | `/run/initramfs/live/scripts/make-rocky-bootable/plugins/firstboot-root-startup/startup-root.sh` |
| ログ出力先 | `/var/log/make-rocky-bootable/firstboot-root-startup.log` |
| 実行回数 | 初回起動時のみ（実行後にサービスファイルを自己削除） |

## カスタマイズ

リポジトリの以下のファイルを編集することで、初回起動時に任意の処理を root で自動実行できます。

```
plugins/features/post/firstboot-root-startup/ISO_DIR/startup-root.sh
```
