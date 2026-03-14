# default-setting-os

[← 一覧に戻る](README.md)

## 概要

SSH・firewalld・dnf の基本OS設定を行います。

## メタ情報

| 項目 | 値 |
|------|-----|
| 種別 | 常時適用 (`check = false`) |
| 適用順序 | 15 |
| 対応OS | 全OS |

## 設定内容

| 設定 | 内容 |
|------|------|
| dnf | `fastestmirror=True`、タイムアウト・リトライ設定を `/etc/dnf/dnf.conf` に追記 |
| SSH | root ログインを許可 (`PermitRootLogin yes`) |
| firewalld | 起動時に自動有効化 |
