#
# Root firstboot startup script template
#

echo "[$(date '+%Y-%m-%d %H:%M:%S')] startup-root.sh started"

hostname localhost

## Hide login prompt os/kernel
# echo "" > /etc/issue

## Vulnerable! Root password mode
# passwd --delete username
# systemctl stop sshd

## make-rocky-bootable root firstboot script
rm -f /root/original-ks.cfg

echo "[$(date '+%Y-%m-%d %H:%M:%S')] startup-root.sh finished"
