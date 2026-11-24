"""
flux_web.py - Diffuse sur le réseau l'image annotée de la caméra MediaPipe.

Même logique que rasberry/camera_serveur.py :
  port 5000 -> page interactive (flux + boutons s = capture, q = quitter)
  port 5001 -> flux vidéo seul, pour <img src="https://<ip>:5001/"> (AliveCode)

Utilisation (voir detection_action.py) :
  flux_web.demarrer()                 # une fois, avant la boucle
  flux_web.publier(image, action)     # à chaque image
  flux_web.arret.is_set()             # True si on a cliqué sur Quitter

HTTPS (requis par le dashboard AliveCode) : actif si le paquet
`cryptography` est installé, sinon le serveur démarre en HTTP.
  pip install flask cryptography
"""

import os
import threading
import time
from datetime import datetime

import cv2
from flask import Flask, Response, abort, jsonify, request, send_from_directory
from werkzeug.serving import make_server

HOTE = "0.0.0.0"
PORT = 5000        # page interactive
PORT_FLUX = 5001   # flux vidéo seul
QUALITE_JPEG = 80
DOSSIER_CAPTURES = "captures"

verrou = threading.Lock()
etat = {"action": "Aucune", "fps": 0.0, "message": ""}
dernier_jpeg = None
demande_capture = False
arret = threading.Event()
_temps_precedent = time.time()


def publier(image, action="Aucune"):
    """Encode l'image (déjà annotée) pour les navigateurs connectés."""
    global dernier_jpeg, demande_capture, _temps_precedent

    maintenant = time.time()
    fps = 0.9 * etat["fps"] + 0.1 * (1.0 / max(maintenant - _temps_precedent, 1e-6))
    _temps_precedent = maintenant

    if demande_capture:
        demande_capture = False
        os.makedirs(DOSSIER_CAPTURES, exist_ok=True)
        nom = datetime.now().strftime("capture_%Y%m%d_%H%M%S.jpg")
        ok = cv2.imwrite(os.path.join(DOSSIER_CAPTURES, nom), image)
        with verrou:
            etat["message"] = f"Capture sauvegardée : {nom}" if ok else "Échec de la capture"

    ok, jpeg = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, QUALITE_JPEG])
    if ok:
        with verrou:
            dernier_jpeg = jpeg.tobytes()
            etat["fps"] = round(fps, 1)
            etat["action"] = action


def generer_flux():
    derniere = None
    while not arret.is_set():
        with verrou:
            jpeg = dernier_jpeg
        if jpeg is None or jpeg is derniere:
            time.sleep(0.01)
            continue
        derniere = jpeg
        yield b"--image\r\nContent-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"


def reponse_flux():
    return Response(generer_flux(), mimetype="multipart/x-mixed-replace; boundary=image")


PAGE = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Smart Blackjack - Camera</title>
<style>
  body { font-family: sans-serif; background: #1e1e1e; color: #ddd; margin: 0;
         display: flex; flex-direction: column; align-items: center; }
  img { max-width: 100%; margin-top: 8px; border: 1px solid #444; }
  .barre { margin: 8px; display: flex; gap: 8px; flex-wrap: wrap; justify-content: center; }
  button { padding: 6px 12px; cursor: pointer; }
  #statut { min-height: 1.4em; margin: 4px; }
</style>
</head>
<body>
  <img src="/flux" alt="Flux caméra">
  <div class="barre">
    <button data-touche="s">[s] Capture</button>
    <button data-touche="q">[q] Quitter</button>
  </div>
  <div id="statut">Cliquez sur la page puis utilisez les touches s, q.</div>
<script>
const statut = document.getElementById("statut");
function afficher(e) {
  const parts = ["Dernière action : " + e.action, e.fps + " FPS"];
  if (e.message) parts.push(e.message);
  statut.textContent = parts.join("  |  ");
}
async function envoyer(t) {
  try { afficher(await (await fetch("/touche/" + t, { method: "POST" })).json()); }
  catch (err) { statut.textContent = "Serveur injoignable."; }
}
document.addEventListener("keydown", (ev) => {
  if (ev.ctrlKey || ev.metaKey || ev.altKey) return;
  const t = ev.key.toLowerCase();
  if (t === "s" || t === "q") { ev.preventDefault(); envoyer(t); }
});
document.querySelectorAll("button").forEach((b) =>
  b.addEventListener("click", () => envoyer(b.dataset.touche)));
setInterval(async () => {
  try { afficher(await (await fetch("/etat")).json()); } catch (e) {}
}, 1000);
</script>
</body>
</html>
"""

# ---- Port 5000 : page interactive ----
app = Flask("flux_web")


@app.route("/")
def index():
    return PAGE


@app.route("/flux")
def flux():
    return reponse_flux()


@app.route("/etat")
def lire_etat():
    with verrou:
        return jsonify(etat)


@app.route("/touche/<touche>", methods=["POST", "OPTIONS"])
def appuyer_touche(touche):
    global demande_capture
    if request.method == "OPTIONS":   # pré-vérification CORS du navigateur
        return "", 204
    with verrou:
        etat["message"] = ""
        if touche == "s":
            demande_capture = True
            etat["message"] = "Capture en cours..."
        elif touche == "q":
            etat["message"] = "Arrêt de la détection."
            arret.set()   # detection_action.py sort de sa boucle
        else:
            abort(404)
        return jsonify(etat)


@app.route("/captures/<path:nom>")
def telecharger_capture(nom):
    return send_from_directory(os.path.abspath(DOSSIER_CAPTURES), nom)


# ---- Port 5001 : flux vidéo seul ----
app_flux = Flask("flux_web_seul")


@app_flux.route("/")
@app_flux.route("/flux")
def flux_seul():
    return reponse_flux()


@app.after_request
@app_flux.after_request
def autoriser_dashboard(reponse):
    """Autorise le dashboard AliveCode à appeler le serveur."""
    reponse.headers["Access-Control-Allow-Origin"] = "*"
    reponse.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    reponse.headers["Access-Control-Allow-Headers"] = "Content-Type"
    reponse.headers["Access-Control-Allow-Private-Network"] = "true"
    return reponse


def demarrer(https=True):
    """Lance les deux serveurs en arrière-plan (ne bloque pas)."""
    ssl = None
    if https:
        try:
            import cryptography  # noqa: F401  requis pour le certificat auto-signé
            ssl = "adhoc"
        except ImportError:
            print("Paquet 'cryptography' absent : flux web en HTTP "
                  "(bloqué par AliveCode). pip install cryptography")
    schema = "https" if ssl else "http"

    for application, port in ((app, PORT), (app_flux, PORT_FLUX)):
        serveur = make_server(HOTE, port, application, threaded=True, ssl_context=ssl)
        threading.Thread(target=serveur.serve_forever, daemon=True).start()

    print(f"Page interactive : {schema}://<adresse-ip>:{PORT}")
    print(f"Flux seul        : {schema}://<adresse-ip>:{PORT_FLUX}")
