# Reconnaissance des cartes (modèle) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entraîner un YOLOv8n sur le dataset Roboflow (export YOLOv8) et le faire tourner en direct sur la caméra du Raspberry Pi.

**Architecture:** Dataset re-téléchargé depuis Roboflow au format YOLOv8 ; un notebook Colab l'entraîne et exporte en NCNN. Côté Pi, un module réutilisable `rasberry/detection_cartes.py` (servira plus tard au calcul des scores) et un script de démonstration `rasberry/test_cartes.py`.

**Tech Stack:** Python 3, ultralytics (YOLOv8), NCNN, OpenCV, pytest, Google Colab.

**Spec:** `docs/superpowers/specs/2026-11-20-reconnaissance-cartes-design.md`

## Global Constraints

- Cible : Raspberry Pi 4, CPU seulement, Raspberry Pi OS 64 bits (`aarch64`).
- Modèle : `yolov8n.pt`, entraînement en `imgsz=640`, export `format="ncnn"`.
- Caméra : toujours via `ouvrir_camera()` de `rasberry/camera.py`.
- Code, noms et commentaires en français, style des fichiers existants (`camera.py`).
- `ultralytics` est importé paresseusement : les tests doivent tourner sur un PC sans ultralytics.
- Pas d'Aliot, pas de zones, pas de scores dans cette étape.

## Review Focus

- Le `data.yaml` de Roboflow utilise des chemins relatifs (`../train/images`) qui cassent sur Colab → le notebook les réécrit en chemins absolus.
- Le zip Roboflow peut contenir un niveau de dossier en plus → chercher `data.yaml` récursivement.
- Une même carte détectée deux fois (ses deux coins) → apparaît une seule fois dans la liste des cartes.
- Dossier du modèle absent sur le Pi → message clair qui dit quoi faire.

---

### Task 1: Notebook d'entraînement Colab

**Files:**
- Create: `ia/entrainement_cartes.ipynb`

**Interfaces:**
- Consumes: zip Roboflow exporté au format « YOLOv8 ».
- Produces: dossier `cartes_ncnn_model/` téléchargé, à placer dans `rasberry/modele/cartes_ncnn_model/`.

Cellules (markdown en français entre chaque) :
1. Vérifier le GPU (`!nvidia-smi`), `!pip install ultralytics`.
2. Téléverser le zip (`google.colab.files.upload()`), le décompresser dans `/content/dataset`, trouver `data.yaml` récursivement, réécrire `train`/`val`/`test` en chemins absolus (`train/images`, `valid/images`, `test/images` si présent) et `path`, afficher `nc` (attendu : 52).
3. `YOLO("yolov8n.pt").train(data=<data.yaml corrigé>, imgsz=640, epochs=100, patience=20, batch=16, fliplr=0.0, name="cartes")`. `fliplr=0.0` parce qu'un coin de carte retourné en miroir n'existe pas en vrai.
4. Validation : `model.val()`, afficher mAP50 et mAP50-95, et quelques prédictions sur `test/images`.
5. Export : `YOLO(".../best.pt").export(format="ncnn", imgsz=640)`, zip du dossier `best_ncnn_model` renommé `cartes_ncnn_model`, plus `best.pt`, puis `files.download`.

- [ ] **Step 1:** Écrire le notebook.
- [ ] **Step 2: Verify** `python -c "import json; nb=json.load(open('ia/entrainement_cartes.ipynb', encoding='utf-8')); print(len(nb['cells']))"` → JSON valide. L'exécution réelle se fait sur Colab par l'utilisateur.
- [ ] **Step 3: Commit** `git commit -m "Notebook Colab d'entraînement du modèle de cartes"`

### Task 2: Détection sur le Pi + script de test + doc

