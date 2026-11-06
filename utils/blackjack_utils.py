import serial
import time
import threading
import math


arduino = serial.Serial("COM6", 9600)

_led_state = False
_buzzer_state = False
