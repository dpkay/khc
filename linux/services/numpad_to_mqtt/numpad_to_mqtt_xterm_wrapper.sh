#!/usr/bin/bash
ABS_DIR=$(dirname $(realpath $0))

xterm -e "sudo -u dpkay python3 $ABS_DIR/numpad_to_mqtt.py 1>/tmp/out 2>/tmp/err"
#xterm -e "/usr/bin/python3 1>/tmp/out 2>/tmp/err"