**Files:**
- Create: `rasberry/detection_cartes.py`
- Create: `rasberry/test_cartes.py`
- Create: `rasberry/modele/.gitkeep`
- Modify: `rasberry/requirements.txt` (ajouter `ultralytics`)
- Modify: `rasberry/README.md` (section « Reconnaissance des cartes »)
- Modify: `README.md` (arbre du dépôt + ligne du tableau de démarrage rapide)
- Test: `rasberry/tests/test_detection_cartes.py`

**Interfaces:**
- Consumes: `ouvrir_camera()` (`rasberry/camera.py`), dossier `rasberry/modele/cartes_ncnn_model/` (Task 1).
- Produces (pour l'étape « scores ») :
  - `@dataclass Detection: nom: str; confiance: float; boite: tuple[int, int, int, int]` (x1, y1, x2, y2 en pixels).
  - `cartes_uniques(detections: list[Detection]) -> list[str]` — un nom par carte, ordre de confiance décroissante.
  - `class DetecteurCartes(chemin_modele=CHEMIN_MODELE, seuil=SEUIL_CONFIANCE, taille=TAILLE_IMAGE)` avec `detecter(frame) -> list[Detection]`. Constantes de réglage en haut du module, style `camera.py` : `CHEMIN_MODELE` = `rasberry/modele/cartes_ncnn_model` (relatif au fichier), `SEUIL_CONFIANCE = 0.5`, `TAILLE_IMAGE = 640`. Si le dossier n'existe pas : `FileNotFoundError` avec un message qui dit de lancer le notebook et de copier le dossier. `from ultralytics import YOLO` dans `__init__`.

- [ ] **Step 1: Write the failing tests**

```python
def test_coins_doubles_comptes_une_fois():
    d = [Detection("AH", 0.9, (0, 0, 10, 10)), Detection("AH", 0.7, (50, 50, 60, 60)),
         Detection("10C", 0.8, (20, 20, 30, 30))]
    assert cartes_uniques(d) == ["AH", "10C"]

def test_aucune_detection():
    assert cartes_uniques([]) == []

def test_modele_absent_message_clair(tmp_path):
    with pytest.raises(FileNotFoundError, match="entrainement_cartes"):
        DetecteurCartes(chemin_modele=tmp_path / "absent")
```

(Le test du modèle absent doit vérifier le dossier **avant** d'importer ultralytics.)

- [ ] **Step 2: Run** `python -m pytest rasberry/tests -v` → FAIL (import).
- [ ] **Step 3: Implement** `rasberry/detection_cartes.py`. `detecter` appelle `self.modele(frame, imgsz=self.taille, conf=self.seuil, verbose=False)[0]` et lit `boxes.xyxy`, `boxes.conf`, `boxes.cls` + `modele.names`.
- [ ] **Step 4: Run** `python -m pytest rasberry/tests -v` → 3 passed.
- [ ] **Step 5: Implement** `rasberry/test_cartes.py` sur le modèle de la boucle de `camera.py` : boîtes + `nom confiance` au-dessus, FPS lissé, `cartes_uniques` imprimé dans le terminal seulement quand la liste change, touches `q` (quitter) et `s` (capture dans `captures/`).
- [ ] **Step 6:** Ajouter `ultralytics` au requirements, la section README du Pi (vérifier `uname -m` → `aarch64`, `pip install -r rasberry/requirements.txt`, copier `cartes_ncnn_model/` dans `rasberry/modele/`, `python3 rasberry/test_cartes.py`, réexport en 416 si trop lent), et mettre à jour `README.md`.
- [ ] **Step 7: Verify** `python -m pytest rasberry/tests -v` → tout passe ; `python -m py_compile rasberry/test_cartes.py`.
- [ ] **Step 8: Commit** `git commit -m "Détection des cartes sur le Raspberry Pi"`

### Vérification finale (utilisateur, sur le matériel)

Notebook exécuté sur Colab → mAP50 affiché ; `python3 rasberry/test_cartes.py` sur le Pi → cartes reconnues sur la table, FPS noté.
