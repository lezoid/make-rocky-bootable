#
# Setting Startup User Scripts
#
### Set User Script
hostname localhost

## Hide Login Pronpt os/kernel
# echo "" > /etc/issue

##Vulnerable!! Root Password mode
# passwd --delete username
# systemctl stop sshd

### make-rocky-bootable last initilized Script
rm -f /root/original-ks.cfg
