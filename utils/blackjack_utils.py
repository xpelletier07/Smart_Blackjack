import serial
import time
import threading
import math
from dataclasses import dataclass


ser = serial.Serial("COM5", 9600)

_led_state = False
_buzzer_state = False

@dataclass
class Data:
    action: str
    moteur: bool
    nombre_tours: int
    buzzer: bool

latest_data = None

def read_data() :
    data = ser.readline().decode().strip()
    action, moteur, nombre_tours, buzzer = data.split(':')
    return action, moteur, nombre_tours, buzzer

def read_from_serial():
    global latest_data
    try:
        ser.flush()
        while True:
            # Check if there is data available from Arduino
            if ser.in_waiting > 0:
                action, moteur, nombre_tours, buzzer = read_data()
                latest_data = Data(
                    action=action,
                    moteur=(moteur == "1"),
                    nombre_tours=int(nombre_tours),
                    buzzer=(buzzer == "1")
                )
                print(f"Action : {latest_data.action}, moteur actif : {latest_data.moteur}, nombre de tours : {latest_data.nombre_tours}, buzzer actif : {latest_data.buzzer} ")
                
            time.sleep(1)

    except KeyboardInterrupt:
        print("Exiting...")

    finally:
        ser.close()

#TODO
def get_latest_data():
    return latest_data

def set_led():
    pass

def get_led():
    pass

def switch_led():
    pass

def set_buzzer():
    pass

def broadcast_lcd():
    pass

def afficher_score():
    pass

def faire_action():
    pass

try:
    t = threading.Thread(target=read_from_serial)
    t.start()
except KeyboardInterrupt:
    print("Exiting...")

