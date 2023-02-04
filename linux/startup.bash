#!/usr/bin/bash

# Set up environment.
export KHC_ROOT=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )/.." &> /dev/null && pwd )

# Disable key repeat (for numpad).
setterm -repeat off

# Run tmux containing all services if we are running from tty1 (i.e. the first session with the
# keyboard physically connected to the decive) and are also a login shell.
# The idea is that this only runs at bootup time.
if [[ `tty` == "/dev/tty1" ]] ; then
    if shopt -q login_shell ; then
        # Start services in one tab per service, then the keyboard client last so it ends up in front.
        tm new-session \
        \; send-keys "docker-compose -f $KHC_ROOT/linux/docker-compose.yaml up" C-m \; new-window \
        \; send-keys $KHC_ROOT/linux/services/mqtt_to_shield/mqtt_to_shield.py C-m \; new-window \
        \; send-keys $KHC_ROOT/linux/services/numpad_to_mqtt/run_numpad_to_mqtt.sh C-m
    fi
fi