#!/usr/bin/env python3
"""
test_cartes.py - Tester la reconnaissance des cartes avec la caméra du Raspberry Pi.

Affiche le flux avec une boîte autour de chaque carte reconnue (nom + confiance),
la ligne qui sépare le joueur (en haut) du croupier (en bas), le score de chaque
main et le nombre d'images par seconde. Les mains et les scores sont écrits dans
le terminal à chaque changement.

Touches :
  q  -> quitter
  s  -> sauvegarder une capture d'écran (dans le dossier captures/)

Prérequis : le dossier rasberry/modele/cartes_ncnn_model/ (voir rasberry/README.md).
"""

import os
import time
from datetime import datetime

import cv2

from camera import ouvrir_camera
from detection_cartes import DetecteurCartes
from scores import position_ligne, separer_mains, valeur_main


def dessiner(frame, detections, zone):
    """Dessine la zone de jeu, puis une boîte et le nom de chaque carte détectée."""
    if zone is not None:
        cv2.rectangle(frame, zone[:2], zone[2:], (255, 0, 0), 1)
    for d in detections:
        x1, y1, x2, y2 = d.boite
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, f"{d.nom} {d.confiance:.2f}", (x1, max(y1 - 6, 15)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)


def afficher_score(frame, texte, y):
    cv2.putText(frame, texte, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 4)
    cv2.putText(frame, texte, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)


def main():
    detecteur = DetecteurCartes()
    camera = ouvrir_camera()

    mains_precedentes = None
    temps_precedent = time.time()
    fps = 0.0

    try:
        while True:
            frame = camera.lire()
            if frame is None:
                print("Image non reçue, arrêt.")
                break

            # --- Analyse : cartes ---
            detections = detecteur.detecter(frame)
            dessiner(frame, detections, detecteur.zone)

            # --- Mains et scores : joueur en haut, croupier en bas ---
            hauteur, largeur = frame.shape[:2]
            ligne_y = position_ligne(detecteur.zone, hauteur)
            x1, x2 = (detecteur.zone[0], detecteur.zone[2]) if detecteur.zone else (0, largeur)
            cv2.line(frame, (x1, ligne_y), (x2, ligne_y), (255, 0, 0), 2)

            joueur, croupier = separer_mains(detections, ligne_y)
            score_joueur, score_croupier = valeur_main(joueur), valeur_main(croupier)
            afficher_score(frame, f"Joueur : {score_joueur}", ligne_y - 12)
            afficher_score(frame, f"Croupier : {score_croupier}", ligne_y + 28)

            # Comparaison sans l'ordre : deux cartes de confiance proche s'échangent souvent de place
            mains = (set(joueur), set(croupier))
            if mains != mains_precedentes:
                print(f"Joueur : {', '.join(joueur) or '-'} = {score_joueur}   |   "
                      f"Croupier : {', '.join(croupier) or '-'} = {score_croupier}")
                mains_precedentes = mains

            # --- FPS ---
            maintenant = time.time()
            fps = 0.9 * fps + 0.1 * (1.0 / max(maintenant - temps_precedent, 1e-6))
            temps_precedent = maintenant
            cv2.putText(frame, f"{fps:.1f} FPS", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            cv2.imshow("Cartes - Smart Blackjack", frame)

            touche = cv2.waitKey(1) & 0xFF
            if touche == ord("q"):
                break
            elif touche == ord("s"):
                dossier_captures = "captures"
                os.makedirs(dossier_captures, exist_ok=True)
                nom = os.path.join(
                    dossier_captures,
                    datetime.now().strftime("cartes_%Y%m%d_%H%M%S.jpg"),
                )
                if not cv2.imwrite(nom, frame):
                    raise RuntimeError(f"Impossible d'enregistrer la capture : {nom}")
                print(f"Capture sauvegardée : {nom}")

    finally:
        camera.fermer()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
