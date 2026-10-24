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
```

Le script peut aussi utiliser l'ancienne bibliothèque `picamera` lorsqu'elle
est déjà installée, notamment pour le matériel utilisé au laboratoire.

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
