#!/usr/bin/env python3
"""
camera_server.py - Diffuse la caméra du Raspberry Pi sur le réseau.

Le flux, les annotations (mouvement, FPS) et les commandes clavier
sont accessibles depuis une page web, donc depuis VS Code (Simple Browser)
sur le poste de travail.

Touches (dans la page) :
  q  -> arrêter le serveur
  d  -> activer/désactiver la détection de mouvement
  s  -> enregistrer une capture (dossier captures/ sur le Raspberry Pi)

Installation sur le Raspberry Pi :
  sudo apt update
  sudo apt install -y python3-opencv python3-picamera2 python3-flask

Lancement (depuis la racine du dépôt) :
  python3 rasberry/camera_server.py
"""

import argparse
import os
import threading
import time
from datetime import datetime

import cv2
from flask import Flask, Response, abort, jsonify, request, send_from_directory
from werkzeug.serving import make_server

from camera import detecter_mouvement, ouvrir_camera

HOTE = "0.0.0.0"   # écoute sur toutes les interfaces du Pi
PORT = 5000        # page web interactive (flux + boutons d, s, q)
PORT_FLUX = 5001   # flux vidéo seul, pour <img src="https://<ip>:5001/">  (AliveCode)
QUALITE_JPEG = 80
DOSSIER_CAPTURES = "captures"

app = Flask(__name__)

verrou = threading.Lock()
etat = {
    "mouvement": True,
    "fps": 0.0,
    "message": "",
}
dernier_jpeg = None
demande_capture = False
arret = threading.Event()


def boucle_camera():
    """Lit la caméra, applique les analyses et garde la dernière image encodée."""
    global dernier_jpeg, demande_capture

    camera = ouvrir_camera()

    gris_precedent = None
    temps_precedent = time.time()
    fps = 0.0

    try:
        while not arret.is_set():
            frame = camera.lire()
            if frame is None:
                print("Image non reçue, arrêt.")
                break

            with verrou:
                mode_mouvement = etat["mouvement"]

            if mode_mouvement:
                gris_precedent, zones = detecter_mouvement(frame, gris_precedent)
                for (x, y, w, h) in zones:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                if zones:
                    cv2.putText(frame, "MOUVEMENT", (10, 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            else:
                gris_precedent = None

            maintenant = time.time()
            fps = 0.9 * fps + 0.1 * (1.0 / max(maintenant - temps_precedent, 1e-6))
            temps_precedent = maintenant
            cv2.putText(frame, f"{fps:.1f} FPS", (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            # Capture demandée depuis la page (touche s)
            if demande_capture:
                demande_capture = False
                os.makedirs(DOSSIER_CAPTURES, exist_ok=True)
                nom = datetime.now().strftime("capture_%Y%m%d_%H%M%S.jpg")
                chemin = os.path.join(DOSSIER_CAPTURES, nom)
                if cv2.imwrite(chemin, frame):
                    print(f"Capture sauvegardée : {chemin}")
                    with verrou:
                        etat["message"] = f"Capture sauvegardée : {nom}"
                else:
                    with verrou:
                        etat["message"] = f"Échec de la capture : {chemin}"

            ok, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, QUALITE_JPEG])
            if ok:
                with verrou:
                    dernier_jpeg = jpeg.tobytes()
                    etat["fps"] = round(fps, 1)
    except Exception as e:
        # sans ce message, le serveur reste ouvert mais le flux ne vient jamais
        print(f"ERREUR caméra, plus d'images envoyées : {e!r}")
        with verrou:
            etat["message"] = f"Erreur caméra : {e}"
        raise
    finally:
        camera.fermer()


def generer_flux():
    """Génère le flux MJPEG envoyé au navigateur."""
    derniere = None
    while not arret.is_set():
        with verrou:
            jpeg = dernier_jpeg
        if jpeg is None or jpeg is derniere:
            time.sleep(0.01)
            continue
        derniere = jpeg
        yield (b"--image\r\nContent-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n")


PAGE = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<title>Camera - Robot</title>
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
  <img id="video" src="/flux" alt="Flux caméra">
  <div class="barre">
    <button data-touche="d">[d] Mouvement</button>
    <button data-touche="s">[s] Capture</button>
    <button data-touche="q">[q] Quitter</button>
  </div>
  <div id="statut">Cliquez sur la page puis utilisez les touches d, s, q.</div>
<script>
const statut = document.getElementById("statut");

async function envoyer(touche) {
  try {
    const r = await fetch("/touche/" + touche, { method: "POST" });
    const e = await r.json();
    afficher(e);
  } catch (err) {
    statut.textContent = "Serveur injoignable.";
  }
}

function afficher(e) {
  const parts = [
    "Mouvement : " + (e.mouvement ? "ON" : "OFF"),
    e.fps + " FPS",
  ];
  if (e.message) parts.push(e.message);
  statut.textContent = parts.join("  |  ");
}

document.addEventListener("keydown", (ev) => {
  if (ev.ctrlKey || ev.metaKey || ev.altKey) return;
  const t = ev.key.toLowerCase();
  if ("dsq".includes(t) && t.length === 1) { ev.preventDefault(); envoyer(t); }
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


# Deuxième serveur (port 5001) : uniquement le flux vidéo, sans page ni commandes.
app_flux = Flask("camera_flux")


@app_flux.route("/")
@app_flux.route("/flux")
def flux_seul():
    return Response(generer_flux(), mimetype="multipart/x-mixed-replace; boundary=image")


@app.after_request
@app_flux.after_request
def autoriser_dashboard(reponse):
    """Autorise le composant HTML du dashboard AliveCode à appeler le serveur."""
    reponse.headers["Access-Control-Allow-Origin"] = "*"
    reponse.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    reponse.headers["Access-Control-Allow-Headers"] = "Content-Type"
    # Chrome : accès d'un site public (alivecode.ca) vers une IP du réseau local
    reponse.headers["Access-Control-Allow-Private-Network"] = "true"
    return reponse


@app.route("/")
def index():
    return PAGE


@app.route("/flux")
def flux():
    return Response(generer_flux(), mimetype="multipart/x-mixed-replace; boundary=image")


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
        if touche == "d":
            etat["mouvement"] = not etat["mouvement"]
        elif touche == "s":
            demande_capture = True
            etat["message"] = "Capture en cours..."
        elif touche == "q":
            etat["message"] = "Arrêt du serveur."
            arret.set()
            # laisse le temps d'envoyer la réponse avant de quitter
            threading.Timer(0.5, lambda: os._exit(0)).start()
        else:
            abort(404)
        return jsonify(etat)


@app.route("/captures/<path:nom>")
def telecharger_capture(nom):
    return send_from_directory(os.path.abspath(DOSSIER_CAPTURES), nom)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diffuse la caméra du Raspberry Pi.")
    parser.add_argument(
        "--https", action="store_true",
        help="sert en HTTPS (certificat auto-signé), requis pour le dashboard AliveCode",
    )
    args = parser.parse_args()

    ssl = "adhoc" if args.https else None
    schema = "https" if args.https else "http"

    threading.Thread(target=boucle_camera, daemon=True).start()

    serveur_flux = make_server(HOTE, PORT_FLUX, app_flux, threaded=True, ssl_context=ssl)
    threading.Thread(target=serveur_flux.serve_forever, daemon=True).start()

    print(f"Page interactive : {schema}://<adresse-ip-du-pi>:{PORT}")
    print(f"Flux seul        : {schema}://<adresse-ip-du-pi>:{PORT_FLUX}")
    app.run(host=HOTE, port=PORT, threaded=True, ssl_context=ssl)