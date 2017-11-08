# autoscale-verdi-amazon-ami
Configs for verdi autoscale using Amazon AMI

## Prerequisites
1. Change user to root:
   ```
   sudo su -
   ```
1. Install packages:
   ```
   yum -y install puppet nscd ntp wget curl subversion git vim screen docker docker-storage-setup
   yum groupinstall "Development Tools"
   ```
1. Create ops user:
   ```
   groupadd -g 1001 ops
   useradd -g 1001 -G wheel,docker -m ops -u 1001
   ```
1. Add sudo priveleges for ops user:
   ```
   echo "ops ALL = NOPASSWD: ALL" >> /etc/sudoers.d/cloud-init
   echo "ops ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/cloud-init
   ```
1. Copy ssh keys to ops user:
   ```
   cp -rp /home/ec2-user/.ssh /home/ops/.ssh
   chown -R ops:ops /home/ops/.ssh
   ```
1. Start docker service:
   ```
   service docker start
   ```
1. Reboot:
   ```
   reboot
   ```
1. Log in as ops user.
1. Configure AWS creds:
   ```
   aws configure
   ```
1. Install docker-compose:
   ```
   sudo curl -L https://github.com/docker/compose/releases/download/1.17.0/docker-compose-`uname -s`-`uname -m` -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   docker-compose --version
   ```
