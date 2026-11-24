# Documentation: https://alivecode.ca/docs/aliot
from aliot.aliot_obj import AliotObj
import os
import threading
import time
import blackjack_utils
from detection_action import lancer_detection

# Création de l'objet à partir du fichier de configuration
blackjack = AliotObj("blackjack")
import blackjack_utils

# Fonction pour démarrer la boucle principale   
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

# Scores saisis dans le dashboard pour la partie en cours
scores = {"score": None, "dealer_score": None}

# Enregistre un score reçu du dashboard, puis envoie le résultat à la route /results_game
# (table Results_Game) dès que les deux scores sont remplis
def enregistrer_score(nom, valeur):
    try:
        scores[nom] = int(valeur)
    except (TypeError, ValueError):
        print(f"Score invalide pour {nom} : {valeur!r}")
        return

    blackjack.update_doc({f"/doc/{nom}": scores[nom]})

    if None in scores.values():
        return

    resultat = {
        "score": scores["score"],
        "dealer_score": scores["dealer_score"],
        "date": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    print(f"Envoi du résultat : {resultat}")
    blackjack.send_route("/results_game", resultat)

    # On vide les scores pour la prochaine partie
    scores["score"] = None
    scores["dealer_score"] = None

def send_score(valeur):
    enregistrer_score("score", valeur)

def send_dealer_score(valeur):
    enregistrer_score("dealer_score", valeur)

# Action reconnue par les doigts : envoyée à l'Arduino et à AliveCode
def envoyer_action(action):
    print(f"Action reconnue : {action}")
    blackjack_utils.faire_action(action)
    blackjack.update_doc({"/doc/action": action})

# Appel de la fonction start une fois que l'objet se connecte au serveur
blackjack.on_start(callback=start)

# Réception des scores entrés avec les prompts du dashboard
blackjack.on_action_recv(action_id="send_score", callback=send_score)
blackjack.on_action_recv(action_id="send_dealer_score", callback=send_dealer_score)

# Appel des fonctions de blackjack_utils pour contrôler les LEDs, le buzzer, l'écran LCD et effectuer des actions spécifiques
blackjack.on_action_recv(action_id="set_green_led", callback=blackjack_utils.set_green_led)
blackjack.on_action_recv(action_id="set_blue_led", callback=blackjack_utils.set_blue_led)
blackjack.on_action_recv(action_id="set_red_led", callback=blackjack_utils.set_red_led)
blackjack.on_action_recv(action_id="set_buzzer", callback=blackjack_utils.set_buzzer)
blackjack.on_action_recv(action_id="broadcast_lcd", callback=blackjack_utils.broadcast_lcd)
blackjack.on_action_recv(action_id="faire_action", callback=blackjack_utils.faire_action)
# blackjack.on_action_recv(action_id="afficher_score", callback=blackjack_utils.afficher_score)

# Connection de l'objet au serveur ALIVEcode, en arrière-plan
threading.Thread(target=blackjack.run, daemon=True).start()

# Reconnaissance des doigts dans le programme principal (la fenêtre OpenCV doit y rester).
# Les actions faites avant la connexion à AliveCode vont seulement à l'Arduino.
lancer_detection(envoyer_action)

# Touche q dans la fenêtre : on arrête tout (la lecture série de blackjack_utils ne s'arrête pas seule)
blackjack.stop()
os._exit(0)
