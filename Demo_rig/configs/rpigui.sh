sleep 5 && \
cd /home/pi/LCD-show && \
sudo cp -rf ./usr/share/X11/xorg.conf.d/99-fbturbo.conf  /usr/share/X11/xorg.conf.d/99-fbturbo.conf && \
sleep 5 && \
startx
