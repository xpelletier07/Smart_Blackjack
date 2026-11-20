#!/usr/bin/env python3
"""
detection_cartes.py - Reconnaissance des cartes avec le modèle YOLOv8 (format NCNN).

Le modèle est entraîné avec le notebook ia/entrainement_cartes.ipynb (Colab),
puis le dossier cartes_ncnn_model/ est copié dans rasberry/modele/.

Installation sur le Raspberry Pi (OS 64 bits) :
  python3 -m pip install -r rasberry/requirements.txt
"""

import os
from dataclasses import dataclass

# ----------------------------- Réglages ------------------------------------
CHEMIN_MODELE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "modele", "cartes_ncnn_model")
SEUIL_CONFIANCE = 0.5     # en dessous, la détection est ignorée
TAILLE_IMAGE = 640        # doit correspondre à l'imgsz de l'export
# ---------------------------------------------------------------------------


@dataclass
class Detection:
    """Une carte détectée dans l'image."""
    nom: str                              # ex. "AH", "10C"
    confiance: float
    boite: tuple[int, int, int, int]      # (x1, y1, x2, y2) en pixels


def cartes_uniques(detections):
    """Liste des cartes vues, une seule fois chacune (une carte a souvent ses deux
    coins détectés), de la plus sûre à la moins sûre."""
    meilleures = {}
    for d in detections:
        if d.nom not in meilleures or d.confiance > meilleures[d.nom]:
            meilleures[d.nom] = d.confiance
    return sorted(meilleures, key=meilleures.get, reverse=True)


class DetecteurCartes:
    """Charge le modèle et détecte les cartes dans une image OpenCV (BGR)."""

    def __init__(self, chemin_modele=CHEMIN_MODELE, seuil=SEUIL_CONFIANCE, taille=TAILLE_IMAGE):
        if not os.path.isdir(chemin_modele):
            raise FileNotFoundError(
                f"Modèle introuvable : {chemin_modele}\n"
                "Entraînez-le avec le notebook ia/entrainement_cartes.ipynb (Colab), "
                "puis copiez le dossier cartes_ncnn_model/ dans rasberry/modele/."
            )
        from ultralytics import YOLO  # import ici : lourd, et absent sur le PC de test

        self.modele = YOLO(str(chemin_modele), task="detect")
        self.seuil = seuil
        self.taille = taille

    def detecter(self, frame):
        resultat = self.modele(frame, imgsz=self.taille, conf=self.seuil, verbose=False)[0]
        detections = []
        for boite, confiance, classe in zip(resultat.boxes.xyxy.tolist(),
                                            resultat.boxes.conf.tolist(),
                                            resultat.boxes.cls.tolist()):
            detections.append(Detection(
                nom=resultat.names[int(classe)],
                confiance=float(confiance),
                boite=tuple(int(v) for v in boite),
            ))
        return detections
