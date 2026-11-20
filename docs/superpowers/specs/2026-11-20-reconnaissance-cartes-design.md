# Reconnaissance des cartes — étape 1 : le modèle

## Intention

Reconnaître les cartes posées sur la table à partir de la caméra du Raspberry Pi,
pour, à terme, calculer les scores du joueur et du croupier et les envoyer à
AliveCode avec Aliot (comme `blackjack/blackjack.py`). Tout le système final
tourne sur le Pi, y compris `blackjack.py` (testé jusqu'ici sur un PC).

Cette étape ne fait que **mettre en place le modèle** : l'entraîner et vérifier
qu'il reconnaît les cartes sur la vraie table, avec la caméra du Pi, à une
vitesse acceptable.

## Objectifs

- Un modèle qui détecte et identifie les 52 cartes, le plus précis possible.
- Une mise en place simple : un notebook à exécuter, un dossier à copier sur le Pi.
- Un script de test sur le Pi qui montre les détections en direct.

## Hors périmètre (étapes suivantes)

- Partage joueur / croupier par zone de l'image (décidé : par zone).
- Calcul des scores et envoi à AliveCode (scores seulement, pas la liste des cartes).
- Split, plusieurs joueurs.

## Contraintes

- Cible : Raspberry Pi 4, CPU seulement, **Raspberry Pi OS 64 bits** (`uname -m` → `aarch64`).
- Caméra ouverte via `ouvrir_camera()` de `rasberry/camera.py`.
- Dataset Roboflow re-téléchargé au format **YOLOv8** (décision : pas de convertisseur COCO).

## Approches considérées

| Approche | Pour | Contre |
|---|---|---|
| **YOLOv8n (ultralytics) → NCNN** — choisie | La plus précise sur les coins de cartes, installation simple, très documentée | Conversion COCO → YOLO à faire |
| MediaPipe Model Maker | Lit le COCO directement, modèle léger | Pas sous Windows, entrée 256 px : coins minuscules, moins précis |
| OpenCV seul (contours + gabarits) | Aucun entraînement | Fragile (lumière, chevauchements), n'utilise pas le dataset |

Choix de l'utilisateur : la plus facile à installer **et** la plus précise → YOLOv8n.

## Design

1. **`ia/entrainement_cartes.ipynb`** (Google Colab, GPU) : téléversement du zip
   YOLOv8 de Roboflow, correction des chemins du `data.yaml`, entraînement YOLOv8n en
   640 px, validation, export NCNN, téléchargement du dossier du modèle.
2. **`rasberry/modele/`** : le dossier NCNN exporté (~12 Mo), copié sur le Pi.
3. **`rasberry/test_cartes.py`** : boucle caméra → détection → boîtes + nom de
   carte + confiance + FPS dans la fenêtre OpenCV, liste des cartes vues dans le
   terminal.
4. **`rasberry/requirements.txt`** + **`rasberry/README.md`** : ajout de
   `ultralytics` et des étapes d'installation et de test.

Si les FPS sont trop bas, réexporter en 416 px sans réentraîner.

## Laissé au constructeur

Hyperparamètres d'entraînement (époques, augmentations), seuil de confiance par
défaut, gestion de la structure exacte du zip Roboflow.
