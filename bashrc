# Run KHAFE if we are running from tty1 (i.e. the first session with the
# keyboard physically connected to the decive) and are also a login shell.
# The idea is that this only runs at bootup time.
if [[ `tty` == "/dev/tty1" ]] ; then
  if shopt -q login_shell ; then
    # Start services in one tab per service, then the keyboard client last so it ends up in front.
    tm new-session \
        \; send-keys "cd ~/kha && docker compose up" C-m \; new-window \
        \; send-keys ~/kha/services/mqtt_to_soundmix.py C-m \; new-window \
        \; send-keys ~/kha/scripts/khafe_keyboard_client.py C-m
  fi
fi

export KHA_ROOT_DIR=$HOME/kha
export KHA_CONFIG_DIR=$KHA_ROOT_DIR/config
