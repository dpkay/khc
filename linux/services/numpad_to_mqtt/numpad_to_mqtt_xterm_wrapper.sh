#!/usr/bin/bash
ABS_DIR=$(dirname $(realpath $0))

source /home/dpkay/khc-private/bashrc
xterm -e "sudo -u dpkay MQTT_USER=$MQTT_USER MQTT_PASSWORD=$MQTT_PASSWORD python3 $ABS_DIR/numpad_to_mqtt.py 1>/tmp/numpad_to_mqtt_stdout 2>/tmp/numpad_to_mqtt_stderr"
#xterm -e "/usr/bin/python3 1>/tmp/out 2>/tmp/err"
