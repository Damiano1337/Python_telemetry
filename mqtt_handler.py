import ssl
import json
import paho.mqtt.client as paho
from PyQt6.QtCore import QObject, pyqtSignal
from encryption_utils import decrypt_file
from config import ADMIN_PASSWORD

class MqttSignal(QObject):
    new_data = pyqtSignal(dict, str)  # emitujemy też topic

mqtt_signal = MqttSignal()
mqtt_client = None
current_user = None
user_topic = None
is_admin = False

def set_user_topic(username):
    global user_topic, is_admin
    try:
        users = decrypt_file(ADMIN_PASSWORD, filename="users.json.encrypted")
        user_topic = users[username]["topic"]
        is_admin = users[username]["role"] == "admin"
    except Exception as e:
        print("Błąd wczytywania tematu użytkownika:", e)
        user_topic = "esp32/pub"
        is_admin = False

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        payload["source_topic"] = msg.topic  # 👈 dodajemy topik do danych
        mqtt_signal.new_data.emit(payload, msg.topic)
    except Exception as e:
        print("Błąd dekodowania MQTT:", e)

def change_topic(new_topic):
    global user_topic
    if mqtt_client and user_topic != new_topic:
        try:
            mqtt_client.unsubscribe(user_topic)
            mqtt_client.subscribe(new_topic, qos=1)
            user_topic = new_topic
            print(f">>> Zmieniono topik na: {new_topic}")
        except Exception as e:
            print("Błąd przy zmianie topika:", e)



def on_disconnect(client, userdata, rc):
    print("MQTT disconnected:", rc)

def init_mqtt():
    global mqtt_client
    mqtt_client = paho.Client(client_id="", userdata=None, protocol=paho.MQTTv5)
    mqtt_client.on_message = on_message
    mqtt_client.on_disconnect = on_disconnect
    mqtt_client.tls_set(tls_version=ssl.PROTOCOL_TLS)
    mqtt_client.username_pw_set("dataServer", "Hydrive1")
    mqtt_client.connect("6aa9c1de47b0404e82629f1961517374.s1.eu.hivemq.cloud", 8883)

    if is_admin:
        mqtt_client.subscribe("#", qos=1)  # Admin widzi wszystko
    else:
        mqtt_client.subscribe(user_topic, qos=1)

    mqtt_client.loop_start()
