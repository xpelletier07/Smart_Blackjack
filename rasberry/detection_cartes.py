#!/usr/bin/env python3
"""
detection_cartes.py - Reconnaissance des cartes avec un modèle YOLO (format NCNN).

Le modèle (YOLO11s pré-entraîné, converti en NCNN) est dans
rasberry/modele/cartes_ncnn_model/ : voir rasberry/README.md pour le changer.

Le modèle est lancé directement avec la bibliothèque ncnn (pas besoin
d'ultralytics ni de torch sur le Pi, qui sont très lourds à installer).

Installation sur le Raspberry Pi (OS 64 bits) :
  python3 -m pip install -r rasberry/requirements.txt
"""

import os
import re
from dataclasses import dataclass

import cv2
import numpy as np

# ----------------------------- Réglages ------------------------------------
CHEMIN_MODELE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "modele", "cartes_ncnn_model")
SEUIL_CONFIANCE = 0.5     # en dessous, la détection est ignorée
SEUIL_CHEVAUCHEMENT = 0.7 # deux boîtes de la même carte plus chevauchantes = doublon
TAILLE_IMAGE = 640        # doit correspondre à l'imgsz de l'export
NB_THREADS = 4            # le Pi 4 a 4 cœurs
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


def lire_noms(chemin_metadata):
    """Lit les noms des classes ({0: "10C", ...}) dans le metadata.yaml de l'export."""
    noms = {}
    dans_noms = False
    with open(chemin_metadata, encoding="utf-8") as f:
        for ligne in f:
            if ligne.startswith("names:"):
                dans_noms = True
                continue
            if dans_noms:
                trouve = re.match(r"\s+(\d+):\s*['\"]?(.*?)['\"]?\s*$", ligne)
                if not trouve:
                    break  # fin de la section names
                noms[int(trouve.group(1))] = trouve.group(2)
    return noms


def preparer_image(frame, taille):
    """Redimensionne l'image en carré (bandes grises, comme à l'entraînement).
    Retourne (blob RGB 0-1 en 3 x taille x taille, ratio, (pad_x, pad_y))."""
    hauteur, largeur = frame.shape[:2]
    ratio = min(taille / hauteur, taille / largeur)
    nouv_l, nouv_h = round(largeur * ratio), round(hauteur * ratio)
    if (nouv_l, nouv_h) != (largeur, hauteur):
        frame = cv2.resize(frame, (nouv_l, nouv_h), interpolation=cv2.INTER_LINEAR)

    pad_x, pad_y = (taille - nouv_l) / 2, (taille - nouv_h) / 2
    haut, bas = round(pad_y - 0.1), round(pad_y + 0.1)
    gauche, droite = round(pad_x - 0.1), round(pad_x + 0.1)
    frame = cv2.copyMakeBorder(frame, haut, bas, gauche, droite,
                               cv2.BORDER_CONSTANT, value=(114, 114, 114))

    blob = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).transpose(2, 0, 1)
    return np.ascontiguousarray(blob, dtype=np.float32) / 255.0, ratio, (gauche, haut)


def decoder_sortie(sortie, ratio, pad, seuil, largeur, hauteur, noms,
                   seuil_chevauchement=SEUIL_CHEVAUCHEMENT):
    """Transforme la sortie brute du modèle (4 + nb_classes, N) en détections dans
    l'image d'origine : filtre par confiance, retire les doublons (NMS)."""
    scores = sortie[4:]
    classes = scores.argmax(axis=0)
    confiances = scores.max(axis=0)
    garder = confiances >= seuil
    if not garder.any():
        return []

    cx, cy, w, h = sortie[:4, garder]
    classes, confiances = classes[garder], confiances[garder]
    boites = np.stack([cx - w / 2, cy - h / 2, w, h], axis=1)

    # NMS par carte : on décale chaque classe pour que deux cartes différentes
    # qui se chevauchent ne s'éliminent pas
    decalees = boites.copy()
    decalees[:, :2] += classes[:, None] * 4096
    indices = cv2.dnn.NMSBoxes(decalees.tolist(), confiances.tolist(), seuil, seuil_chevauchement)

    detections = []
    for i in np.array(indices).flatten():
        x, y, bw, bh = boites[i]
        x1 = (x - pad[0]) / ratio
        y1 = (y - pad[1]) / ratio
        x2 = (x + bw - pad[0]) / ratio
        y2 = (y + bh - pad[1]) / ratio
        detections.append(Detection(
            nom=noms[int(classes[i])],
            confiance=float(confiances[i]),
            boite=(int(np.clip(x1, 0, largeur)), int(np.clip(y1, 0, hauteur)),
                   int(np.clip(x2, 0, largeur)), int(np.clip(y2, 0, hauteur))),
        ))
    return detections


class DetecteurCartes:
    """Charge le modèle NCNN et détecte les cartes dans une image OpenCV (BGR)."""

    def __init__(self, chemin_modele=CHEMIN_MODELE, seuil=SEUIL_CONFIANCE, taille=TAILLE_IMAGE):
        if not os.path.isdir(chemin_modele):
            raise FileNotFoundError(
                f"Modèle introuvable : {chemin_modele}\n"
                "Convertissez un modèle .pt en NCNN (voir rasberry/README.md) "
                "et copiez le dossier cartes_ncnn_model/ dans rasberry/modele/."
            )
        import ncnn  # import ici : les tests n'en ont pas besoin

        self.ncnn = ncnn
        self.net = ncnn.Net()
        self.net.opt.num_threads = NB_THREADS
        self.net.load_param(os.path.join(chemin_modele, "model.ncnn.param"))
        self.net.load_model(os.path.join(chemin_modele, "model.ncnn.bin"))
        self.noms = lire_noms(os.path.join(chemin_modele, "metadata.yaml"))
        self.seuil = seuil
        self.taille = taille

    def detecter(self, frame):
        hauteur, largeur = frame.shape[:2]
        blob, ratio, pad = preparer_image(frame, self.taille)
        with self.net.create_extractor() as ex:
            ex.input("in0", self.ncnn.Mat(blob))
            _, sortie = ex.extract("out0")
        return decoder_sortie(np.array(sortie), ratio, pad, self.seuil,
                              largeur, hauteur, self.noms)
