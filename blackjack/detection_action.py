import math
import time
import cv2
import mediapipe as mp
import flux_web  # diffusion web : port 5000 (page) et 5001 (flux seul)

# Initialisation MediaPipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.75)

# Mapping exact attendu par faireAction() dans l'Arduino
ACTIONS_BLACKJACK = {
    0: "Double",  # poing
    1: "Hit",
    2: "Split",
    5: "Stand"    # main ouverte
}

TEMPS_CONFIRMATION = 1.5

# Pause (en secondes) après une action, le temps que l'Arduino distribue les cartes :
# le moteur tourne à 15 tr/min, donc 4 s par carte, + 2 s d'affichage sur l'Arduino
DELAI_APRES_ACTION = {
    "Stand": 2,
    "Hit": 6,     # 1 carte
    "Double": 6,  # 1 carte
    "Split": 10   # 2 cartes
}

# Un doigt est levé si son bout est plus loin du poignet que son articulation du milieu.
# Plus haut = il faut tendre le doigt davantage pour qu'il compte.
SEUIL_DOIGT = 1.1
# Le pouce est levé si son bout est plus loin de la base de l'auriculaire que son articulation
SEUIL_POUCE = 1.1


def compter_doigts(points, largeur, hauteur):
    """Nombre de doigts levés. On compare des distances plutôt que des hauteurs (y),
    pour que le comptage marche même si la main est penchée ou tournée."""
    def distance(a, b):
        # x et y vont de 0 à 1 : on les remet en pixels pour ne pas déformer les distances
        return math.hypot((points[a].x - points[b].x) * largeur, (points[a].y - points[b].y) * hauteur)

    doigts_leves = 0

    # Pouce : replié, son bout (4) revient vers la base de l'auriculaire (17)
    if distance(4, 17) > distance(3, 17) * SEUIL_POUCE:
        doigts_leves += 1

    # 4 autres doigts (Index, Majeur, Annulaire, Auriculaire) : bout comparé à l'articulation
    # du milieu (bout - 2), par rapport au poignet (0)
    for bout in [8, 12, 16, 20]:
        if distance(bout, 0) > distance(bout - 2, 0) * SEUIL_DOIGT:
            doigts_leves += 1

    return doigts_leves


def lancer_detection(envoyer):
    """Lit la webcam, affiche la fenêtre et appelle envoyer(action) à chaque action
    validée. Retourne quand on appuie sur q dans la fenêtre."""
    dernier_geste = None
    debut_geste = 0
    action_deja_envoyee = False
    action_validee = "Aucune"
    fin_pause = 0

    cap = cv2.VideoCapture(0)
    flux_web.demarrer()

    while cap.isOpened():
        succes, image = cap.read()
        if not succes:
            break

        image = cv2.flip(image, 1)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        resultats = hands.process(image_rgb)

        action_detectee = None
        hauteur, largeur = image.shape[:2]

        if resultats.multi_hand_landmarks:
            for hand_landmarks in resultats.multi_hand_landmarks:
                mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                doigts_leves = compter_doigts(hand_landmarks.landmark, largeur, hauteur)
                action_detectee = ACTIONS_BLACKJACK.get(doigts_leves, None)

                # Pour vérifier le comptage à l'écran
                cv2.putText(image, f"Doigts : {doigts_leves}", (20, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 0), 2)

        # Pause pendant la distribution des cartes : on ignore les gestes
        if time.time() < fin_pause:
            dernier_geste = None
            action_deja_envoyee = False
            cv2.putText(image, f"Distribution... {fin_pause - time.time():.0f} s", (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        # Validation et appel de faire_action()
        elif action_detectee:
            if action_detectee == dernier_geste:
                temps_ecoule = time.time() - debut_geste
                progression = min(int((temps_ecoule / TEMPS_CONFIRMATION) * 100), 100)

                cv2.putText(image, f"Maintenir : {action_detectee} ({progression}%)", (20, 50),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

                if temps_ecoule >= TEMPS_CONFIRMATION and not action_deja_envoyee:
                    action_validee = action_detectee
                    envoyer(action_validee)
                    action_deja_envoyee = True
                    fin_pause = time.time() + DELAI_APRES_ACTION[action_validee]
            else:
                dernier_geste = action_detectee
                debut_geste = time.time()
                action_deja_envoyee = False
        else:
            dernier_geste = None
            action_deja_envoyee = False
            cv2.putText(image, "Poing, 1, 2 ou 5 doigts...", (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)

        cv2.putText(image, f"DERNIERE ACTION : {action_validee}", (20, 430),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 3)

        cv2.imshow("Smart Blackjack - Camera", image)
        flux_web.publier(image, action_validee)

        if cv2.waitKey(1) & 0xFF == ord('q') or flux_web.arret.is_set():
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    # Seul, sans AliveCode : les actions vont seulement à l'Arduino.
    # Pour les envoyer aussi à AliveCode, lancer blackjack.py à la place.
    from blackjack_utils import faire_action
    lancer_detection(faire_action)
