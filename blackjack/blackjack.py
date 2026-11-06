# Documentation: https://alivecode.ca/docs/aliot
from aliot.aliot_obj import AliotObj
import time
import utils.blackjack_utils

# Création de l'objet à partir du fichier de configuration
blackjack = AliotObj("blackjack")

# Fonction pour démarrer la boucle principale
def start():
    while True:
        try:
            # Récupération des données les plus récentes
            latest_data = utils.blackjack_utils.get_latest_data()

            # Mise à jour des données dans l'objet AliotObj blackjack
            blackjack.update_doc({
                "/doc/action" : latest_data.action if latest_data else None,
                "/doc/moteur" : latest_data.moteur if latest_data else None,
                "/doc/nombre_tours" : latest_data.nombre_tours if latest_data else None,
                "/doc/buzzer" : latest_data.buzzer if latest_data else None,    
                "/doc/green_led" : latest_data.green_led if latest_data else None,
                "/doc/blue_led" : latest_data.blue_led if latest_data else None,
                "/doc/red_led" : latest_data.red_led if latest_data else None
            })

            time.sleep(1)  # Pause d'une seconde entre chaque itération
        except KeyboardInterrupt:
            print("Exiting...")
            break

# Appel de la fonction start une fois que l'objet se connecte au serveur
blackjack.on_start(callback=start)

# Appel des fonctions de utils.blackjack_utils pour contrôler les LEDs, le buzzer, l'écran LCD et effectuer des actions spécifiques
blackjack.on_action_recv(action_id="set_green_led", callback=utils.blackjack_utils.set_green_led)
blackjack.on_action_recv(action_id="set_blue_led", callback=utils.blackjack_utils.set_blue_led)
blackjack.on_action_recv(action_id="set_red_led", callback=utils.blackjack_utils.set_red_led)
blackjack.on_action_recv(action_id="set_buzzer", callback=utils.blackjack_utils.set_buzzer)
blackjack.on_action_recv(action_id="broadcast_lcd", callback=utils.blackjack_utils.broadcast_lcd)
blackjack.on_action_recv(action_id="faire_action", callback=utils.blackjack_utils.faire_action)

# Connection de l'objet au serveur ALIVEcode 
blackjack.run()
