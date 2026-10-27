# Smart_Blackjack

## Présentation

Smart Blackjack est un projet d'objets connectés réalisé autour d'une table de
blackjack intelligente. Le dépôt regroupe :

- le **programme Arduino** (boutons, LEDs, écran LCD, buzzer et moteur
  pas-à-pas de distribution des cartes) ;
- les **scripts Raspberry Pi** (caméra, serveur vidéo, contrôle du moteur) ;
- un **script d'interprétation** qui lit les messages série envoyés par
  l'Arduino.

Le système de caméra permet de :

- afficher le flux vidéo en direct (fenêtre locale ou page web) ;
- détecter les mouvements dans l'image ;
- afficher le nombre d'images par seconde (FPS) ;
- enregistrer des captures pour documenter les tests.

## Organisation du dépôt

```text
Smart_Blackjack/
├── arduino_smart_BJ/
│   └── arduino_smart_BJ.ino    # programme de l'Arduino
├── rasberry/
│   ├── README.md               # guide détaillé du Raspberry Pi
│   ├── requirements.txt        # dépendances Python (pyserial)
│   ├── camera.py               # caméra + détection de mouvement (fenêtre OpenCV)
│   ├── camera_serveur.py       # caméra diffusée sur une page web
│   ├── moteur.py               # bouton GPIO -> commande série vers l'Arduino
│   └── interpretation.py       # lecture des messages série de l'Arduino
└── README.md
```

Le nom du dossier `rasberry` est conservé pour correspondre au nom actuel du
dossier dans le projet.

## Démarrage rapide

Toutes les commandes Python se lancent depuis la **racine du dépôt**.

Pour les éléments dans le rasberry Pi, ouvrir le venv avec
```bash
source ./venv/bin/activate
```

