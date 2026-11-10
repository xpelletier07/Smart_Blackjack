# Documentation: https://alivecode.ca/docs/aliot
from aliot.aliot_obj import AliotObj

# Création de l'objet à partir du fichier de configuration
blackjack = AliotObj("blackjack")
import blackjack_utils


def start():
    # Dernières données envoyées, pour éviter de mettre à jour le doc inutilement
    previous_doc = None

    while True:
        try:
            # Récupération des données les plus récentes
            latest_data = blackjack_utils.get_latest_data()

            new_doc = {
                "/doc/action" : latest_data.action if latest_data else None,
                "/doc/moteur" : latest_data.moteur if latest_data else None,
                "/doc/nombre_tours" : latest_data.nombre_tours if latest_data else None,
                "/doc/buzzer" : latest_data.buzzer if latest_data else None,
                "/doc/green_led" : latest_data.green_led if latest_data else None,
                "/doc/blue_led" : latest_data.blue_led if latest_data else None,
                "/doc/red_led" : latest_data.red_led if latest_data else None,
                "/doc/digit_display" : latest_data.digit_display if latest_data else None
            }

            # Mise à jour des données dans l'objet AliotObj blackjack seulement si elles ont changé
            if new_doc != previous_doc:
                blackjack.update_doc(new_doc)
                previous_doc = new_doc

            time.sleep(1)  # Pause d'une seconde entre chaque itération
        except KeyboardInterrupt:
            print("Exiting...")
            break

# Appel de la fonction start une fois que l'objet se connecte au serveur
blackjack.on_start(callback=start)

# Connection de l'objet au serveur ALIVEcode
blackjack.run()
