# language-japanese-support

[← 一覧に戻る](README.md)

## 概要

日本語ロケール・キーボードレイアウト・タイムゾーンを設定します。

## メタ情報

| 項目 | 値 |
|------|-----|
| 種別 | 選択式 (`check = true`) |
| デフォルト | — (未選択) |
| 適用順序 | 20 |
| 対応OS | 全OS |
| 依存プラグイン | — |

## 追加パッケージ

| パッケージ | 説明 |
|-----------|------|
| `langpacks-ja` | 日本語言語パック |
| `glibc-langpack-ja` | glibc 日本語ロケール |

## 設定内容

| 設定 | 内容 |
|------|------|
| ロケール | `/etc/locale.conf` に `LANG=ja_JP.UTF-8` を設定 |
| コンソールキーボード | `/etc/vconsole.conf` に `KEYMAP=jp106` を設定 |
| X11キーボード | `/etc/X11/xorg.conf.d/00-keyboard.conf` に `XkbLayout jp` を設定 |
| タイムゾーン | `/etc/localtime` を `Asia/Tokyo` にシンボリックリンク |

> **Note:** kickstart ヘッダーのデフォルトは `lang en_US.UTF-8` / `keyboard us` / `timezone UTC` です。
> このプラグインが有効な場合のみ、%post で日本語環境に切り替えます。
