# To run this on Windows, a few steps are needed.
#
# 1. Download Python from python.org, and install dependencies:
#
#     python.exe -m pip install pygame
#     python.exe -m pip install paho-mqtt
#
# 2. Install LoopMIDI and make sure it is always running.
#
# 3. Install the Studio One DAW, and make sure it is loaded with our song.

import json
import pygame.midi
import time
import paho.mqtt.client

MQTT_CLIENT_NAME = "mqtt_from_and_to_windows"
MQTT_TOPIC_PREFIX = "kha/bedroom/windows_pc"
NUM_UPDATES_PER_SECOND = 50.0

EXAMPLE_MQTT_PARAMS = {
    "input__piano": 0.5,
    "input__windows_desktop": 0.5,
    "input__windows_laptop": 0.5,
    "input__external_laptop": 0.5,
    "output__piano_speakers": 0.5,
    "output__desk_speakers": 0.5,
    "output__regular_headphones": 0.5,
    "output__inverted_headphones": 0.5,
}


def create_midi_devices(buffer_size):
    count = pygame.midi.get_count()
    sparrow_device_ids = []
    loopmidi_device_ids = []
    for i in range(count):
        dev = pygame.midi.get_device_info(i)
        name = dev[1].decode("ascii")
        num_inputs = dev[2]
        num_outputs = dev[3]
        if name == "Sparrow 5x100" and num_inputs == 1 and num_outputs == 0:
            sparrow_device_ids.append(i)
        elif name == "LoopMIDI" and num_inputs == 0 and num_outputs == 1:
            loopmidi_device_ids.append(i)

    if len(sparrow_device_ids) != 1:
        raise Exception(
            "Unable to find exactly one Sparrow fader device. "
            f"Number found: {len(sparrow_device_ids)}"
        )
    if len(loopmidi_device_ids) != 1:
        raise Exception(
            "Unable to find exactly one LoopMIDI fader device. "
            f"Number found: {len(loopmidi_device_ids)}"
        )
    sparrow_input_device = pygame.midi.Input(sparrow_device_ids[0], buffer_size)
    loopmidi_output_device = pygame.midi.Output(loopmidi_device_ids[0])
    return (sparrow_input_device, loopmidi_output_device)


def midi_params_from_mqtt_params(mqtt_params):
    """
    For an example of MQTT params, look at EXAMPLE_MQTT_PARAMS.

    This function converts MQTT params to MIDI params. Those look as follows:
        [
            [15,  # channel
             0,   # control ID
             0.3  # normalized value
            ], ...
        ]
    """
    midi_params = []

    def maybe_assign(channel, controller, key):
        try:
            midi_params.append([channel, controller, mqtt_params[key]])
        except KeyError:
            pass

    maybe_assign(channel=0, controller=0, key="input__piano")
    maybe_assign(channel=0, controller=1, key="input__windows_desktop")
    maybe_assign(channel=0, controller=2, key="input__windows_laptop")
    maybe_assign(channel=0, controller=3, key="input__external_laptop")

    maybe_assign(channel=0, controller=16, key="output__piano_speakers")
    maybe_assign(channel=0, controller=17, key="output__desk_speakers")
    maybe_assign(channel=0, controller=18, key="output__regular_headphones")
    maybe_assign(channel=0, controller=19, key="output__inverted_headphones")

    return midi_params


def send_midi_params_to_loopmidi(midi_params, loopmidi_output_device):
    for channel_id, controller_id, value_normalized in midi_params:
        midi_status = 0xB0 + channel_id  # 0xB0 = Channel 0 control signal.
        value_7bit = int(value_normalized * 127)
        loopmidi_output.write_short(midi_status, controller_id, value_7bit)


def on_mqtt_connected(client, userdata, flags, rc):
    print("Connected with result code {0}".format(str(rc)))
    client.subscribe(f"{MQTT_TOPIC_PREFIX}/daw/#")


def on_mqtt_message_received(client, userdata_loopmidi_output_device, msg):
    # Decode payload.
    payload_decoded = msg.payload.decode("utf-8", "ignore")
    try:
        payload_json = json.loads(payload_decoded)
    except Exception as e:
        print(f"Unable to decode payload '{payload_decoded}':", e)
        return

    # Uncomment the following for debugging the received payload.
    # print(json.dumps(payload_json, indent=2))

    # Now act based on the topic name.
    if msg.topic == f"{MQTT_TOPIC_PREFIX}/daw/set_params":
        midi_params = midi_params_from_mqtt_params(payload_json)
        send_midi_params_to_loopmidi(midi_params, userdata_loopmidi_output_device)


def mqtt_publish_fader_values(client, fader_value_by_id):
    values_json = json.dumps(fader_value_by_id)
    client.publish(f"{MQTT_TOPIC_PREFIX}/faders", values_json)


def send_example_midi_params_to_loopmidi(loopmidi_output_device):
    midi_params = midi_params_from_mqtt_params(EXAMPLE_MQTT_PARAMS)
    send_midi_params_to_loopmidi(midi_params, loopmidi_output_device)


if __name__ == "__main__":
    # If anything breaks at runtime, just restart automatically.
    while True:
        try:
            # Setup MIDI I/O.
            print("Attempting to find MIDI device...")
            pygame.midi.init()  # Safe to call more than once according to pygame.org.

            sparrow_input, loopmidi_output = create_midi_devices(buffer_size=10000)
            send_example_midi_params_to_loopmidi(loopmidi_output)

            # Setup MQTT.
            print("Attempting to connect to MQTT broker...")
            mqtt_client = paho.mqtt.client.Client(MQTT_CLIENT_NAME)
            mqtt_client.on_connect = on_mqtt_connected
            mqtt_client.on_message = on_mqtt_message_received
            mqtt_client.user_data_set(loopmidi_output)
            mqtt_client.connect("192.168.1.11", 1883)

            # Main event loop.
            while True:
                events = sparrow_input.read(num_events=1000)
                fader_value_by_id = {}
                for event in events:
                    status = event[0][0]
                    if status == 0xBF:  # Channel 16 control signal.
                        fader_id_raw = event[0][1]
                        value = event[0][2]

                        # Sparrow sends the fader id as zero-based, but for downstream consumption one-based makes more sense.
                        fader_id = fader_id_raw + 1

                        # Now store the latest value in the dictionary.
                        fader_value_by_id[fader_id] = value / 127

                if fader_value_by_id:
                    mqtt_publish_fader_values(mqtt_client, fader_value_by_id)

                mqtt_client.loop(1.0 / NUM_UPDATES_PER_SECOND)

        except Exception as e:
            print("Error:", e)
            print("Retrying in 1 second.")
            time.sleep(1)
