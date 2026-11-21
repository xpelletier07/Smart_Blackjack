from detection_cartes import Detection
from scores import Stabilisateur, position_ligne, separer_mains, valeur_main


def test_valeur_cartes_simples():
    assert valeur_main(["10C", "7H"]) == 17
    assert valeur_main(["KS", "QD"]) == 20
    assert valeur_main(["JH", "2S"]) == 12


def test_blackjack():
    assert valeur_main(["AH", "KS"]) == 21


def test_as_vaut_1_si_ca_depasse():
    assert valeur_main(["AH", "9C", "5D"]) == 15
    assert valeur_main(["AH", "AD"]) == 12
    assert valeur_main(["AH", "AD", "9S"]) == 21


def test_main_vide():
    assert valeur_main([]) == 0


def _d(nom, y, confiance=0.8):
    return Detection(nom, confiance, (100, y - 10, 120, y + 10))


def test_separer_mains_croupier_en_bas():
    detections = [_d("KS", 100), _d("7H", 150), _d("AD", 300), _d("9C", 400)]
    joueur, croupier = separer_mains(detections, ligne_y=240)
    assert sorted(joueur) == ["7H", "KS"]
    assert sorted(croupier) == ["9C", "AD"]


def test_separer_mains_deux_coins_comptes_une_fois():
    # les deux coins du 8D sont vus : une seule carte
    detections = [_d("8D", 100, 0.9), _d("8D", 180, 0.7), _d("3C", 120)]
    joueur, croupier = separer_mains(detections, ligne_y=240)
    assert sorted(joueur) == ["3C", "8D"]
    assert croupier == []


def test_position_ligne_dans_la_zone():
    assert position_ligne((160, 0, 480, 480), 480) == 240
    assert position_ligne((0, 100, 640, 300), 480, partage=0.25) == 150


def test_position_ligne_sans_zone():
    assert position_ligne(None, 480) == 240


def test_carte_a_cheval_sur_la_ligne_comptee_d_un_seul_cote():
    # coin du haut à y=200 (au-dessus), coin du bas à y=300 (en dessous) : milieu 250 -> croupier
    detections = [_d("KS", 200), _d("KS", 300), _d("7H", 100)]
    joueur, croupier = separer_mains(detections, ligne_y=240)
    assert joueur == ["7H"]
    assert croupier == ["KS"]


def test_stabilisateur_carte_retenue_apres_plusieurs_images():
    s = Stabilisateur(nb_images=5, minimum=3)
    assert s.ajouter(["KS"], []) == ([], [])
    assert s.ajouter(["KS"], []) == ([], [])
    assert s.ajouter(["KS"], []) == (["KS"], [])


def test_stabilisateur_ignore_une_carte_fantome():
    s = Stabilisateur(nb_images=5, minimum=3)
    for _ in range(4):
        s.ajouter(["KS"], ["AD"])
    assert s.ajouter(["KS", "8S"], ["AD"]) == (["KS"], ["AD"])


def test_stabilisateur_garde_une_carte_ratee_une_fois():
    s = Stabilisateur(nb_images=5, minimum=3)
    for _ in range(4):
        s.ajouter(["KS", "7H"], [])
    assert s.ajouter(["KS"], []) == (["7H", "KS"], [])


def test_stabilisateur_carte_retiree_finit_par_disparaitre():
    s = Stabilisateur(nb_images=5, minimum=3)
    for _ in range(5):
        s.ajouter(["KS"], [])
    resultats = [s.ajouter([], []) for _ in range(3)]
    assert resultats[-1] == ([], [])


def test_stabilisateur_mains_separees():
    s = Stabilisateur(nb_images=3, minimum=2)
    s.ajouter(["KS"], ["AD"])
    assert s.ajouter(["KS"], ["AD"]) == (["KS"], ["AD"])
