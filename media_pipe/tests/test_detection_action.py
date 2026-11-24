from types import SimpleNamespace

from detection_action import Confirmation, compter_doigts


def _main(pouce_leve=False, doigts_leves=()):
    """21 points MediaPipe d'une main droite : bout du pouce = 4, bouts des doigts = 8, 12, 16, 20."""
    points = [SimpleNamespace(x=0.5, y=0.5) for _ in range(21)]
    points[3].x = 0.5
    points[4].x = 0.4 if pouce_leve else 0.6
    for bout in (8, 12, 16, 20):
        points[bout].y = 0.3 if bout in doigts_leves else 0.7   # plus haut = y plus petit
    return points


def test_poing_ferme():
    assert compter_doigts(_main(), "Right") == 0


def test_deux_doigts():
    assert compter_doigts(_main(doigts_leves=(8, 12)), "Right") == 2


def test_pouce_main_droite_et_gauche():
    assert compter_doigts(_main(pouce_leve=True), "Right") == 1
    assert compter_doigts(_main(pouce_leve=True), "Left") == 0


def test_action_envoyee_apres_le_temps_de_confirmation():
    c = Confirmation(temps=1.5)
    assert c.ajouter("Hit", 0.0) is None
    assert c.ajouter("Hit", 1.0) is None
    assert c.ajouter("Hit", 1.6) == "Hit"


def test_action_envoyee_une_seule_fois():
    c = Confirmation(temps=1.5)
    c.ajouter("Hit", 0.0)
    assert c.ajouter("Hit", 2.0) == "Hit"
    assert c.ajouter("Hit", 3.0) is None


def test_changer_de_geste_recommence_le_compte():
    c = Confirmation(temps=1.5)
    c.ajouter("Hit", 0.0)
    assert c.ajouter("Stand", 1.0) is None
    assert c.ajouter("Stand", 2.0) is None
    assert c.ajouter("Stand", 2.6) == "Stand"


def test_retirer_la_main_permet_de_refaire_le_meme_geste():
    c = Confirmation(temps=1.5)
    c.ajouter("Hit", 0.0)
    assert c.ajouter("Hit", 2.0) == "Hit"
    c.ajouter(None, 3.0)
    c.ajouter("Hit", 4.0)
    assert c.ajouter("Hit", 5.6) == "Hit"
