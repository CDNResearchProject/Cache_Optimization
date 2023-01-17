# Demo rig setup and configurations
In this file, we are going to describe how to set up the CDN Demo rig and share the configuration files

# **PXE Boot Setup for Raspberry Pi 3 Model B+**
This document covers all the steps on how to network boot Raspberry Pi 3B+.
It is assumed you have a working private LAN that also has access to the internet. For LAN as an example we will use 192.168.0.0/24 network

---
## Prepare the client board
---
The Raspberry Pi 3B+ comes from the factory already set for network booting

---
## Prepare the server board
---
You need to create a Raspberry Pi OS on an microSD card. In this case a [Raspberry Pi Imager](https://www.raspberrypi.com/software/) was used after being installed in a Windows 10 laptop.
- for OS we used [Raspberry Pi OS Lite 64-bit](https://downloads.raspberrypi.org/raspios_lite_arm64/images/raspios_lite_arm64-2022-09-26/2022-09-22-raspios-bullseye-arm64-lite.img.xz)
 - for storage, choose the microSD card slotted in you reader
 - select the cogwheel to enable SSH and write a default password
 - select *write*

Slot the microSD into the Raspberry Pi, connect the STP/UTP cable and power it on. After it has booted, check your switch to see what IP has been leased to the board, and use that to SSH to the board
```
ssh -l pi 192.168.0.37
```
Supply the password you set during preparation of the microSD

**Install the packages needed**

```
sudo apt update
sudo apt upgrade
sudo apt install nfs-kernel-server dnsmasq rsync tcpdump
```

**Create the root file system that will be served over NFS**

The client Raspberry Pi will need a root file system to boot from. We will use a copy of the root file system and place it in /nfs/client
```
sudo mkdir -p /nfs/client
sudo rsync -xa --progress --exclude /nfs / /nfs/client
```
Delete SSH keys and enable the ssh server
```
cd /nfs/client
sudo mount --bind /dev dev
sudo mount --bind /sys sys
sudo mount --bind /proc proc
sudo chroot . rm -f /etc/ssh/ssh_host_*
sudo chroot . dpkg-reconfigure openssh-server
sudo chroot . systemctl enable ssh
sleep 1
sudo umount dev sys proc
sudo touch boot/ssh
```
Configure fstab (/nfs/client/etc/fstab) for the client to mount via NFS. This will tell the client to mount its root volume off the NFS server on our PXE boot server
```
proc       /proc        proc     defaults    0    0
192.168.0.11:/tftpboot/client /boot nfs defaults,vers=3 0 0
tmpfs /tmp tmpfs defaults,noatime,nosuid 0 0
tmpfs /var/log tmpfs defaults,noatime,nosuid,size=16m 0 0
```
Export the root file system created earlier, and the TFTP boot folder. To do this configure /etc/exports as follows
```
/nfs/client *(rw,sync,no_subtree_check,no_root_squash)
/tftpboot *(rw,sync,no_subtree_check,no_root_squash)
```

**Setting up the TFTP**

```
sudo mkdir -p /tftpboot/client
sudo chmod 777 /tftpboot
sudo cp -r /boot/* /tftpboot/client
sudo cp /boot/bootcode.bin /tftpboot/
```
Configure dnsmasq (/etc/dnsmasq.conf) configuration file with the following contents. Mostly you will be uncommenting and slightly editing configurations which are already present
```
interface=eth0
no-hosts
dhcp-range=192.168.0.101,192.168.0.200,12h
log-dhcp
enable-tftp
tftp-root=/tftpboot
pxe-service=0,"Raspberry Pi Boot"
dhcp-option=3,192.168.0.1
dhcp-option=6,8.8.8.8,8.8.4.4
```
Configure the cmdline.txt file for the client
```
console=serial0,115200 console=tty1 root=/dev/nfs nfsroot=192.168.0.11:/nfs/client,vers=3 rw ip=dhcp rootwait elevator=deadline
```
Then execute the command
```
sudo chmod 777 /tftpboot/client/cmdline.txt
```

**Setting a fixed IP address for the PXE server board**

Edit the dhcpcd file (/etc/dhcpcd.conf) and put the following configurations. Again, mostly will be uncommenting with minor edits. This will assign a fixed IP to our PXE boot server Raspberry Pi
```
interface eth0
static ip_address=192.168.0.11/24
static routers=192.168.0.1
static domain_name_servers=8.8.8.8 8.8.4.4
```
Remember to change `192.168.0.11` to fit your network setup

At this point, if you have a switch/router with DHCP capabilities in your LAN, disable that

**Restart all services**

```
sudo systemctl enable dnsmasq
sudo systemctl restart dnsmasq
sudo systemctl enable rpcbind
sudo systemctl restart rpcbind
sudo systemctl enable nfs-kernel-server
sudo systemctl restart nfs-kernel-server
sudo reboot
```
At this point it would be good to duplicate both *client* folders (in /nfs/ and in /tftpboot/)
```
sudo rsync -xa --progress client/ client1
```
This will make it very convenient when adding more client Raspberry Pis. The only hustle will be in editing *fstab*, *exports* and *cmdline.txt* with every additional client Raspberry Pi (client2, client3, etc.)

---
## Booting up the client Raspberry Pi
---
The PC being used to SSH will be leased an IP by the server board. SSH back to the server board and run the following command
```
sudo tail -f /var/log/syslog
```
Then plug in another Raspberry Pi (make sure there is no microSD in it). It will fail to boot. Ouch! Sorry to have wasted your time, all this was a prank! Hey, just joking. However the command that you executed will enable you to see the something like this
```
...
Dec 15 14:05:30 rpinetboot dnsmasq-tftp[511]: failed sending /tftpboot/f9c26df7/start.elf to 192.168.0.111
...
```
Copy only that f9c26df7 which is a serial number of the client board you just tried to boot in order to make a symbolic link as follows
```
cd /tftpboot
sudo ln -s client1 f9c26df7
```
What remains is to restart the client Raspberry Pi (remove from power and power it back on, if you have a spare monitor, plug that to the client board), and Voila!
