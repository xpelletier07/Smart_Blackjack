#!/usr/bin/env python3
"""
scores.py - Partage des cartes entre joueur et croupier, et calcul des scores.

La zone de jeu est coupée par une ligne horizontale :
  - en haut : le joueur ;
  - en bas  : le croupier.

On joue avec un seul paquet : un nom de carte (ex. "8D") correspond toujours à
une seule carte, même si ses deux coins sont vus.
"""

from detection_cartes import cartes_uniques

# ----------------------------- Réglages ------------------------------------
LIGNE_PARTAGE = 0.5   # position de la ligne dans la zone de jeu (0 = haut, 1 = bas)
# ---------------------------------------------------------------------------


def valeur_main(cartes):
    """Score de blackjack d'une main (ex. ["AH", "KS"] -> 21). L'as vaut 11,
    ou 1 si la main dépasserait 21."""
    total = 0
    nb_as = 0
    for nom in cartes:
        rang = nom[:-1]  # "10C" -> "10", "AH" -> "A"
        if rang == "A":
            total += 11
            nb_as += 1
        elif rang in ("J", "Q", "K"):
            total += 10
        else:
            total += int(rang)
    while total > 21 and nb_as:
        total -= 10
        nb_as -= 1
    return total


def position_ligne(zone, hauteur_image, partage=LIGNE_PARTAGE):
    """Ordonnée (en pixels) de la ligne joueur / croupier dans l'image."""
    haut, bas = (zone[1], zone[3]) if zone is not None else (0, hauteur_image)
    return round(haut + partage * (bas - haut))


def separer_mains(detections, ligne_y):
    """Retourne (cartes du joueur, cartes du croupier). Chaque carte va d'un seul
    côté : celui du milieu de ses coins détectés (une carte posée à cheval sur la
    ligne a un coin de chaque côté)."""
    centres = {}
    for d in detections:
        centres.setdefault(d.nom, []).append((d.boite[1] + d.boite[3]) / 2)
    haut, bas = [], []
    for d in detections:
        milieu = sum(centres[d.nom]) / len(centres[d.nom])
        (haut if milieu < ligne_y else bas).append(d)
    return cartes_uniques(haut), cartes_uniques(bas)
