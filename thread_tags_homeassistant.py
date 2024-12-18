import paho.mqtt.client as mqtt
import socket 
import logging as log
import cfg
from mqtt import mqtt_start
import json
import os
import utils as utl


def generate_config_payload(uid, name, device_class, valuetag, unit_of_measurement):
    #{"alive":8589,"voltage":3.245,"light":2266.726,"temperature":-0.56,"humidity":59.12,"pressure":1027.39}
    return {
        "name": device_class.capitalize(),
        "obj_id": "thread_sensor_tag_"+uid+"_"+valuetag,
        "~": "homeassistant/sensor/"+uid,
        "uniq_id": uid+"#"+valuetag,
        "state_topic": "~/state",
        "unit_of_measurement": unit_of_measurement,
        "device_class": device_class,
        "value_template": "{{ value_json."+valuetag+" }}",
        "force_update": True,
        "device": {
            "identifiers": [
                str(uid)
            ],
            "manufacturer": "open-things.de",
            "model": "Thread Sensor Tag",
            "name": name
        }
    }

def send_config_message(clientMQTT,uid, name, device_class, valuetag, unit_of_measurement):
    payload = generate_config_payload(uid, name, device_class, valuetag, unit_of_measurement)
    topic = "homeassistant/sensor/"+uid+"/"+device_class+"/config"
    log.info(f"'{topic}' => '{payload}'")
    clientMQTT.publish(topic, json.dumps(payload), retain=True)

def send_all_config_messages(clientMQTT, uid, name):
    send_config_message(clientMQTT, uid, name, "duration",    "alive",        "ms")
    send_config_message(clientMQTT, uid, name,"voltage",     "voltage",      "V")
    send_config_message(clientMQTT, uid, name, "temperature", "temperature",  "°C")
    send_config_message(clientMQTT, uid, name,"humidity",    "humidity",     "%")
    send_config_message(clientMQTT, uid, name, "pressure",    "pressure",     "Pa")
    send_config_message(clientMQTT, uid, name, "illuminance", "light",        "lx")


def run():
    config = cfg.configure_log(__file__)
    UDP_IP = "::" # = 0.0.0.0 u IPv4
    UDP_PORT = config["thread"]["port"]

    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM) # UDP
    sock.bind((UDP_IP, UDP_PORT))

    # will start a separate thread for looping
    clientMQTT = mqtt_start(config,None,True)

    devices = utl.load_yaml(os.path.join(os.path.dirname(__file__),"devices.yaml"))
    friendlyNames = devices["friendly_names"]["thread_tags"]

    while True:
        data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
        message = data.decode("utf-8")
        log.info("udp message: " + message)
        parts = message.split("{")
        uid = parts[0].split('/')[1]
        tag_name = "Thread Sensor Tag ["+uid+"]"
        for name,friendly_name in friendlyNames.items():
            if uid == name:
                tag_name=friendly_name
                break

        send_all_config_messages(clientMQTT, uid, tag_name)

        topic = "homeassistant/sensor/"+uid+"/state"
        payload = '{'+parts[1].rstrip('\n')
        log.info(f"'{topic}' => {payload}")
        clientMQTT.publish(topic, payload)
    return

if __name__ == '__main__':
    run()
