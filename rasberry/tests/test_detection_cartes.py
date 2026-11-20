import pytest

from detection_cartes import DetecteurCartes, Detection, cartes_uniques


def test_coins_doubles_comptes_une_fois():
    d = [Detection("AH", 0.9, (0, 0, 10, 10)), Detection("AH", 0.7, (50, 50, 60, 60)),
         Detection("10C", 0.8, (20, 20, 30, 30))]
    assert cartes_uniques(d) == ["AH", "10C"]


def test_aucune_detection():
    assert cartes_uniques([]) == []


def test_modele_absent_message_clair(tmp_path):
    with pytest.raises(FileNotFoundError, match="entrainement_cartes"):
        DetecteurCartes(chemin_modele=tmp_path / "absent")
