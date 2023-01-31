#!/usr/bin/python3
import pygtrie
import khafe_common
import termios, fcntl, sys, os

import paho.mqtt.client
import time

def on_mqtt_connect(client, userdata, flags, rc):
    if rc == 0:

        print("mqtt_connected to broker")

        global mqtt_connected                #Use global variable
        mqtt_connected = True                #Signal connection

    else:

        print("Connection failed")

mqtt_connected = False   #global variable for the state of the connection

#broker_address= "m11.cloudmqtt.com"
#port = 12948

mqtt_client = paho.mqtt.client.Client("tty2mqtt")               #create new instance
mqtt_client.on_connect = on_mqtt_connect                      #attach function to callback
while True:
  print("Attempting to connect...")
  try:
    mqtt_client.connect('127.0.0.1', 1883)
  except ConnectionRefusedError as e:
    print("Unable to connect:", e)
    print("Retrying in 5 seconds.")
    time.sleep(5)
    continue
  break

mqtt_client.loop_start()        #start the loop

while mqtt_connected != True:    #Wait for connection
    time.sleep(0.1)


def on_key_pressed(name):
  print(name)
  payload={"key":name}
  mqtt_client.publish("livingroom/numpad", f'{{"key": "{name}"}}')
  #if name == "one":
  #  khafe_common.run_hass_script("bedroom_device_closet_light_toggle")
  #else:
  #  print("Unbound key:", name)

# Creates a Trie specifically for the Fosmon numkey pad.
# https://www.amazon.com/gp/product/B09NRZCJRQ/
def make_key_name_by_char_sequence_trie():
  trie = pygtrie.CharTrie()
  trie['1'] = 'one'
  trie['\x1b[4~'] = 'one'
  trie['2'] = 'two'
  trie['\x1b[B'] = 'two'
  trie['3'] = 'three'
  trie['\x1b[6~'] = 'three'
  trie['4'] = 'four'
  trie['\x1b[D'] = 'four'
  trie['5'] = 'five'
  trie['\x1b[G'] = 'five'
  trie['6'] = 'six'
  trie['\x1b[C'] = 'six'
  trie['7'] = 'seven'
  trie['\x1b[1~'] = 'seven'
  trie['8'] = 'eight'
  trie['\x1b[A'] = 'eight'
  trie['9'] = 'nine'
  trie['\x1b[5~'] = 'nine'
  trie['0'] = 'zero'
  trie['\x1b[2~'] = 'zero'
  trie['.'] = 'dot'
  trie['\x1b[3~'] = 'dot'
  trie['='] = 'equals'
  trie['/'] = 'slash'
  trie['*'] = 'asterisk'
  trie['-'] = 'minus'
  trie['+'] = 'plus'
  trie['\n'] = 'enter'
  trie['\t'] = 'tab'
  trie['\x7f'] = 'backspace'
  #trie['\x1b'] = 'escape'
  return trie

class TrieReader:
  def __init__(self, trie, on_match):
    self.buffer = ''
    self.trie = trie
    self.on_match = on_match

  def on_char(self, ch):
    self.buffer += ch

    # Query the trie.
    result = self.trie.has_node(self.buffer)

    if result == pygtrie.Trie.HAS_SUBTRIE:
      # Keep reading as there is a subtrie.
      return

    else:
      if result == pygtrie.Trie.HAS_VALUE:
        self.on_match(self.trie[self.buffer])

      # In any case, there is no subtrie, so restart the buffer.
      self.buffer = ''


if __name__ == "__main__":
  # Setup key reading infrastructure.
  fd = sys.stdin.fileno()
  oldterm = termios.tcgetattr(fd)
  newattr = termios.tcgetattr(fd)
  newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
  termios.tcsetattr(fd, termios.TCSANOW, newattr)
  oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
  fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

  # Setup trie traversal infrastructure.
  key_name_by_char_sequence_trie = make_key_name_by_char_sequence_trie()
  trie_reader = TrieReader(key_name_by_char_sequence_trie, on_key_pressed)

  # Start reading keys:
  try:
    while True:
      try:
        c = sys.stdin.read(1)
        if c:
          print(repr(c))
          trie_reader.on_char(c)
      except IOError:
        pass
  finally:
    termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)

#try:
#    while True:
#        value = raw_input('Enter the message:')
#
#except KeyboardInterrupt:
#
#    client.disconnect()
#    client.loop_stop()
