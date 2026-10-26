import sys
import serial
from serial.tools import list_ports


def find_serial_port():
    ports = list_ports.comports()
    if not ports:
        raise RuntimeError("No serial port found. Connect the Arduino and check Device Manager.")

    # Prefer a non-default COM1 if another Arduino port is available
    candidates = [p.device for p in ports if p.device.upper() != 'COM1']
    return candidates[0] if candidates else ports[0].device


try:
    port = find_serial_port()
    print(f"Connecting to {port}...")
    ser = serial.Serial(port, 9600, timeout=1)

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

except Exception as exc:
    print(f"Could not open serial port: {exc}")
    print("Available ports:")
    for p in list_ports.comports():
        print(f" - {p.device} : {p.description}")
    sys.exit(1)