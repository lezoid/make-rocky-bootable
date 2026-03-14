#
# Root firstboot startup script template
#

hostname localhost

## Hide login prompt os/kernel
# echo "" > /etc/issue

## Vulnerable! Root password mode
# passwd --delete username
# systemctl stop sshd

## make-rocky-bootable root firstboot script
rm -f /root/original-ks.cfg
