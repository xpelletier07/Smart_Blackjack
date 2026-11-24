import threading

from camera import CameraPartagee


class FausseCamera:
    """Donne les images 1, 2, 3 puis plus rien (caméra débranchée)."""

    def __init__(self):
        self.images = [1, 2, 3]
        self.fermee = False
        self.peut_lire = threading.Event()   # le test choisit quand une image arrive

    def lire(self):
        self.peut_lire.wait(timeout=2)
        self.peut_lire.clear()
        return self.images.pop(0) if self.images else None

    def fermer(self):
        self.fermee = True


def test_deux_lecteurs_recoivent_la_meme_image():
    source = FausseCamera()
    camera = CameraPartagee(source)
    resultats = []
    lecteurs = [threading.Thread(target=lambda: resultats.append(camera.lire())) for _ in range(2)]
    for t in lecteurs:
        t.start()
    source.peut_lire.set()
    for t in lecteurs:
        t.join(timeout=2)
    assert resultats == [1, 1]
    camera.fermer()


def test_lire_attend_une_nouvelle_image():
    source = FausseCamera()
    camera = CameraPartagee(source)
    source.peut_lire.set()
    assert camera.lire() == 1
    source.peut_lire.set()
    assert camera.lire() == 2   # pas deux fois la même image pour le même lecteur
    camera.fermer()


def test_none_quand_la_camera_s_arrete():
    source = FausseCamera()
    source.images = []
    camera = CameraPartagee(source)
    source.peut_lire.set()
    assert camera.lire() is None
    assert source.fermee
