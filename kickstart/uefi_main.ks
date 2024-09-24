#version=RHEL9
# System language
lang ja_JP.UTF-8

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
clearpart --all --initlabel
part / --fstype="xfs" --grow --size=8192
bootloader --location=mbr --boot-drive=sda --append="rhgb quiet"

# Package selection
%packages
## --Required LiveBoot Packages ---
dracut-live
memtest86+
syslinux
*-logos
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
systemctl restart sshd

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

# Debug Message
echo "===== Disk and Partition Info ====="
fdisk -l | tee -a /root/ks-post.log
df -h  | tee -a /root/ks-post.log
echo "===== Kernel Image =====" | tee -a /root/ks-post.log
ls -l /boot/vmlinuz-* | tee -a /root/ks-post.log
ls -l /syslinux/boot/vmlinuz-* | tee -a /root/ks-post.log

echo "===== initramfs Image =====" | tee -a /root/ks-post.log
ls -l /boot/initramfs-*.img | tee -a /root/ks-post.log
ls -l /syslinux/boot/initramfs-*.img | tee -a /root/ks-post.log

# Remove unnecessary kickstart files
rm -f /root/anaconda-ks.cfg /root/ks-post.log /root/original-ks.cfg
%end
shutdown

