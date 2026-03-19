# kiosk-browser

このプラグインは、イメージ作成中に `rocky-kiosk-browser` を clone・ビルド・導入し、`add-user` で作成したユーザー向けの kiosk ブラウザとして設定します。

## 役割

- `%post` 中に `https://github.com/lezoid/rocky-kiosk-browser.git` を clone
- Qt WebEngine ベースのブラウザをビルド
- `/opt/make-rocky-bootable/kiosk-browser/` に導入
- 起動用 user service とキーボード抑止用 service を作成
- `ISO_DIR/config/` にある `domain-policy.json` と `page-list.json` を、起動前にユーザーごとの runtime ディレクトリへ同期

## 実行時の主な配置先

- ブラウザ本体: `/opt/make-rocky-bootable/kiosk-browser/bin/kiosk-browser`
- 起動ラッパー: `/opt/make-rocky-bootable/kiosk-browser/bin/run-kiosk-browser.sh`
- runtime 設定同期先: `~/.local/share/make-rocky-bootable/kiosk-browser/config/`
- ログ出力先: `~/.local/log/make-rocky-bootable/`

## ブラウザソース

- 取得元: `https://github.com/lezoid/rocky-kiosk-browser.git`
- イメージ作成時に build するため、ビルド時はインターネット接続が必要
- `user_agent` prompt のデフォルト値は Edge 互換の User-Agent

## OS ごとの挙動

- Rocky 8 / Rocky 9
  - `add-xfce-gui-support` を必須依存にする
  - XFCE / xfwm 向けのショートカット抑止を適用
- Rocky 10
  - `add-kde-gui-support` を必須依存にする
  - `kglobalshortcutsrc` を使って KDE のショートカット抑止を適用

## プラグイン配下の主なファイル

- `metadata.ini`
- `ISO_DIR/config/domain-policy.json`
- `ISO_DIR/config/domain-policy.json.example`
- `ISO_DIR/config/page-list.json`
- `ISO_DIR/config/page-list.json.example`

## 補足

- 接続待機画面はブラウザ本体に埋め込まれており、実行時ロケールに応じて表示言語が切り替わる
- ドメイン制御とページ巡回は `ISO_DIR/config/` の JSON を編集して設定する
- 起動ラッパーは毎回それらの JSON をユーザーごとの runtime ディレクトリへ同期してからブラウザを起動する
