# dnf-update

`dnf-update` は、Kickstart の `%post` 中で `dnf -y update` を実行する任意の post プラグインです。

## 動作

- `default-setting-os` の後に実行されます
- `default-setting-os` が書き込んだ `dnf.conf` の設定を使って更新を行います
- 後続の post プラグインより前に、ビルド VM 内のインストール済みパッケージを更新します

## 注意点

- このプラグインは任意選択で、デフォルトでは有効になりません
- 有効にするとビルド時間が伸びます
- ミラーやネットワーク状況の影響を受けやすくなります
- Rocky Linux 8 / 9 / 10 で利用できます
