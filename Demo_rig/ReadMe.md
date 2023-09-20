# Demo rig setup and configurations
In this file, we are going to describe how to set up the CDN Demo rig and share the configuration files

# **PXE Boot Setup for Raspberry Pi 3 Model B+/Pi 4 Model B**
This document covers all the steps on how to network boot Raspberry Pi 3B+.
It is assumed you have a working private LAN that also has access to the internet. For LAN as an example we will use 192.168.0.0/24 network

---
## Prepare the client board
---
The Raspberry Pi 3B+ comes from the factory already set for network booting

For the Raspberry Pi 4 Model B; boot the RPi with Raspberry Pi OS (Raspbian), and in the terminal enter this command:
```
sudo raspi-config
```
In the screen that pops up, go to Advanced options to change the boot order into Network Boot. Save the changes and reboot the RPi4 to go back to the terminal and check if the boot order has changed by using this command:
```
vcgencmd bootloader_config
```
Where the output should be this: BOOT_ORDER=0xf21

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
This will make it very convenient when adding more client Raspberry Pis. The only thing to do will be in editing */nfs/client/etc/fstab*, */etc/exports* and */tftpboot/client/cmdline.txt* with every additional client Raspberry Pi (client2, client3, etc.)

---
## Booting up the client Raspberry Pi
---
The PC being used to SSH will be leased an IP by the server board. SSH back to the server board and run the following command
```
sudo tail -f /var/log/syslog
```
Then plug in another Raspberry Pi (make sure there is no microSD in it). It will fail to boot. Ouch! No worries. However the command that you executed will enable you to see the something like this
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
In the /nfs/client1/etc/fstab edit as follows:
```
proc       /proc        proc     defaults    0    0
192.168.0.11:/tftpboot/client1 /boot nfs defaults,vers=3 0 0
tmpfs /tmp tmpfs defaults,noatime,nosuid 0 0
tmpfs /var/log tmpfs defaults,noatime,nosuid,size=16m 0 0
```


In the /tftpboot/client1/cmdline.txt edit as follows:
```
console=serial0,115200 console=tty1 root=/dev/nfs nfsroot=192.168.0.11:/nfs/client1,vers=3 rw ip=dhcp rootwait elevator=deadline
```
And in the /etc/exports edit as follows:
```
/nfs/client1 *(rw,sync,no_subtree_check,no_root_squash)
/tftpboot *(rw,sync,no_subtree_check,no_root_squash)
```
As you can see, what we did is only to add the number in front of 'client' (client1).

What remains is to restart the client Raspberry Pi (remove from power and power it back on, if you have a spare monitor, plug that to the client board), and Voila!

---
## Adding another client to the rig
---
At this point duplicate both client folders (in /nfs/ and /tftpboot/) as mentioned earlier with rsync as follows
```
cd /nfs
sudo rsync -xa --progress client/ client2
cd /tftpboot
sudo rsync -xa --progress client/ client2
```
Repeat what was done in the previous section (*Booting up the client Raspberry Pi*), and you will note that you will only edit the same mentioned files from 'client' to 'client2'.
This process repeats for every additional client added.

---
## Connecting to the outside world via the Server
---
This setup is if we want to connect to the internet via the server with its WiFi interface. With our setup using Raspbian Lite, you will see this message "Wi-Fi is currently blocked by rfkill". To unblock do the following on your server's terminal:
```
rfkill list
rfkill unblock 0
```
In our case identifier of device was 0 (zero).

Then edit /etc/wpa_supplicant/wpa_supplicant.conf by appending this configuration below:
```
network={
    ssid="Your Network SSID"
    psk="Your WiFi Password"
}
```
Then edit /etc/sysctl.conf file by uncommenting the line:
```
net.ipv4.ip_forward=1
```
Then we configure iptables as follows:
```
apt install iptables
sudo iptables -t nat -A POSTROUTING -o wlan0 -j MASQUERADE
sudo iptables -A FORWARD -i wlan0 -o eth0 -m state --state RELATED,ESTABLISHED -j ACCEPT
sudo iptables -A FORWARD -i eth0 -o wlan0 -j ACCEPT
sudo sh -c "iptables-save > /etc/iptables.ipv4.nat"
```
Then in /etc/rc.local file, add a line to load the tables on boot:
```
_IP=$(hostname -I) || true
if [ "$_IP" ]; then
  printf "My IP address is %s\n" "$_IP"
fi

iptables-restore < /etc/iptables.ipv4.nat

exit 0
```
Remember to comment these lines in /etc/dnsmasq.conf:
```
dhcp-option=3,192.168.0.1
dhcp-option=6,8.8.8.8,8.8.4.4
```
Then reboot. Would be good to reboot also the clients.

---
## Attaching an LCD Screen (2.8 inch LCD, 320x240 Raspberry Pi)
---
Attach the LCD screen to a client Raspberry Pi then follow the instructions provided by the LCD screen installation [documentation](https://www.waveshare.com/wiki/2.8inch_RPi_LCD_(A)) provided by Waveshare.
After the installation, edit the /tftpboot/client(x)/cmdline.txt file with the following configuration:
```
console=serial0,115200 console=tty1 root=/dev/nfs nfsroot=192.168.0.11:/nfs/client1,vers=3 rw ip=dhcp rootwait elevator=deadline fsck.repair=yes quiet splash fbcon=map:10 fbcon=font:ProFont6x11
```
Then power off and back on the client Raspberry Pi. By now, your LCD screen will display a log in prompt, perhaps with the IP address assigned to the client.

Minor update: It is wise to edit 'cmdline.txt' file in the 'LCD-show' directory just before launching/executing './LCD28-show-V2 lite'.

---
## Sources and References
---
- [GitHub](https://github.com/garyexplains/examples/blob/master/How%20to%20network%20boot%20a%20Pi%204.md) for network booting RPI4.
- [Linuxhit](https://linuxhit.com/raspberry-pi-pxe-boot-netbooting-a-pi-4-without-an-sd-card/) for Raspberry Pi PXE Boot.
