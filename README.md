# Smart_Blackjack

## Présentation

Smart Blackjack est un projet d'objets connectés réalisé autour d'une table de
blackjack intelligente. Le dépôt contient notamment les essais de capture et
d'analyse vidéo exécutés sur un Raspberry Pi.

Le système de caméra permet de :

- afficher le flux vidéo en direct ;
- détecter les mouvements dans l'image ;
- détecter les visages avec le classificateur Haar d'OpenCV ;
- afficher le nombre d'images par seconde (FPS) ;
- enregistrer des captures pour documenter les tests.

## Organisation du dépôt

```text
Smart_Blackjack/
├── rasberry/
│   ├── README.md
│   └── camera.py
└── README.md
```

Le dossier [`rasberry/`](./rasberry/) contient la documentation et les scripts
destinés au Raspberry Pi. Le nom `rasberry` est conservé pour correspondre au
nom actuel du dossier dans le projet.

## Démarrage rapide

Le test de caméra se lance sur le Raspberry Pi avec :

```bash
python3 rasberry/camera.py
```

Avant de l'exécuter, consultez le
[guide Raspberry Pi](./rasberry/README.md) pour l'installation, le branchement
de la caméra et les commandes de test.

## Contributions

Les modifications doivent être testées sur le matériel disponible et la
documentation correspondante doit être mise à jour lorsque le comportement
du projet change.
--