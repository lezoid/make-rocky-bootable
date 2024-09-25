#version=RHEL9 UEFI with GUI
# System language
lang ja_JP.UTF-8
#lang en_US.UTF-8

# Keyboard layout
keyboard jp

# Timezone settings
timezone Asia/Tokyo --utc

# root user plain text password settings
rootpw --plaintext password

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
# Add UEFI Support
shim
grub2
grub2-efi
grub2-efi-*-cdboot
efibootmgr
## ---------Add Packages-----------
vi
bash-completion
langpacks-ja
glibc-langpack-ja
%end

# Post script: Configure services and system settings inside the guest
%post --log=/root/ks-post.log

##############################################################
###                       Desktop Config                   ###
##############################################################
## Setting Desktop Users (Administrator)
#useradd Administrator
#usermod -aG wheel Administrator

## Set Administrator password
#echo "Administrator:password" | chpasswd
#Encrypt Version
#echo "Administrator:PASSWORD_HASH" | chpasswd --encrypted

## Add GUI Packages
# Enable EPEL repository
dnf -y install epel-release

# Install additional packages from EPEL
dnf -y install langpacks-ja glibc-langpack-ja ibus-mozc firefox xrdp

# Install XFCE desktop environment
dnf -y groupinstall "xfce"


## create xinit files for skel, root
for path in /etc/skel /root ; do
    echo "exec /usr/bin/xfce4-session" > $path/.Xclients
    echo "exec /usr/bin/xfce4-session" > $path/.xinitrc
    chmod +x $path/.Xclients
    chmod +x $path/.xinitrc
done

## gdm autologin enable
#sed -i '1i auth sufficient pam_succeed_if.so user ingroup nopasswdlogin' /etc/pam.d/gdm-password
#groupadd nopasswdlogin
#usermod -aG nopasswdlogin Administrator

## gdm autologin setting
#bash -c 'cat <<EOL > /etc/gdm/custom.conf
## GDM configuration storage
#
#[daemon]
#AutomaticLogin=Administrator
#AutomaticLoginEnable=True
## Uncomment the line below to force the login screen to use Xorg
##WaylandEnable=false
#
#[security]
#
#[xdmcp]
#
#[chooser]
#
#[debug]
## Uncomment the line below to turn on debugging
##Enable=true
#EOL'

## gdm default session for xfce with correct Icon paths
for account in root; do
    icon_path="/home/$account/.face"
    [[ "$account" == "root" ]] && icon_path="/root/.face"
    
    sudo bash -c "cat <<EOL > /etc/accountsservice/user-templates/$account
# This file contains defaults for new users. To edit, first
# copy it to /etc/accountsservice/user-templates and make changes
# there

[com.redhat.AccountsServiceUser.System]
id=\"rocky\"
version-id=\"9.4\"

[User]
Session=xfce
Icon=$icon_path
SystemAccount=true
EOL"
done

## gdm session settings for root and Users
for useraccount in root ; do
    sudo bash -c "cat <<EOL > /var/lib/AccountsService/users/$useraccount
[User]
XSession=xfce
EOL"
done

## Ibus setting
for user in root Administrator; do
    bashrc_path="/home/$user/.bashrc"
    [[ "$user" == "root" ]] && bashrc_path="/root/.bashrc"
    
    cat <<EOL >> $bashrc_path

# IBus settings for input method
export GTK_IM_MODULE=ibus
export XMODIFIERS=@im=ibus
export QT_IM_MODULE=ibus
EOL
done

# Set graphical target as default
systemctl set-default graphical

# Enable and start xrdp
systemctl enable xrdp --now

# Open port 3389 for XRDP (TCP)
systemctl enable firewalld
firewall-offline-cmd --add-port=3389/tcp

##############################################################
###                      End Desktop Config                ###
##############################################################

# Allow SSH login as root
sed -i 's/#PermitRootLogin yes/PermitRootLogin yes/' /etc/ssh/sshd_config
sed -i 's/^#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config
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

# Cleanup operations
rm -f /core*
rm -f /var/lib/rpm/__db*
rm -f /var/lib/systemd/random-seed
rm -f /etc/machine-id
touch /etc/machine-id
rm -f /root/anaconda-ks.cfg /root/ks-post.log /root/original-ks.cfg

%end
shutdown
