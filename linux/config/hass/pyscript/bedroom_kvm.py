"""
KVM source switching for the Level1Techs KVM in the bedroom.

Stream Deck calls pyscript.set_kvm_source to switch between 4 inputs.
The input_booleans act as radio buttons for Stream Deck to display
which source is active. The actual switching happens via MQTT: a Mac
service (khc_mqtt_to_kvm) subscribes to the topic and sends the
corresponding ASCII command over USB serial to the KVM.
"""

import json

KVM_SET_SOURCE_MQTT_TOPIC = "kha/bedroom/windows_pc/kvm/set_source"

SOURCE_NAMES = [
   "personal_mac",
   "personal_windows",
   "corp_windows",
   "corp_mac",
]


@service
def set_kvm_source(source_name=None, entity_id=None):
  """Stream Deck calls this service to switch the KVM source."""
  if source_name not in SOURCE_NAMES:
    return

  # Update booleans to reflect new source (for Stream Deck display).
  for name in SOURCE_NAMES:
    bool_id = f"input_boolean.bedroom_kvm_{name}_active"
    target = "on" if name == source_name else "off"
    if state.get(bool_id) != target:
      state.set(bool_id, target)

  # Send the source change to the Mac KVM service via MQTT.
  mqtt.publish(topic=KVM_SET_SOURCE_MQTT_TOPIC,
               payload=json.dumps({"source_name": source_name}))
