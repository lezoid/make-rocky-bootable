# make-rocky-bootable

make-rocky-bootableは簡単にカスタムしたブータブルISOの作成を行うことができます :)
![GUI Mode Screenshot](README/res/screenshot0.png)

## Languages
- [英語 (English)](README/README_EN.md)
- [日本 (Japan)](README/README_JP.md)

## 目次
- [make-rocky-bootable](#make-rocky-bootable)
  - [Languages](#languages)
  - [目次](#目次)
  - [Requirements](#requirements)
  - [Usage](#usage)
  - [make-rocky-bootableの利点](#make-rocky-bootableの利点)
  - [本ツールで作成したiso利用前の注意事項](#本ツールで作成したiso利用前の注意事項)


## Requirements

- 仮想化(KVM)が有効化なRocky Linux 9 
  (Rocky Linux 9以外は試してないけど、EL8以上の互換系OSならたぶん動く気がする）
- qemu-kvm
- lorax
- lorax-lmc-virt

## Usage

1. **Run the make-rocky-bootable**
    ```sh
    # git clone https://github.com/lezoid/make-rocky-bootable.git
    # cd make-rocky-bootable
    # ./build.sh --help
    Usage: ./build2.sh [--boot-mode MODE] [--help]
    
    Options:
     --boot-mode MODE     Specify the boot mode: 'uefi', 'mbr', 'uefi_gui', or 'mbr_gui'.
                       - uefi: Uses kickstart/uefi_main.ks (default)
                       - mbr: Uses kickstart/mbr_main.ks
                       - uefi_gui: Uses kickstart/uefi_gui.ks
                       - mbr_gui: Uses kickstart/mbr_gui.ks
                       --help               Display this help message.
    # ./build.sh
    ```

    基本的にはbuild.shを実行するだけで良いです。
    UEFIに対応したイメージがbuild-iso配下に出力されます。
    GUI対応イメージを作成したい場合においては、`--boot-mode`で`uefi_gui`もしくは`mbr_gui`を入力してください。
    
    UEFIイメージでもBIOS構成のマシンでもブート可能な事を確認しています。
    EFIがあると不都合な環境の場合は`--boot-mode`で`mbr`もしくは`mbr_gui`を入力してください。
    EFI関連のパッケージやファイルを内包しない形のisoが出力されます。

2. **Settings**
   1. パッケージの追加 (Edit Kickstart)
    ```text
    kickstart/uefi_*.ks , kickstart/mbr_*.ks 
    上記Kickstartの%packagesに追加することでデフォルトパッケージを増やすことができます。
    パスワードはrootpwの記述を変更することで対応することができます。
    ```
   2. rootパスワードの変更 (Edit Kickstart)
    ```text
    パスワードはrootpwの記述を変更することで対応することができます。
    # root user plain text password settings
    rootpw --plaintext password
    # root user encrypt password setting
    # rootpw --iscrypted $6$randomsalt$encryptedpasswordhash
    ```
   3. 自前のツールの埋め込み
    ```text
    kickstartでルートイメージに自前のファイルを展開して、
    rootイメージ内部に組み込んでしまうという手もありますが、
    本ツールで作成したisoは起動時にsystemd経由で/run/initramfs/live/scripts/startup.shを実行するようにしています。
    /run/initramfs/live/scripts/は、iso作成時にmake-rocky-bootableのscripts/配下からコピーされます。
    ```

    ```sh
    [root@image make-rocky-bootable]# ll scripts/　 ←/run/initramfs/live/scripts/になる
    -rwxr-xr-x. 1 root root 289 Sep 24 17:09  startup.sh ←これ
    ```
    なのでkickstartに不慣れな方でもscripts/に組み込みたいファイルやスクリプトを配置した上で、
    startup.shに処理を記載することで、起動時に独自のツールやスクリプトを実行させることができます。

## make-rocky-bootableの利点

- **自作バイナリやスクリプトの埋め込みと実行**
  作成したライブDVDは起動時にsystemd経由で/run/initramfs/live/scripts/startup.shを実行するようになっています。
  /run/initramfs/live/scripts/は、iso作成時にmake-rocky-bootableのscripts/配下からISO作成時にコピーされます。
  
  本ツールを使うとkickstartに不慣れな方でも、ブータブルISOに組み込みたいファイルを配置したり、
  自前の処理を自動的に実行する、独自のカスタマイズを簡単に行うことができます。

- **手軽にRDP可能な軽量GUIイメージの作成も可能**
  昨今のデフォルト謹製LiveCDだと、大体デフォルトでGNOME3が標準になっている影響で、
  画面描画性能が貧弱なサーバーなどで起動すると、エフェクト処理描画待ちが発生したりして非常にストレスが溜まります。

  そのような環境にも対応できるように、make-rocky-bootableでは、
  xfceをデフォルトで有効化した軽量なライブDVDを生成することが可能になっています。
  またxrdpを有効化しているため、リモートデスクトップで接続することでクリップボード機能も利用できます。

## 本ツールで作成したiso利用前の注意事項

- 標準イメージはsshのポートが開放されており、kickstartファイルでrootログインを許可するようにしています。
- GUIイメージはsshおよびrdpのポートが開放されています。
- いずれのユーザーもパスワードは全て"password"になるように、kickstartで定義しています。
- 必ずkickstartファイルを編集してrootパスワードを複雑な内容に変更もしくは、鍵認証に変更してください。
  kickstartに不慣れな方は埋め込み用スクリプト(startup.sh)でパスワードを変更する処理を入れる事を推奨します。
- あくまでも一時的な利用を想定したブータブルISOを構成する前提として作成しているため、不特定多数の環境から接続が行える環境での利用は推奨しません。
- GUI版はRDPと物理的なグラフィカルターゲットの画面から両方同時に同じユーザーでログインすることはできません。
  排他利用のため片方からのみログインするか、切り替える場合はログイン中のXfceからはログアウトしてください。