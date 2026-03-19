# default-add-packages

[← 一覧に戻る](README.md)

## 概要

ライブブートISOに必要な基本パッケージを追加します。

## メタ情報

| 項目 | 値 |
|------|-----|
| 種別 | 常時適用 (`check = false`) |
| 適用順序 | 10 |
| 対応OS | 全OS |

## 追加パッケージ

| パッケージ | 説明 |
|-----------|------|
| `dracut-live` | ライブブート用 dracut モジュール |
| `memtest86+` | メモリテストツール |
| `syslinux` | ブートローダー |
| `*-logos` | OSロゴパッケージ |
| `firewalld` | ファイアウォール |
| `vi` | テキストエディタ |
| `bash-completion` | Bash 補完機能 |
