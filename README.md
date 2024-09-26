# make-rocky-bootable

make-rocky-bootable helps you create a custom bootable ISO easily :)

## Languages
- [英語 (English)](README/README_EN.md)
- [日本 (Japan)](README/README_JP.md)

## Table of Contents
- [make-rocky-bootable](#make-rocky-bootable)
  - [Languages](#languages)
  - [Table of Contents](#table-of-contents)
  - [Requirements](#requirements)
  - [Usage](#usage)
  - [Advantages of make-rocky-bootable](#advantages-of-make-rocky-bootable)
  - [Precautions Before Using the ISO Created by This Tool](#precautions-before-using-the-iso-created-by-this-tool)

## Requirements

- Rocky Linux 9 with virtualization (KVM) enabled
  (Not tested on other versions, but should work on EL8 or later compatible OS)
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

## Advantages of make-rocky-bootable

- **Embedding and Executing Custom Binaries and Scripts**
  The created live DVD executes /run/initramfs/live/scripts/startup.sh via systemd at boot time.
  /run/initramfs/live/scripts/ is copied from the scripts/ directory of make-rocky-bootable during ISO creation.
  
  This tool allows even those unfamiliar with kickstart to easily customize the bootable ISO by placing files to be embedded or automatically executing custom processes.

- **Easily Create Lightweight GUI Images with RDP Support**
  Recent default LiveCDs often use GNOME3 by default, which can cause significant delays on servers with poor graphical performance due to effect processing.

  To address such environments, make-rocky-bootable allows the creation of lightweight live DVDs with xfce enabled by default.
  Additionally, xrdp is enabled, allowing clipboard functionality via remote desktop connection.

## Precautions Before Using the ISO Created by This Tool

- The standard image has the SSH port open and allows root login via the kickstart file.
- The GUI image has both SSH and RDP ports open.
- All user passwords are defined as "password" in the kickstart file.
- Be sure to edit the kickstart file to change the root password to a complex one or switch to key authentication.
  For those unfamiliar with kickstart, it is recommended to include a script in startup.sh to change the password.
- This tool is designed to create bootable ISOs for temporary use, and it is not recommended for use in environments accessible by an unspecified number of people.
- The GUI version does not allow simultaneous login with the same user from both RDP and the physical graphical target screen.
  For exclusive use, log in from only one side or log out from Xfce when switching.# make-rocky-bootable
