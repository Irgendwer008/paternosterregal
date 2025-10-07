config_line="dtoverlay=pwm-2chan"

if ! grep -qF $config_line /boot/firmware/config.txt; then
    echo $config_line >> /boot/firmware/config.txt
    reboot now
fi
