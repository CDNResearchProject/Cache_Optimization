# Demo rig setup and configurations
In this file, we are going to describe how to set up the CDN Demo rig and share the configuration files

## Attaching an LCD Screen (2.8 inch LCD, 320x240 Raspberry Pi)
---
Attach the LCD screen to a client Raspberry Pi then follow the instructions provided by the LCD screen installation [documentation](https://www.waveshare.com/wiki/2.8inch_RPi_LCD_(A)) provided by Waveshare.
After the installation, edit the /tftpboot/client(x)/cmdline.txt file with the following configuration:
```
console=serial0,115200 console=tty1 root=/dev/nfs nfsroot=192.168.0.11:/nfs/client1,vers=3 rw ip=dhcp rootwait elevator=deadline fsck.repair=yes quiet splash fbcon=map:10 fbcon=font:ProFont6x11
```
Then power off and back on the client Raspberry Pi. By now, your LCD screen will display a login prompt, perhaps with the IP address assigned to the client.

Minor update: It is wise to edit 'cmdline.txt' file in the 'LCD-show' directory just before launching/executing './LCD28-show-V2' or './LCD28-show-V2 lite'.

---
## Sources and References
---
- [GitHub](https://github.com/garyexplains/examples/blob/master/How%20to%20network%20boot%20a%20Pi%204.md) for network booting RPI4 by GaryExplains.
- [Linuxhit](https://linuxhit.com/raspberry-pi-pxe-boot-netbooting-a-pi-4-without-an-sd-card/) for Raspberry Pi PXE Boot.
- [28 inch LCD setup guide](https://www.waveshare.com/wiki/2.8inch_RPi_LCD_(A)) for Raspberry Pi