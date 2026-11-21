import numpy as np
import pytest

from detection_cartes import (DetecteurCartes, Detection, cartes_uniques, decaler_detections,
                              decoder_sortie, lire_noms, preparer_image, rogner)


def test_coins_doubles_comptes_une_fois():
    d = [Detection("AH", 0.9, (0, 0, 10, 10)), Detection("AH", 0.7, (50, 50, 60, 60)),
         Detection("10C", 0.8, (20, 20, 30, 30))]
    assert cartes_uniques(d) == ["AH", "10C"]


def test_aucune_detection():
    assert cartes_uniques([]) == []


def test_modele_absent_message_clair(tmp_path):
    with pytest.raises(FileNotFoundError, match="README"):
        DetecteurCartes(chemin_modele=tmp_path / "absent")


def test_lire_noms(tmp_path):
    meta = tmp_path / "metadata.yaml"
    meta.write_text('task: detect\nnames:\n  0: "10C"\n  1: "AH"\nargs:\n  batch: 1\n', encoding="utf-8")
    assert lire_noms(meta) == {0: "10C", 1: "AH"}


def test_preparer_image_letterbox():
    frame = np.zeros((480, 640, 3), np.uint8)
    blob, ratio, (pad_x, pad_y) = preparer_image(frame, 640)
    assert blob.shape == (3, 640, 640) and blob.dtype == np.float32
    assert ratio == 1.0 and (pad_x, pad_y) == (0, 80)
    assert blob[:, 0, 0] == pytest.approx(114 / 255)    # bande grise ajoutée
    assert blob[:, 320, 320] == pytest.approx(0.0)      # image d'origine


def _sortie(boites, nb_classes=3):
    """Construit une sortie YOLO (4 + nb_classes, N) : boites = [(cx, cy, w, h, classe, score)]."""
    sortie = np.zeros((4 + nb_classes, len(boites)), np.float32)
    for i, (cx, cy, w, h, classe, score) in enumerate(boites):
        sortie[:4, i] = (cx, cy, w, h)
        sortie[4 + classe, i] = score
    return sortie


def test_decoder_sortie_nms_et_remise_a_l_echelle():
    noms = {0: "10C", 1: "AH", 2: "KS"}
    sortie = _sortie([
        (320, 200, 40, 60, 1, 0.9),    # AH
        (322, 202, 40, 60, 1, 0.8),    # même coin, doublon -> supprimé par la NMS
        (100, 300, 20, 20, 0, 0.3),    # sous le seuil -> ignoré
        (500, 400, 40, 40, 2, 0.7),    # KS
    ])
    detections = decoder_sortie(sortie, ratio=1.0, pad=(0, 80), seuil=0.5,
                                largeur=640, hauteur=480, noms=noms)
    assert [d.nom for d in detections] == ["AH", "KS"]
    assert detections[0].confiance == pytest.approx(0.9)
    assert detections[0].boite == (300, 90, 340, 150)   # y remis dans l'image d'origine (pad 80)


def test_decoder_sortie_boite_bornee_a_l_image():
    sortie = _sortie([(630, 470, 40, 40, 0, 0.9)], nb_classes=1)
    (d,) = decoder_sortie(sortie, ratio=1.0, pad=(0, 0), seuil=0.5,
                          largeur=640, hauteur=480, noms={0: "10C"})
    assert d.boite == (610, 450, 640, 480)


def test_rogner_sans_zone_garde_toute_l_image():
    frame = np.zeros((480, 640, 3), np.uint8)
    image, decalage = rogner(frame, None)
    assert image.shape == (480, 640, 3) and decalage == (0, 0)


def test_rogner_zone_et_decalage():
    frame = np.zeros((480, 640, 3), np.uint8)
    frame[120, 130] = 255
    image, decalage = rogner(frame, (130, 120, 640, 300))
    assert image.shape == (180, 510, 3) and decalage == (130, 120)
    assert image[0, 0, 0] == 255


def test_rogner_zone_bornee_a_l_image():
    frame = np.zeros((480, 640, 3), np.uint8)
    image, decalage = rogner(frame, (-20, 400, 700, 900))
    assert image.shape == (80, 640, 3) and decalage == (0, 400)


def test_decaler_detections():
    d = [Detection("AH", 0.9, (10, 20, 30, 40))]
    assert decaler_detections(d, (130, 120))[0].boite == (140, 140, 160, 160)


def test_decoder_sortie_un_seul_nom_par_coin():
    # cas réel : le même coin lu "QC" (0.58) et "QS" (0.32) -> on garde le plus sûr
    sortie = _sortie([
        (279, 114, 12, 24, 0, 0.58),
        (278.5, 113.5, 11, 25, 2, 0.32),
    ])
    detections = decoder_sortie(sortie, ratio=1.0, pad=(0, 0), seuil=0.3,
                                largeur=640, hauteur=480, noms={0: "QC", 1: "AH", 2: "QS"})
    assert [d.nom for d in detections] == ["QC"]


def test_decoder_sortie_cartes_voisines_gardees():
    # coins de deux cartes en escalier : décalés, ils ne se superposent pas
    sortie = _sortie([
        (279, 114, 12, 24, 0, 0.7),
        (315, 88, 12, 24, 1, 0.7),
    ])
    detections = decoder_sortie(sortie, ratio=1.0, pad=(0, 0), seuil=0.3,
                                largeur=640, hauteur=480, noms={0: "QC", 1: "5H", 2: "QS"})
    assert sorted(d.nom for d in detections) == ["5H", "QC"]
