# Smart Blackjack sur Raspberry Pi

Ce dossier contient les éléments nécessaires pour tester la caméra du projet
Smart Blackjack avec un Raspberry Pi.

## Matériel

- un Raspberry Pi ;
- une caméra officielle Raspberry Pi ou une webcam USB ;
- une alimentation adaptée ;
- un écran et un clavier pour contrôler la fenêtre OpenCV, ou une session
  permettant d'afficher cette fenêtre.

## Vérifier la caméra

Pour vérifier qu'une caméra officielle est reconnue :

```bash
rpicam-hello
```

Le test doit afficher l'aperçu de la caméra. Fermez ensuite l'aperçu avant de
lancer le script Python.

## Installer les dépendances

Sur le Raspberry Pi :

```bash
sudo apt update
sudo apt install -y python3-opencv python3-picamera2
python3 -m pip install -r rasberry/requirements.txt
```

Le script peut aussi utiliser l'ancienne bibliothèque `picamera` lorsqu'elle
est déjà installée, notamment pour le matériel utilisé au laboratoire.

> Installez `pyserial`, et non le paquet `serial`. Le module `serial` fourni
> par `pyserial` expose la classe `serial.Serial` utilisée par
> [`interpretation.py`](./interpretation.py) et [`moteur.py`](./moteur.py).

## Lancer le test de caméra

Depuis la racine du dépôt :

```bash
python3 rasberry/camera.py
```

Ou, depuis ce dossier :

```bash
python3 camera.py
```

La résolution demandée par défaut est de `640 x 480`. Le script essaie les
caméras dans l'ordre suivant :

1. caméra officielle avec `Picamera2` ;
2. caméra officielle avec l'ancienne bibliothèque `picamera` ;
3. webcam USB à l'index `0`.

Les erreurs de détection sont affichées dans le terminal avant de passer à la
solution suivante.

## Fonctionnalités et commandes

La fenêtre `Camera - Robot` affiche le flux, le FPS et les annotations de
détection.

| Touche | Action |
| --- | --- |
| `q` | Quitter le programme |
| `d` | Activer ou désactiver la détection de mouvement |
| `f` | Activer ou désactiver la détection de visages |
| `s` | Enregistrer une capture |

La détection de mouvement est activée au démarrage. La détection de visages
cherche automatiquement le fichier
`haarcascade_frontalface_default.xml` dans les emplacements connus d'OpenCV.
Si le fichier est introuvable, la touche `f` reste désactivée.

## Captures

La touche `s` crée automatiquement le dossier `captures/` dans le répertoire
depuis lequel le script a été lancé, puis enregistre une image JPEG avec un
nom comme :

```text
captures/capture_20261024_143000.jpg
```

Pour que la capture soit enregistrée dans le projet, lancez le script depuis
la racine du dépôt. Vérifiez également que l'utilisateur possède les droits
d'écriture dans ce dossier.

## Réglages principaux

Les réglages se trouvent au début de
[`camera.py`](./camera.py) :

- `LARGEUR` et `HAUTEUR` : résolution de la caméra ;
- `INDEX_CAMERA_USB` : index de la webcam USB ;
- `SEUIL_MOUVEMENT` : sensibilité de la détection de mouvement ;
- `AIRE_MIN_MOUVEMENT` : taille minimale d'une zone considérée comme un
  mouvement.

Un seuil de mouvement plus bas rend la détection plus sensible. Une aire
minimale plus élevée réduit les petites détections parasites.

## Reconnaissance des cartes

Le script [`test_cartes.py`](./test_cartes.py) reconnaît les cartes posées sur
la table grâce à un modèle YOLOv8 entraîné sur le dataset Roboflow. Le code de
détection, réutilisable, se trouve dans [`detection_cartes.py`](./detection_cartes.py).

### 1. Entraîner le modèle (une seule fois, sur Google Colab)

1. Sur Roboflow, exporter le dataset au format **YOLOv8** (zip).
2. Ouvrir [`ia/entrainement_cartes.ipynb`](../ia/entrainement_cartes.ipynb)
   dans Google Colab, choisir un environnement **GPU**, puis exécuter les
   cellules dans l'ordre.
3. Le notebook télécharge `modele_cartes.zip`, qui contient :
   - `cartes_ncnn_model/` : le modèle pour le Raspberry Pi ;
   - `best.pt` : le modèle d'origine, à garder pour un éventuel réexport.

### 2. Installer sur le Raspberry Pi

Le modèle exige un **Raspberry Pi OS 64 bits**. Vérifier avec :

```bash
uname -m   # doit afficher aarch64
```

Si vous utilisez un venv, créez-le avec `--system-site-packages` pour garder
accès à `picamera2` installé par `apt` :

```bash
python3 -m venv --system-site-packages venv
source ./venv/bin/activate
python3 -m pip install -r rasberry/requirements.txt
```

Vérifier que la caméra Pi fonctionne toujours (numpy doit être en version 1.x) :

```bash
python3 -c "import picamera2, numpy; print('OK, numpy', numpy.__version__)"
```

Copier ensuite le dossier `cartes_ncnn_model/` dans `rasberry/modele/` :

```text
rasberry/modele/cartes_ncnn_model/
```

### 3. Lancer le test

Depuis la racine du dépôt :

```bash
python3 rasberry/test_cartes.py
```

La fenêtre `Cartes - Smart Blackjack` encadre chaque carte reconnue avec son
nom et sa confiance. Le terminal affiche la liste des cartes vues à chaque
changement. Une carte dont les deux coins sont visibles n'est comptée qu'une
fois.

| Touche | Action |
| --- | --- |
| `q` | Quitter le programme |
| `s` | Enregistrer une capture |

### Réglages

Au début de [`detection_cartes.py`](./detection_cartes.py) :

- `SEUIL_CONFIANCE` : en dessous, une détection est ignorée (`0.5` par défaut) ;
- `TAILLE_IMAGE` : doit être la même que celle de l'export (`640` par défaut).

Si le nombre d'images par seconde est trop bas, réexportez le modèle en 416 px
sans réentraîner (sur Colab ou un PC avec `ultralytics`) :

```python
from ultralytics import YOLO
YOLO("best.pt").export(format="ncnn", imgsz=416)
```

Remplacez alors `rasberry/modele/cartes_ncnn_model/` par le nouveau dossier
(renommé) et mettez `TAILLE_IMAGE = 416`.
