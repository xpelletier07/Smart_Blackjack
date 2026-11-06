import serial
import time
import threading
import math
from dataclasses import dataclass


ser = serial.Serial("COM5", 9600)

@dataclass
class Data:
    action: str
    moteur: bool
    nombre_tours: int
    buzzer: bool
    green_led: bool
    blue_led: bool
    red_led: bool

latest_data = None

def read_data() :
    data = ser.readline().decode().strip()
    action, moteur, nombre_tours, buzzer, green_led, blue_led, red_led = data.split(':')
    return action, moteur, nombre_tours, buzzer, green_led, blue_led, red_led

def read_from_serial():
    global latest_data
    try:
        ser.flush()
        while True:
            # Check if there is data available from Arduino
            if ser.in_waiting > 0:
                action, moteur, nombre_tours, buzzer, green_led, blue_led, red_led = read_data()
                latest_data = Data(
                    action=action,
                    moteur=(moteur == "1"),
                    nombre_tours=int(nombre_tours),
                    buzzer=(buzzer == "1"),
                    green_led=(green_led == "1"),
                    blue_led=(blue_led == "1"),
                    red_led=(red_led == "1")
                )
                print(f"Action : {latest_data.action}, moteur actif : {latest_data.moteur}, nombre de tours : {latest_data.nombre_tours}, buzzer actif : {latest_data.buzzer} ")
                print(f"LED States - Green: {latest_data.green_led}, Blue: {latest_data.blue_led}, Red: {latest_data.red_led}")

            time.sleep(1)

    except KeyboardInterrupt:
        print("Exiting...")

    finally:
        ser.close()


def get_latest_data():
    return latest_data

# Contrôle de la LED verte
def set_green_led():
    print("Appel de set_green_led()")
    if latest_data and latest_data.green_led:
        ser.write(b'GREEN_LED_OFF\n')
    else:
        ser.write(b'GREEN_LED_ON\n')

def get_green_led():
    return latest_data.green_led if latest_data else None

def switch_green_led():
    latest_data.green_led = not latest_data.green_led
    set_green_led()

# Contrôle de la LED bleue
def set_blue_led():
    print("Appel de set_blue_led()")
    if latest_data and latest_data.blue_led:
        ser.write(b'BLUE_LED_OFF\n')
    else:
        ser.write(b'BLUE_LED_ON\n')

def get_blue_led():
    return latest_data.blue_led if latest_data else None

def switch_blue_led():
    latest_data.blue_led = not latest_data.blue_led
    set_blue_led()

# Contrôle de la LED rouge
def set_red_led():
    print("Appel de set_red_led()")
    if latest_data and latest_data.red_led:
        ser.write(b'RED_LED_OFF\n')
    else:
        ser.write(b'RED_LED_ON\n')

def get_red_led():
    return latest_data.red_led if latest_data else None

def switch_red_led():
    latest_data.red_led = not latest_data.red_led
    set_red_led()

# Contrôle du buzzer
def set_buzzer():
    print("Appel de set_buzzer()")
    if latest_data and latest_data.buzzer:
        ser.write(b'BUZZER_OFF\n')
    else:
        ser.write(b'BUZZER_ON\n')

# Affichage du message sur l'écran LCD
def broadcast_lcd(message):
    print(f"Appel de broadcast_lcd({message})")
    if (message):
        ser.write(f'LCD:{message}\n'.encode())

# Envoie une action à l'Arduino
def faire_action(action):
    print(f"Appel de faire_action({action})")
    if (action):
        ser.write(f'ACTION:{action}\n'.encode())

# J'en ai aucune calisse d'idée de comment faire ça
def afficher_score():
    pass


try:
    t = threading.Thread(target=read_from_serial)
    t.start()
except KeyboardInterrupt:
    print("Exiting...")

