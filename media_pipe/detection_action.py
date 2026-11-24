import sys
import os
import time
import cv2
import mediapipe as mp

# Ajoute le dossier parent (Smart_Blackjack) au chemin de recherche Python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importe depuis le dossier "blackjack"
from blackjack.blackjack_utils import faire_action

# Initialisation MediaPipe
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.75)

# Mapping exact attendu par faireAction() dans l'Arduino
ACTIONS_BLACKJACK = {
    0: "Stand",
    1: "Hit",
    2: "Double",
    3: "Split"
}

TEMPS_CONFIRMATION = 1.5
dernier_geste = None
debut_geste = 0
action_deja_envoyee = False
action_validee = "Aucune"

cap = cv2.VideoCapture(0)

while cap.isOpened():
    succes, image = cap.read()
    if not succes:
        break

    image = cv2.flip(image, 1)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    resultats = hands.process(image_rgb)

    action_detectee = None

    if resultats.multi_hand_landmarks and resultats.multi_handedness:
        for hand_landmarks, handedness in zip(resultats.multi_hand_landmarks, resultats.multi_handedness):
            mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            points = hand_landmarks.landmark
            main_label = handedness.classification.label

            doigts_leves = 0

            # Pouce
            if main_label == "Right":
                if points.x < points.x:
                    doigts_leves += 1
            else:
                if points.x > points.x:
                    doigts_leves += 1

            # 4 autres doigts (Index, Majeur, Annulaire, Auriculaire)
            for bout in [8, 12, 16, 20]:
                if points[bout].y < points[bout - 2].y:
                    doigts_leves += 1

            action_detectee = ACTIONS_BLACKJACK.get(doigts_leves, None)

    # Validation et appel de faire_action()
    if action_detectee:
        if action_detectee == dernier_geste:
            temps_ecoule = time.time() - debut_geste
            progression = min(int((temps_ecoule / TEMPS_CONFIRMATION) * 100), 100)

            cv2.putText(image, f"Maintenir : {action_detectee} ({progression}%)", (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

            if temps_ecoule >= TEMPS_CONFIRMATION and not action_deja_envoyee:
                action_validee = action_detectee
                faire_action(action_validee) 
                action_deja_envoyee = True
        else:
            dernier_geste = action_detectee
            debut_geste = time.time()
            action_deja_envoyee = False
    else:
        dernier_geste = None
        action_deja_envoyee = False
        cv2.putText(image, "Montrez 0, 1, 2 ou 3 doigts...", (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)

    cv2.putText(image, f"DERNIERE ACTION : {action_validee}", (20, 430),
                cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 3)

    cv2.imshow("Smart Blackjack - Camera", image)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
