# Reconnaissance des cartes (modèle) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entraîner un YOLOv8n sur le dataset Roboflow (COCO JSON) et le faire tourner en direct sur la caméra du Raspberry Pi.

**Architecture:** Un module de conversion COCO → YOLO testé (`ia/coco_vers_yolo.py`) appelé par un notebook Colab qui entraîne et exporte en NCNN. Côté Pi, un module réutilisable `rasberry/detection_cartes.py` (servira plus tard au calcul des scores) et un script de démonstration `rasberry/test_cartes.py`.

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

- Roboflow ajoute une catégorie « supercatégorie » (id 0, ex. `cards`) jamais utilisée par les annotations → elle ne doit pas devenir une classe.
- Image sans annotation → fichier label vide (sinon ultralytics la compte comme image manquante).
- Dossier Roboflow `valid/` → split `val` attendu par ultralytics.
- Boîte qui dépasse le bord de l'image → coordonnées normalisées bornées à [0, 1].
- Une même carte détectée deux fois (ses deux coins) → apparaît une seule fois dans la liste des cartes.

---

### Task 1: Conversion COCO → YOLO

**Files:**
- Create: `ia/coco_vers_yolo.py`
- Create: `ia/requirements.txt` (`pytest`)
- Test: `ia/tests/test_coco_vers_yolo.py`

**Interfaces:**
- Produces:
  - `bbox_coco_vers_yolo(bbox: list[float], largeur: int, hauteur: int) -> tuple[float, float, float, float]` — `[x, y, w, h]` en pixels (coin haut-gauche) → `(cx, cy, w, h)` normalisés et bornés à [0, 1].
  - `classes_utilisees(coco: dict) -> list[dict]` — catégories référencées par au moins une annotation, triées par `id`.
  - `convertir_dataset(dossier_coco: Path, dossier_sortie: Path) -> list[str]` — lit `{train,valid,test}/_annotations.coco.json` (splits absents ignorés), écrit `dossier_sortie/images/<split>/` (copie), `dossier_sortie/labels/<split>/<nom>.txt` (lignes `classe cx cy w h`), et `dossier_sortie/data.yaml` (`path`, `train: images/train`, `val: images/val`, `test` si présent, `names` en liste). Retourne les noms des classes. Les classes sont calculées sur l'union des splits pour garder les mêmes indices partout. `data.yaml` est écrit à la main (pas de dépendance PyYAML).

- [ ] **Step 1: Write the failing tests** — fixture `dataset_coco(tmp_path)` qui crée `train/` et `valid/` avec de petites images (`cv2` ou octets bidons : la conversion copie sans décoder) et un JSON contenant la catégorie 0 `cards` (supercatégorie) + `10C`, `AH`.

```python
def test_bbox_centre_normalise():
    assert bbox_coco_vers_yolo([10, 20, 30, 40], 100, 200) == pytest.approx((0.25, 0.2, 0.3, 0.2))

def test_bbox_bornee_au_bord():
    cx, cy, w, h = bbox_coco_vers_yolo([90, 0, 30, 10], 100, 100)
    assert all(0.0 <= v <= 1.0 for v in (cx, cy, w, h))

def test_supercategorie_ignoree(dataset_coco, tmp_path):
    noms = convertir_dataset(dataset_coco, tmp_path / "sortie")
    assert noms == ["10C", "AH"]

def test_valid_devient_val_et_labels(dataset_coco, tmp_path):
    convertir_dataset(dataset_coco, tmp_path / "sortie")
    assert (tmp_path / "sortie/images/val").is_dir()
    lignes = (tmp_path / "sortie/labels/train/img1.txt").read_text().split("\n")
    assert lignes[0].split()[0] == "0"  # 10C -> classe 0

def test_image_sans_annotation_label_vide(dataset_coco, tmp_path):
    convertir_dataset(dataset_coco, tmp_path / "sortie")
    assert (tmp_path / "sortie/labels/train/vide.txt").read_text() == ""

def test_data_yaml(dataset_coco, tmp_path):
    convertir_dataset(dataset_coco, tmp_path / "sortie")
    texte = (tmp_path / "sortie/data.yaml").read_text()
    assert "val: images/val" in texte and "10C" in texte and "cards" not in texte
```

