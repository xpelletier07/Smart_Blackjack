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
- `INVERSER_ROUGE_BLEU` : à `True` si les objets rouges apparaissent bleus
  (cas de la webcam USB du projet lue par Picamera2). À mettre à `False` avec
  la caméra officielle si ce sont les objets bleus qui apparaissent rouges.

Un seuil de mouvement plus bas rend la détection plus sensible. Une aire
minimale plus élevée réduit les petites détections parasites.

## Reconnaissance des cartes

Le script [`test_cartes.py`](./test_cartes.py) reconnaît les cartes posées sur
la table. Le code de détection, réutilisable, se trouve dans
[`detection_cartes.py`](./detection_cartes.py).

### 1. Le modèle (déjà fourni)

Le modèle est un **YOLO11s pré-entraîné** sur les 52 cartes
([sroot/yolo11s-playing-cards-detector](https://huggingface.co/sroot/yolo11s-playing-cards-detector),
licence AGPL-3.0), converti au format **NCNN**, le plus rapide sur le CPU du Pi.
Il est déjà dans le dépôt :

```text
rasberry/modele/cartes_ncnn_model/
```

Les noms des cartes sont la valeur suivie de la couleur : `AH` (as de cœur),
`10C` (dix de trèfle), `KS` (roi de pique)… avec `C` trèfle, `D` carreau,
`H` cœur, `S` pique.

Sur le Pi, le modèle est lancé directement avec la bibliothèque `ncnn`
(environ 10 Mo) : pas besoin d'installer `ultralytics` ni `torch`, trop lourds.

Pour **changer de modèle** (autre `.pt` trouvé en ligne ou entraîné), la
conversion se fait sur un PC, sans carte graphique (environ 1 min) :

```bash
pip install ultralytics
yolo export model=best.pt format=ncnn imgsz=640
```

Renommer ensuite le dossier `best_ncnn_model/` produit en `cartes_ncnn_model/`
et remplacer celui de `rasberry/modele/`.

### 2. Installer sur le Raspberry Pi

Le modèle exige un **Raspberry Pi OS 64 bits**. Vérifier avec :

```bash
uname -m   # doit afficher aarch64
```

Si vous utilisez un venv, créez-le avec `--system-site-packages` pour garder
accès à `picamera2` installé par `apt` :

```bash
sudo apt install -y python3-opencv python3-picamera2
python3 -m venv --system-site-packages venv
source ./venv/bin/activate
python3 -m pip install -r rasberry/requirements.txt
```

Vérifier que `ncnn` est bien installé :

```bash
python3 -c "import ncnn; print('ncnn', ncnn.__version__)"
```

Vérifier que la caméra Pi fonctionne toujours (numpy doit être en version 1.x) :

```bash
python3 -c "import picamera2, numpy; print('OK, numpy', numpy.__version__)"
```

Vérifier que MediaPipe (reconnaissance des doigts) est bien installé :

```bash
python3 -c "import mediapipe as mp; mp.solutions.hands.Hands(); print('mediapipe', mp.__version__)"
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

La zone de jeu est coupée par une ligne bleue : les cartes **au-dessus**
sont au **joueur**, celles **en dessous** au **croupier**. Le score de chaque
main (as à 11 ou 1, figures à 10) est affiché de part et d'autre de la ligne et
écrit dans le terminal à chaque changement. On joue avec un seul paquet : une
carte dont les deux coins sont visibles n'est comptée qu'une fois, du côté du
milieu de ses deux coins. Pour que les scores ne clignotent pas, une carte
n'est retenue que si elle est vue dans au moins 3 des 5 dernières images. Le
calcul est dans [`scores.py`](./scores.py).

| Touche | Action |
| --- | --- |
| `q` | Quitter le programme |
| `s` | Enregistrer une capture |

### 4. Tout lancer : cartes, doigts et AliveCode

[`blackjack/blackjack.py`](../blackjack/blackjack.py) lance, dès que l'objet est
connecté et sans fenêtre, deux reconnaissances sur la même caméra
(`CameraPartagee` dans [`camera.py`](./camera.py)) :

- **les cartes** ([`suivi_cartes.py`](./suivi_cartes.py)) : quand elles
  changent, les scores sont envoyés dans le doc de l'objet : `/doc/score`
  (joueur) et `/doc/dealer_score` (croupier) ;
- **les doigts levés** ([`media_pipe/detection_action.py`](../media_pipe/detection_action.py)) :
  0 = Stand, 1 = Hit, 2 = Double, 3 = Split. Un geste maintenu 1,5 s est envoyé
  à l'Arduino (`faire_action`).

```bash
python3 blackjack/blackjack.py
```

Une seule application peut utiliser la caméra à la fois : fermer
`test_cartes.py` avant de lancer `blackjack.py`.

### Réglages

Au début de [`detection_cartes.py`](./detection_cartes.py) :

- `SEUIL_CONFIANCE` : en dessous, une détection est ignorée (`0.5` par défaut) ;
- `TAILLE_IMAGE` : doit être la même que celle de l'export (`640` par défaut).
- `LIGNE_PARTAGE` (dans `scores.py`) : position de la ligne joueur / croupier
  dans la zone de jeu (`0.5` = au milieu, plus grand = croupier plus petit) ;
- `NB_IMAGES_STABLES` et `MINIMUM_VOTES` (dans `scores.py`) : la stabilisation
  (`5` et `3` par défaut). Plus haut = plus stable mais plus lent à réagir ;
  à environ 2 images par seconde, une carte posée apparaît après 1 à 2 s ;
- `ZONE_JEU` : rectangle `(x1, y1, x2, y2)` de l'image où sont posées les
  cartes ; seule cette partie est analysée (`None` = toute l'image). Elle est
  dessinée en bleu dans la fenêtre. **C'est le réglage qui compte le plus** :
  plus la zone est serrée autour des cartes, plus elles paraissent grandes au
  modèle. Pour la régler, faire une capture avec `s` et lire les coordonnées
  des coins dans un logiciel de dessin (ex. Paint). À refaire si la caméra bouge.

Rapprocher la caméra de la table aide aussi beaucoup : un coin de carte doit
faire au moins une vingtaine de pixels de haut dans l'image.

Si le nombre d'images par seconde est trop bas, réexportez le modèle en 416 px
(sur un PC avec `ultralytics`, à partir du `.pt` d'origine) :

```python
from ultralytics import YOLO
YOLO("best.pt").export(format="ncnn", imgsz=416)
```

Remplacez alors `rasberry/modele/cartes_ncnn_model/` par le nouveau dossier
(renommé) et mettez `TAILLE_IMAGE = 416`.
