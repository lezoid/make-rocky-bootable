# プラグイン一覧

make-rocky-bootable のプラグインは `plugins/` ディレクトリに配置されています。
各プラグインの詳細は個別ページを参照してください。

## 常時適用プラグイン

`check = false` のプラグインはユーザーの選択によらず常に適用されます。

| プラグイン名 | 概要 | 詳細 |
|------------|------|------|
| default-remove-packages | 不要なファームウェアパッケージを除外 | [→](default-remove-packages.md) |
| default-add-packages | ライブブートに必要な基本パッケージを追加 | [→](default-add-packages.md) |
| default-setting-os | SSH・firewalld・dnf の基本設定 | [→](default-setting-os.md) |

## 選択式プラグイン

`check = true` のプラグインはビルド時にTUIで選択できます。
「デフォルト」列が ✓ のものは初期状態でチェック済みです。

| プラグイン名 | 概要 | 対応OS | デフォルト | 依存 | 詳細 |
|------------|------|--------|-----------|------|------|
| language-japanese-support | 日本語ロケール・キーボード・タイムゾーン設定 | 全OS | — | — | [→](language-japanese-support.md) |
| add-user | 一般ユーザーの作成 | 全OS | — | — | [→](add-user.md) |
| add-xfce-gui-support | XFCE デスクトップ + XRDP | Rocky 8, 9 | — | — | [→](add-xfce-gui-support.md) |
| add-kde-gui-support | KDE Plasma デスクトップ + krdp (RDP) | Rocky 10 ⚠️ | — | add-user | [→](add-kde-gui-support.md) |
| firstboot-root-startup | 初回起動時に startup-root.sh を root で実行 | 全OS | ✓ | — | [→](firstboot-root-startup.md) |
| default-sysprep | システムクリーンアップ (sysprep) | 全OS | ✓ | — | [→](default-sysprep.md) |

## 独自プラグインの作成

独自プラグインの作成方法については [カスタムプラグイン作成ガイド](custom-plugin.md) を参照してください。
