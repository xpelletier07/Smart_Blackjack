import serial
import time
import threading
import math


ser = serial.Serial("COM6", 9600)

action = None
temps = None
moteur = False
nombre_tours = None
_led_state = False
_buzzer_state = False

def read_data() :
    data = ser.readline().decode().strip()
    action, temps, moteur, nombre_tours = data.split(':')
