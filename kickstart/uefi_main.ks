#version=RHEL9 UEFI Main
# System language
lang en_US.UTF-8
#lang ja_JP.UTF-8

# Keyboard layout
keyboard jp

# Timezone settings
timezone Asia/Tokyo --utc

# root user plain text password settings
rootpw --plaintext password
# root user encrypt password setting
# rootpw --iscrypted $6$randomsalt$encryptedpasswordhash

# Network settings
network --bootproto=dhcp --device=link --activate

# Disable SELinux
selinux --permissive

# Authentication information
auth --useshadow --passalgo=sha512

# Disk partitioning(UEFI)
bootloader --location=none
clearpart --all --initlabel
reqpart
part / --size=6656

# Package selection
%packages
## --Required LiveBoot Packages ---
dracut-live
memtest86+
syslinux
*-logos
firewalld
#Add UEFI Support
shim
grub2
grub2-efi
grub2-efi-*-cdboot
efibootmgr
## ---------Add Packages-----------
vi
bash-completion
## -------Remove Packages----------
-iwl*-firmware
%end

# Post script: Configure services and system settings inside the guest
%post --log=/root/ks-post.log

# Allow SSH login as root
sed -i 's/#PermitRootLogin yes/PermitRootLogin yes/' /etc/ssh/sshd_config
sed -i 's/^#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
systemctl restart sshd

# Enable firewalld
systemctl enable firewalld
systemctl start firewalld

# Create a systemd service for running the startup script once at boot
cat << EOF > /etc/systemd/system/firstboot-startup.service
[Unit]
Description=Run startup.sh script on first boot
After=network.target

[Service]
Type=oneshot
ExecStart=/bin/bash /run/initramfs/live/scripts/startup.sh
ExecStartPost=/bin/rm -f /etc/systemd/system/firstboot-startup.service

[Install]
WantedBy=multi-user.target
EOF

# Enable the firstboot service
systemctl enable firstboot-startup.service

# make sure there aren't core files lying around
rm -f /core*
rm -f /var/lib/rpm/__db*

# remove random seed, the newly installed instance should make it's own
rm -f /var/lib/systemd/random-seed

# Remove machine-id on pre generated images
rm -f /etc/machine-id
touch /etc/machine-id

# Remove unnecessary kickstart files
rm -f /root/anaconda-ks.cfg /root/ks-post.log /root/original-ks.cfg
%end
shutdown