| Élément | Où l'exécuter | Commande |
| --- | --- | --- |
| Arduino | Poste de travail (Arduino IDE ou CLI) | voir [1. Arduino](#1-arduino) |
| Caméra (fenêtre) | Raspberry Pi | `python3 rasberry/camera.py` |
| Caméra (page web) | Raspberry Pi | `python3 rasberry/camera_serveur.py` |
| Moteur / Raspberry Pi | Raspberry Pi | `python3 rasberry/moteur.py` |
| Interprétation | Poste branché à l'Arduino | `python3 rasberry/interpretation.py` |

## 1. Arduino

### Bibliothèques

- `LiquidCrystal` et `Stepper` : incluses avec l'Arduino IDE ;
- `ezBuzzer` : à installer depuis *Outils > Gérer les bibliothèques*.

### Téléverser avec l'Arduino IDE

1. Ouvrir `arduino_smart_BJ/arduino_smart_BJ.ino`.
2. Choisir la carte et le port (*Outils > Type de carte* et *Port*).
3. Cliquer sur **Téléverser**.
4. Ouvrir le moniteur série à `9600` bauds pour voir les messages.

### Téléverser avec `arduino-cli` (optionnel)

Les commandes supposent une carte Arduino Uno ; adaptez `--fqbn` et le port
si votre carte est différente.

```bash
arduino-cli core install arduino:avr
arduino-cli lib install ezBuzzer
arduino-cli compile --fqbn arduino:avr:uno arduino_smart_BJ
arduino-cli upload -p /dev/ttyACM0 --fqbn arduino:avr:uno arduino_smart_BJ
```

Sous Windows, remplacez le port par `COM6` (par exemple).

### Branchements utilisés par le programme

| Composant | Broche(s) |
| --- | --- |
| Écran LCD 16x2 | 2, 3, 4, 5, 6, 7 |
| LED verte / bleue / rouge | 8, 9, 10 |
| Buzzer | 11 |
| Bouton Hit / Stand | 12 |
| Bouton Double / Split | 13 |
| Moteur 28BYJ-48 (IN1 à IN4) | A0, A1, A2, A3 |

### Utilisation des boutons

| Bouton | Appui court | Appui long (> 500 ms) |
| --- | --- | --- |
| 12 | Hit (distribue une carte) | Stand |
| 13 | Double | Split |

L'action est affichée sur l'écran LCD, signalée par les LEDs et le buzzer, et
écrite sur le port série à `9600` bauds.

## 2. Raspberry Pi

### Installation

```bash
sudo apt update
sudo apt install -y python3-opencv python3-picamera2 python3-flask python3-rpi.gpio
python3 -m pip install -r rasberry/requirements.txt
```

> Installez `pyserial`, et non le paquet `serial`.

Pour vérifier qu'une caméra officielle est reconnue :

```bash
rpicam-hello
```

Fermez l'aperçu avant de lancer un script Python.

### Trouver le port série de l'Arduino

```bash
ls /dev/ttyACM* /dev/ttyUSB*
```

Si l'accès au port est refusé, ajoutez votre utilisateur au groupe `dialout`
puis rouvrez la session :

```bash
sudo usermod -a -G dialout $USER
```

### Contrôle du moteur (`moteur.py`)

Le Raspberry Pi lit un bouton (GPIO 17) et envoie des commandes à l'Arduino
par le port série.

```bash
python3 rasberry/moteur.py
```

Adaptez `BUTTON_PIN` et `SERIAL_PORT` (`/dev/ttyUSB0` ou `/dev/ttyACM0`) au
début de `rasberry/moteur.py` selon votre branchement.

## 3. Caméra

### Fenêtre locale (écran branché au Raspberry Pi)

```bash
python3 rasberry/camera.py
```

| Touche | Action |
| --- | --- |
| `q` | Quitter |
| `d` | Activer ou désactiver la détection de mouvement |
| `s` | Enregistrer une capture dans `captures/` |

Le script essaie dans l'ordre : `Picamera2`, l'ancienne `picamera`, puis la
webcam USB (index `0`).

### Flux web (depuis un autre poste)

```bash
python3 rasberry/camera_serveur.py
```

Ouvrez ensuite `http://<adresse-ip-du-pi>:5000` dans un navigateur (ou le
Simple Browser de VS Code). Les touches `d`, `s` et `q` fonctionnent dans la
page. Pour connaître l'adresse du Raspberry Pi :

```bash
hostname -I
```

Les captures sont enregistrées dans le dossier `captures/` du répertoire
depuis lequel le script est lancé.

### Réglages principaux

Au début de `rasberry/camera.py` : `LARGEUR`, `HAUTEUR`, `INDEX_CAMERA_USB`,
`SEUIL_MOUVEMENT` (plus bas = plus sensible) et `AIRE_MIN_MOUVEMENT` (plus
élevé = moins de détections parasites).

## 4. Interprétation (lecture série)

`interpretation.py` affiche les messages envoyés par l'Arduino (action, durée
d'appui, état du moteur).

```bash
python3 -m pip install -r rasberry/requirements.txt
python3 rasberry/interpretation.py
```

Le port est défini dans le script (`COM6` par défaut, donc Windows). Sur
Linux ou sur le Raspberry Pi, remplacez-le par `/dev/ttyACM0` ou
`/dev/ttyUSB0`. Pour lister les ports disponibles :

```bash
python3 -m serial.tools.list_ports
```

Quittez avec `Ctrl+C`. Un seul programme à la fois peut ouvrir le port série :
fermez le moniteur série de l'Arduino IDE avant de lancer le script.

## Ordre de démarrage conseillé

1. Brancher l'Arduino et téléverser `arduino_smart_BJ.ino`.
2. Sur le poste connecté à l'Arduino : `python3 rasberry/interpretation.py`.
3. Sur le Raspberry Pi : `python3 rasberry/camera_serveur.py` (ou `camera.py`).
4. Si le Raspberry Pi pilote le moteur : `python3 rasberry/moteur.py`.

## Contributions

Les modifications doivent être testées sur le matériel disponible et la
documentation correspondante doit être mise à jour lorsque le comportement
du projet change.