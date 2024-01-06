# haiku_cam

### LCD interface
The lcd_interface.c file contains the code to interface with the 220x176 Liquid Crystal Display using the SPI communication protocol. The code uses some functionalities from the [Raspberry-ili9225spi library by nopnop2002](https://github.com/nopnop2002/Raspberry-ili9225spi). After installing this library, the lcd_interface executable can be compiled using the following command:
```
cc -o lcd_interface lcd_interface.c fontx.c ili9225.c -lbcm2835 -lm -lpthread
```

### Start Haiku Cam code on boot
To make the aws-hc.py file run on boot, a cron job was scheduled on the Raspberry Pi.

Use the following command to open crontab:
```
sudo crontab -e
```

And add the following entry:
```
@reboot sh /home/saarthak/Desktop/haiku_cam/launcher.sh > /home/saarthak/logs/cronlog 2>&1
```