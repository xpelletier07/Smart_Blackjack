#!/usr/bin/env python3
"""
Contrôle du moteur de distribution de cartes depuis Raspberry Pi
Communication avec Arduino via Serial
Le Raspberry Pi lit le bouton et envoie les commandes à l'Arduino
"""

import serial
import RPi.GPIO as GPIO
import time

# Configuration
BUTTON_PIN = 17  # GPIO 17 (à adapter selon votre branchement)
BAUD_RATE = 9600
SERIAL_PORT = '/dev/ttyUSB0'  # ou '/dev/ttyACM0' selon votre Arduino

class MotorController:
    def __init__(self, button_pin, serial_port, baud_rate):
        self.button_pin = button_pin
        self.button_prev = GPIO.LOW

        try:
            self.ser = serial.Serial(serial_port, baud_rate, timeout=1)
            time.sleep(2)  # Attendre l'initialisation de l'Arduino
            print(f"Connexion établie avec Arduino sur {serial_port}")
        except Exception as e:
            print(f"Erreur de connexion Arduino: {e}")
            raise

        # Configuration GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        print("Système de distribution des cartes activé")
        print("Appuyez sur le bouton pour distribuer une carte")

    def distribute_card(self):
        """Envoie la commande pour distribuer une carte"""
        try:
            self.ser.write(b"CARD1\n")
            print("✓ Commande CARD1 envoyée à l'Arduino")
            time.sleep(3.5)  # Attendre que le moteur finisse (2 tours + délai)
        except Exception as e:
            print(f"✗ Erreur d'envoi: {e}")

    def test_motor(self):
        """Teste le moteur (1 tour)"""
        try:
            self.ser.write(b"TEST\n")
            print("✓ Commande TEST envoyée à l'Arduino")
        except Exception as e:
            print(f"✗ Erreur d'envoi: {e}")

    def listen_responses(self):
        """Écoute les réponses de l'Arduino et le bouton"""
        print("\nÉcoute active...\n")

        try:
            while True:
                # Lire l'état du bouton
                button_state = GPIO.input(self.button_pin)

                # Détection du relâchement du bouton (LOW → HIGH)
                if button_state == GPIO.HIGH and self.button_prev == GPIO.LOW:
                    print("[BOUTON] Appui détecté")
                    self.distribute_card()

                self.button_prev = button_state

                # Écouter les réponses de l'Arduino
                if self.ser.in_waiting:
                    response = self.ser.readline().decode().strip()
                    if response:
                        print(f"[ARDUINO] {response}")

                time.sleep(0.05)  # Délai court pour réactivité

        except KeyboardInterrupt:
            print("\n\nArrêt du programme...")
        finally:
            self.cleanup()

    def cleanup(self):
        """Nettoie les ressources"""
        try:
            GPIO.cleanup()
            self.ser.close()
            print("Nettoyage terminé")
        except:
            pass

def main():
    try:
        controller = MotorController(BUTTON_PIN, SERIAL_PORT, BAUD_RATE)
        controller.listen_responses()
    except Exception as e:
        print(f"Erreur fatale: {e}")

if __name__ == "__main__":
    main()
