#!/usr/bin/env python3
"""
camera.py - Afficher le flux d'une caméra sur Raspberry Pi 4 + analyse simple.

Fonctionne avec :
  - une webcam USB (via OpenCV)
  - la caméra officielle Raspberry Pi (via Picamera2), si installée

Touches :
  q  -> quitter
  d  -> activer/désactiver la détection de mouvement
  f  -> activer/désactiver la détection de visages
  s  -> sauvegarder une capture d'écran (dans le dossier captures/)

Installation sur le Raspberry Pi :
  sudo apt update
  sudo apt install -y python3-opencv python3-picamera2
"""

import os
import time
from datetime import datetime

import cv2

# ----------------------------- Réglages ------------------------------------
LARGEUR = 640
HAUTEUR = 480
INDEX_CAMERA_USB = 0          # 0 = première webcam USB
SEUIL_MOUVEMENT = 25          # sensibilité (plus bas = plus sensible)
AIRE_MIN_MOUVEMENT = 1500     # taille minimale (en pixels) d'une zone en mouvement
# ---------------------------------------------------------------------------


class CameraUSB:
    """Caméra USB via OpenCV."""

    def __init__(self, index=0, largeur=LARGEUR, hauteur=HAUTEUR):
        self.cap = cv2.VideoCapture(index)
        if not self.cap.isOpened():
            raise RuntimeError("Impossible d'ouvrir la webcam USB.")
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, largeur)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, hauteur)

    def lire(self):
        ok, frame = self.cap.read()
        return frame if ok else None

    def fermer(self):
        self.cap.release()


class CameraPi:
    """Caméra officielle du Raspberry Pi via Picamera2."""

    def __init__(self, largeur=LARGEUR, hauteur=HAUTEUR):
        from picamera2 import Picamera2  # import ici : absent si pas de caméra Pi

        self.cam = Picamera2()
        config = self.cam.create_preview_configuration(
            main={"size": (largeur, hauteur), "format": "RGB888"}
        )
        self.cam.configure(config)
        self.cam.start()

    def lire(self):
        # Picamera2 "RGB888" donne déjà un ordre compatible avec OpenCV (BGR)
        return self.cam.capture_array()

    def fermer(self):
        self.cam.stop()


class CameraPiLegacy:
    """Caméra Pi avec l'ancienne bibliothèque picamera (celle du laboratoire)."""

    def __init__(self, largeur=LARGEUR, hauteur=HAUTEUR):
        from picamera import PiCamera
        from picamera.array import PiRGBArray

        self.camera = PiCamera()
        self.camera.resolution = (largeur, hauteur)
        self.camera.framerate = 30
        self.raw = PiRGBArray(self.camera, size=(largeur, hauteur))
        time.sleep(0.5)  # temps de réchauffement de la caméra
        # capture_continuous = la boucle de capture du labo, en continu
        self.flux = self.camera.capture_continuous(
            self.raw, format="bgr", use_video_port=True
        )

    def lire(self):
        sortie = next(self.flux)
        frame = sortie.array.copy()
        sortie.truncate(0)  # vide le stream pour la prochaine image (comme dans le labo)
        return frame

    def fermer(self):
        self.camera.close()


def ouvrir_camera():
    """Essaie Picamera2, puis l'ancienne picamera (labo), puis la webcam USB."""
    try:
        cam = CameraPi()
        print("Caméra Raspberry Pi (Picamera2) détectée.")
        return cam
    except Exception as e:
        print(f"Picamera2 non disponible ({e}).")
    try:
        cam = CameraPiLegacy()
        print("Caméra Raspberry Pi (picamera, version labo) détectée.")
        return cam
    except Exception as e:
        print(f"picamera non disponible ({e}). Essai de la webcam USB...")
    cam = CameraUSB(INDEX_CAMERA_USB)
    print("Webcam USB détectée.")
    return cam


def detecter_mouvement(frame, frame_precedente_gris):
    """Compare l'image actuelle à la précédente et retourne les zones qui bougent."""
    gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gris = cv2.GaussianBlur(gris, (21, 21), 0)

    if frame_precedente_gris is None:
        return gris, []

    diff = cv2.absdiff(frame_precedente_gris, gris)
    _, masque = cv2.threshold(diff, SEUIL_MOUVEMENT, 255, cv2.THRESH_BINARY)
    masque = cv2.dilate(masque, None, iterations=2)

    contours, _ = cv2.findContours(masque, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    zones = [cv2.boundingRect(c) for c in contours if cv2.contourArea(c) > AIRE_MIN_MOUVEMENT]
    return gris, zones


def trouver_cascade(nom="haarcascade_frontalface_default.xml"):
    """Cherche le fichier du détecteur de visages, selon comment OpenCV est installé."""
    dossiers = []
    # OpenCV installé avec pip : cv2.data existe
    if hasattr(cv2, "data"):
        dossiers.append(cv2.data.haarcascades)
    # OpenCV installé avec apt (python3-opencv) : chemins système habituels
    dossiers += [
        "/usr/share/opencv4/haarcascades/",
        "/usr/share/opencv/haarcascades/",
        "/usr/local/share/opencv4/haarcascades/",
    ]
    for dossier in dossiers:
        chemin = os.path.join(dossier, nom)
        if os.path.exists(chemin):
            return chemin
    return None


def main():
    camera = ouvrir_camera()

    # Détecteur de visages fourni avec OpenCV
    chemin_cascade = trouver_cascade()
    if chemin_cascade:
        detecteur_visages = cv2.CascadeClassifier(chemin_cascade)
    else:
        detecteur_visages = None
        print("Fichier du détecteur de visages introuvable : touche 'f' désactivée.")

    mode_mouvement = True
    mode_visages = False
    gris_precedent = None
    temps_precedent = time.time()
    fps = 0.0

    try:
        while True:
            frame = camera.lire()
            if frame is None:
                print("Image non reçue, arrêt.")
                break

            # --- Analyse : mouvement ---
            if mode_mouvement:
                gris_precedent, zones = detecter_mouvement(frame, gris_precedent)
                for (x, y, w, h) in zones:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                if zones:
                    cv2.putText(frame, "MOUVEMENT", (10, 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            # --- Analyse : visages ---
            if mode_visages:
                gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                visages = detecteur_visages.detectMultiScale(
                    gris, scaleFactor=1.2, minNeighbors=5, minSize=(40, 40)
                )
                for (x, y, w, h) in visages:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                cv2.putText(frame, f"Visages: {len(visages)}", (10, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

            # --- FPS ---
            maintenant = time.time()
            fps = 0.9 * fps + 0.1 * (1.0 / max(maintenant - temps_precedent, 1e-6))
            temps_precedent = maintenant
            cv2.putText(frame, f"{fps:.1f} FPS", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            cv2.imshow("Camera - Robot", frame)

            touche = cv2.waitKey(1) & 0xFF
            if touche == ord("q"):
                break
            elif touche == ord("d"):
                mode_mouvement = not mode_mouvement
                gris_precedent = None
            elif touche == ord("f") and detecteur_visages is not None:
                mode_visages = not mode_visages
            elif touche == ord("s"):
                dossier_captures = "captures"
                os.makedirs(dossier_captures, exist_ok=True)
                nom = os.path.join(
                    dossier_captures,
                    datetime.now().strftime("capture_%Y%m%d_%H%M%S.jpg"),
                )
                if not cv2.imwrite(nom, frame):
                    raise RuntimeError(f"Impossible d'enregistrer la capture : {nom}")
                print(f"Capture sauvegardée : {nom}")

    finally:
        camera.fermer()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()