- [ ] **Step 2: Run** `python -m pytest ia/tests -v` → FAIL (`ModuleNotFoundError: coco_vers_yolo`).
- [ ] **Step 3: Implement** les trois fonctions dans `ia/coco_vers_yolo.py`, plus un `if __name__ == "__main__":` qui prend `dossier_coco dossier_sortie` en arguments.
- [ ] **Step 4: Run** `python -m pytest ia/tests -v` → 6 passed.
- [ ] **Step 5: Commit** `git add ia && git commit -m "Conversion du dataset COCO vers YOLO"`

### Task 2: Notebook d'entraînement Colab

**Files:**
- Create: `ia/entrainement_cartes.ipynb`

**Interfaces:**
- Consumes: `convertir_dataset(dossier_coco, dossier_sortie) -> list[str]` (Task 1).
- Produces: dossier `cartes_ncnn_model/` téléchargé, à placer dans `rasberry/modele/cartes_ncnn_model/`.

Cellules (markdown en français entre chaque) :
1. Vérifier le GPU (`!nvidia-smi`), `!pip install ultralytics`.
2. Récupérer `coco_vers_yolo.py` (`!wget` du fichier brut sur `https://raw.githubusercontent.com/xpelletier07/Smart_Blackjack/main/ia/coco_vers_yolo.py`), téléverser le zip du dataset (`google.colab.files.upload()`), le décompresser dans `/content/coco`. Trouver le dossier qui contient `train/_annotations.coco.json` (le zip Roboflow peut avoir un niveau de dossier en plus).
3. `convertir_dataset(...)` → `/content/yolo`, afficher le nombre de classes (attendu : 52).
4. `YOLO("yolov8n.pt").train(data="/content/yolo/data.yaml", imgsz=640, epochs=100, patience=20, batch=16, fliplr=0.0, name="cartes")`. `fliplr=0.0` parce qu'un coin de carte retourné en miroir n'existe pas en vrai.
5. Validation : `model.val()`, afficher mAP50 et mAP50-95, et quelques prédictions sur `images/test`.
6. Export : `YOLO(".../best.pt").export(format="ncnn", imgsz=640)`, zip du dossier `best_ncnn_model` renommé `cartes_ncnn_model`, plus `best.pt`, puis `files.download`.

- [ ] **Step 1:** Écrire le notebook.
- [ ] **Step 2: Verify** `python -c "import json; nb=json.load(open('ia/entrainement_cartes.ipynb', encoding='utf-8')); print(len(nb['cells']))"` → JSON valide. L'exécution réelle se fait sur Colab par l'utilisateur.
- [ ] **Step 3: Commit** `git commit -m "Notebook Colab d'entraînement du modèle de cartes"`

### Task 3: Détection sur le Pi + script de test + doc

**Files:**
- Create: `rasberry/detection_cartes.py`
- Create: `rasberry/test_cartes.py`
- Create: `rasberry/modele/.gitkeep`
- Modify: `rasberry/requirements.txt` (ajouter `ultralytics`)
- Modify: `rasberry/README.md` (section « Reconnaissance des cartes »)
- Modify: `README.md` (arbre du dépôt + ligne du tableau de démarrage rapide)
- Test: `rasberry/tests/test_detection_cartes.py`

**Interfaces:**
- Consumes: `ouvrir_camera()` (`rasberry/camera.py`), dossier `rasberry/modele/cartes_ncnn_model/` (Task 2).
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
- [ ] **Step 7: Verify** `python -m pytest ia/tests rasberry/tests -v` → tout passe ; `python -m py_compile rasberry/test_cartes.py`.
- [ ] **Step 8: Commit** `git commit -m "Détection des cartes sur le Raspberry Pi"`

### Vérification finale (utilisateur, sur le matériel)

Notebook exécuté sur Colab → mAP50 affiché ; `python3 rasberry/test_cartes.py` sur le Pi → cartes reconnues sur la table, FPS noté.
