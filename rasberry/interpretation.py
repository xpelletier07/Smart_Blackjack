import sys
import serial
from serial.tools import list_ports


ser = serial.Serial("COM5", 9600)
try:
    while True:
        if ser.in_waiting > 0:
            data = ser.readline().decode('utf-8', errors='replace').rstrip()
            if data:
                print(data)
except KeyboardInterrupt:
    print("Exiting...")
finally:
    ser.close()
