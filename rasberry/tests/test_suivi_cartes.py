from detection_cartes import Detection
from scores import Stabilisateur
from suivi_cartes import SuiviCartes


class FauxDetecteur:
    """Renvoie toujours les mêmes détections."""
    zone = (160, 0, 480, 480)  # ligne joueur / croupier à y = 240

    def __init__(self, detections):
        self.detections = detections

    def detecter(self, frame):
        return self.detections


class FausseImage:
    shape = (480, 640, 3)


def _d(nom, y):
    return Detection(nom, 0.8, (300, y - 10, 320, y + 10))


def test_scores_apres_stabilisation():
    detecteur = FauxDetecteur([_d("KS", 100), _d("7H", 150), _d("AD", 300)])
    suivi = SuiviCartes(detecteur, camera=None, stabilisateur=Stabilisateur(nb_images=3, minimum=2))
    assert suivi.analyser(FausseImage()) is False      # pas encore stable : rien ne change
    assert suivi.scores == (0, 0)
    assert suivi.analyser(FausseImage()) is True       # les mains ont changé
    assert suivi.mains == (["7H", "KS"], ["AD"])
    assert suivi.scores == (17, 11)


def test_pas_de_changement_si_memes_cartes():
    detecteur = FauxDetecteur([_d("KS", 100)])
    suivi = SuiviCartes(detecteur, camera=None, stabilisateur=Stabilisateur(nb_images=1, minimum=1))
    assert suivi.analyser(FausseImage()) is True
    assert suivi.analyser(FausseImage()) is False
