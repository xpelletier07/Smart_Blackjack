#!/usr/bin/env python3
"""
suivi_cartes.py - Suivre les cartes en continu avec la caméra, sans fenêtre.

Utilisé par blackjack/blackjack.py : la caméra est lue dans un thread, et les
derniers scores stables (joueur, croupier) sont toujours disponibles dans
`suivi.scores`. Les mains sont écrites dans le terminal à chaque changement.

Pour voir ce que la caméra détecte (boîtes, ligne, scores) : test_cartes.py.
"""

import threading

from scores import Stabilisateur, position_ligne, separer_mains, valeur_main


class SuiviCartes:
    """Détecte les cartes image par image et garde les mains stables."""

    def __init__(self, detecteur=None, camera=None, stabilisateur=None):
        if detecteur is None:
            from detection_cartes import DetecteurCartes
            detecteur = DetecteurCartes()
        self.detecteur = detecteur
        self.camera = camera    # None : ouverte au démarrage du thread
        self.stabilisateur = stabilisateur or Stabilisateur()
        self.mains = ([], [])   # (joueur, croupier), triées par nom
        self.scores = (0, 0)    # (joueur, croupier)

    def analyser(self, frame):
        """Analyse une image. Retourne True si les mains stables ont changé."""
        detections = self.detecteur.detecter(frame)
        ligne_y = position_ligne(self.detecteur.zone, frame.shape[0])
        mains = self.stabilisateur.ajouter(*separer_mains(detections, ligne_y))
        if mains == self.mains:
            return False
        joueur, croupier = mains
        self.mains = mains
        self.scores = (valeur_main(joueur), valeur_main(croupier))
        print(f"Joueur : {', '.join(joueur) or '-'} = {self.scores[0]}   |   "
              f"Croupier : {', '.join(croupier) or '-'} = {self.scores[1]}")
        return True

    def demarrer(self):
        """Lit la caméra en continu dans un thread (qui s'arrête avec le programme)."""
        threading.Thread(target=self._boucle, daemon=True).start()

    def _boucle(self):
        if self.camera is None:
            from camera import ouvrir_camera
            self.camera = ouvrir_camera()
        try:
            while True:
                frame = self.camera.lire()
                if frame is None:
                    print("Image non reçue, arrêt du suivi des cartes.")
                    break
                self.analyser(frame)
        finally:
            self.camera.fermer()
