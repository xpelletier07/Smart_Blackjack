# Documentation: https://alivecode.ca/docs/aliot
from aliot.aliot_obj import AliotObj
import time
import blackjack_utils

# Création de l'objet à partir du fichier de configuration
blackjack = AliotObj("blackjack")

# Fonction pour démarrer la boucle principale   
def start():
    while True:
        try:
            # Récupération des données les plus récentes
            latest_data = blackjack_utils.get_latest_data()

            # Mise à jour des données dans l'objet AliotObj blackjack
            blackjack.update_doc({
                "/doc/action" : latest_data.action if latest_data else None,
                "/doc/moteur" : latest_data.moteur if latest_data else None,
                "/doc/nombre_tours" : latest_data.nombre_tours if latest_data else None,
                "/doc/buzzer" : latest_data.buzzer if latest_data else None,    
                "/doc/green_led" : latest_data.green_led if latest_data else None,
                "/doc/blue_led" : latest_data.blue_led if latest_data else None,
                "/doc/red_led" : latest_data.red_led if latest_data else None,
                "/doc/digit_display" : latest_data.digit_display if latest_data else None
            })

            time.sleep(1)  # Pause d'une seconde entre chaque itération
        except KeyboardInterrupt:
            print("Exiting...")
            break

# Scores saisis dans le dashboard pour la partie en cours
scores = {"/doc/score": None, "/doc/dealer_score": None}

# Envoie les scores à la route /results_game (table Results_Game) dès que les deux sont remplis
def enregistrer_scores(fields):
    for champ, valeur in fields.items():
        if valeur not in (None, ""):
            scores[champ] = valeur

    if None in scores.values():
        return

    resultat = {
        "score": int(scores["/doc/score"]),
        "dealer_score": int(scores["/doc/dealer_score"]),
        "date": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    print(f"Envoi du résultat : {resultat}")
    blackjack.send_route("/results_game", resultat)

    # On vide les champs pour la prochaine partie
    scores["/doc/score"] = None
    scores["/doc/dealer_score"] = None
    blackjack.update_doc({"/doc/score": None, "/doc/dealer_score": None})

# Appel de la fonction start une fois que l'objet se connecte au serveur
blackjack.on_start(callback=start)

# Écoute des scores saisis dans le dashboard
blackjack.listen_doc(fields=["/doc/score", "/doc/dealer_score"], callback=enregistrer_scores)

# Appel des fonctions de blackjack_utils pour contrôler les LEDs, le buzzer, l'écran LCD et effectuer des actions spécifiques
blackjack.on_action_recv(action_id="set_green_led", callback=blackjack_utils.set_green_led)
blackjack.on_action_recv(action_id="set_blue_led", callback=blackjack_utils.set_blue_led)
blackjack.on_action_recv(action_id="set_red_led", callback=blackjack_utils.set_red_led)
blackjack.on_action_recv(action_id="set_buzzer", callback=blackjack_utils.set_buzzer)
blackjack.on_action_recv(action_id="broadcast_lcd", callback=blackjack_utils.broadcast_lcd)
blackjack.on_action_recv(action_id="faire_action", callback=blackjack_utils.faire_action)
# blackjack.on_action_recv(action_id="afficher_score", callback=blackjack_utils.afficher_score)

# Connection de l'objet au serveur ALIVEcode 
blackjack.run()
