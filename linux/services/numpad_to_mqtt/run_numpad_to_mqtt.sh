#!/usr/bin/bash
ABS_DIR=$(dirname $(realpath $0))

sudo xinit $ABS_DIR/numpad_to_mqtt_xterm_wrapper.sh -- :1
