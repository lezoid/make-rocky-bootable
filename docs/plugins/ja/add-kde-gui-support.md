# add-kde-gui-support

[← 一覧に戻る](README.md)

## 概要

KDE Plasma デスクトップ環境と krdp RDP サーバーをインストールします。
RDP (ポート 3389) 経由でリモートデスクトップ接続が可能になります。

> ⚠️ **実験的サポートです。**
> 仮想化環境（VMware・Hyper-V・VirtualBox など）において解像度変更を行うと
> セッションが応答不能になる事象を確認しています。実機環境での利用を推奨します。

## メタ情報

| 項目 | 値 |
|------|-----|
| 種別 | 選択式 (`check = true`) |
| デフォルト | — (未選択) |
| 適用順序 | 50 |
| 対応OS | Rocky Linux 10 |
| 依存プラグイン | **add-user** (自動追加) |
| ISOイメージサイズ | 12288 MB |

## プロンプト

| フィールド | 種別 | デフォルト | 説明 |
|-----------|------|-----------|------|
| `enable_rdp` | boolean | `true` | RDP サーバーを有効化する（有効にすると SDDM 自動ログインも有効になります） |
| `install_mozc` | boolean | `true` | Fcitx5 + Mozc (日本語入力) をインストールする ※ `language-japanese-support` 選択時のみ表示 |

> **Note:** Fcitx5 + Mozc は root ユーザーでは利用できません。

## 設定内容

| 設定 | 内容 |
|------|------|
| リポジトリ | EPEL・CRB を有効化 |
| デスクトップ | KDE Plasma Workspaces グループをインストール |
| 追加パッケージ | `firefox` |
| 起動設定 | SDDM を有効化、グラフィカルターゲットをデフォルトに設定 |
| テーマ | Breeze Dark テーマを `/etc/skel` に設定 |
| 電源管理 | 画面消灯・スクリーンロックを無効化 |
| RDP (`enable_rdp=true`) | krdp サーバーを自動起動、ポート 3389 を開放、SDDM 自動ログインを設定、TLS 証明書を自動生成 |
| 日本語入力 (`install_mozc=true`) | Flatpak 経由で Fcitx5 + Mozc をインストール |
