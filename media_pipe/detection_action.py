import sys
import os
import threading
import time
import cv2

# Mapping exact attendu par faireAction() dans l'Arduino
ACTIONS_BLACKJACK = {
    0: "Stand",
    1: "Hit",
    2: "Double",
    3: "Split"
}

TEMPS_CONFIRMATION = 1.5


def compter_doigts(points, main_label):
    """Nombre de doigts levés à partir des 21 points d'une main MediaPipe."""
    doigts_leves = 0

    # Pouce : bout (4) plus à l'extérieur que l'articulation (3)
    if main_label == "Right":
        if points[4].x < points[3].x:
            doigts_leves += 1
    else:
        if points[4].x > points[3].x:
            doigts_leves += 1

    # 4 autres doigts (Index, Majeur, Annulaire, Auriculaire)
    for bout in [8, 12, 16, 20]:
        if points[bout].y < points[bout - 2].y:
            doigts_leves += 1

    return doigts_leves


class Confirmation:
    """Un geste n'est validé que s'il est maintenu `temps` secondes, et n'est
    envoyé qu'une fois tant que la main ne change pas."""

    def __init__(self, temps=TEMPS_CONFIRMATION):
        self.temps = temps
        self.dernier_geste = None
        self.debut_geste = 0
        self.action_deja_envoyee = False
        self.progression = 0  # en %, pour l'affichage

    def ajouter(self, action_detectee, maintenant):
        """Retourne l'action à envoyer, ou None."""
        if not action_detectee:
            self.dernier_geste = None
            self.action_deja_envoyee = False
            return None

        if action_detectee != self.dernier_geste:
            self.dernier_geste = action_detectee
            self.debut_geste = maintenant
            self.action_deja_envoyee = False
            self.progression = 0
            return None

        temps_ecoule = maintenant - self.debut_geste
        self.progression = min(int((temps_ecoule / self.temps) * 100), 100)
        if temps_ecoule >= self.temps and not self.action_deja_envoyee:
            self.action_deja_envoyee = True
            return action_detectee
        return None


class DetecteurGestes:
    """Reconnaît les actions (0 à 3 doigts levés) dans les images de la caméra."""

    def __init__(self, temps_confirmation=TEMPS_CONFIRMATION):
        import mediapipe as mp  # import ici : les tests n'en ont pas besoin

        self.mp_hands = mp.solutions.hands
        self.mp_drawing = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.75)
        self.confirmation = Confirmation(temps_confirmation)
        self.action_detectee = None

    def analyser(self, image, dessiner=False):
        """Analyse une image (BGR, déjà retournée en miroir). Retourne l'action
        validée à envoyer, ou None. Avec dessiner=True, la main est dessinée sur l'image."""
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        resultats = self.hands.process(image_rgb)

        self.action_detectee = None

        if resultats.multi_hand_landmarks and resultats.multi_handedness:
            for hand_landmarks, handedness in zip(resultats.multi_hand_landmarks, resultats.multi_handedness):
                if dessiner:
                    self.mp_drawing.draw_landmarks(image, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
                main_label = handedness.classification[0].label
                doigts_leves = compter_doigts(hand_landmarks.landmark, main_label)
                self.action_detectee = ACTIONS_BLACKJACK.get(doigts_leves, None)

        return self.confirmation.ajouter(self.action_detectee, time.time())

    def demarrer(self, camera, envoyer):
        """Lit la caméra en continu dans un thread et appelle envoyer(action) à
        chaque action validée (thread qui s'arrête avec le programme)."""
        def boucle():
            while True:
                frame = camera.lire()
                if frame is None:
                    print("Image non reçue, arrêt de la reconnaissance des gestes.")
                    break
                action = self.analyser(cv2.flip(frame, 1))
                if action:
                    envoyer(action)

        threading.Thread(target=boucle, daemon=True).start()


def main():
    # Ajoute le dossier parent (Smart_Blackjack) au chemin de recherche Python
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

    # Importe depuis le dossier "blackjack"
    from blackjack.blackjack_utils import faire_action

    gestes = DetecteurGestes()
    action_validee = "Aucune"

    cap = cv2.VideoCapture(0)

    while cap.isOpened():
        succes, image = cap.read()
        if not succes:
            break

        image = cv2.flip(image, 1)
        action = gestes.analyser(image, dessiner=True)

        # Validation et appel de faire_action()
        if action:
            action_validee = action
            faire_action(action_validee)

        if gestes.action_detectee:
            cv2.putText(image, f"Maintenir : {gestes.action_detectee} ({gestes.confirmation.progression}%)", (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        else:
            cv2.putText(image, "Montrez 0, 1, 2 ou 3 doigts...", (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)

        cv2.putText(image, f"DERNIERE ACTION : {action_validee}", (20, 430),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 3)

        cv2.imshow("Smart Blackjack - Camera", image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
