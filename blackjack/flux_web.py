"""
flux_web.py - Diffuse sur le réseau l'image annotée de la caméra MediaPipe.

Port 5000 :
  /                -> page interactive (flux + boutons s = capture, q = quitter)
  /flux            -> flux vidéo seul, pour <img src="https://<ip>:5000/flux"> (AliveCode)
  /certificat.crt  -> certificat à installer sur le poste (plus d'avertissement)

Utilisation (voir detection_action.py) :
  flux_web.demarrer()                 # une fois, avant la boucle
  flux_web.publier(image, action)     # à chaque image
  flux_web.arret.is_set()             # True si on a cliqué sur Quitter

HTTPS (requis par le dashboard AliveCode) : actif si le paquet
`cryptography` est installé, sinon le serveur démarre en HTTP.
  pip install flask cryptography
Le certificat est créé une seule fois dans blackjack/certificat/ puis
réutilisé ; il n'est recréé que si l'adresse IP de la machine change.
"""

import datetime as dt
import ipaddress
import os
import socket
import subprocess
import threading
import time
from datetime import datetime

import cv2
from flask import Flask, Response, abort, jsonify, request, send_file, send_from_directory
from werkzeug.serving import make_server

HOTE = "0.0.0.0"
PORT = 5000
QUALITE_JPEG = 80
DOSSIER_CAPTURES = "captures"
DOSSIER_CERTIFICAT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "certificat")
FICHIER_CERT = os.path.join(DOSSIER_CERTIFICAT, "flux_web.crt")
FICHIER_CLE = os.path.join(DOSSIER_CERTIFICAT, "flux_web.key")

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


@app.route("/certificat.crt")
def telecharger_certificat():
    """Certificat public (sans la clé) à installer sur le poste."""
    if not os.path.exists(FICHIER_CERT):
        abort(404)
    return send_file(FICHIER_CERT, mimetype="application/x-x509-ca-cert",
                     as_attachment=True, download_name="smart_blackjack.crt")


@app.after_request
def autoriser_dashboard(reponse):
    """Autorise le dashboard AliveCode à appeler le serveur."""
    reponse.headers["Access-Control-Allow-Origin"] = "*"
    reponse.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    reponse.headers["Access-Control-Allow-Headers"] = "Content-Type"
    reponse.headers["Access-Control-Allow-Private-Network"] = "true"
    return reponse


# ---- Certificat HTTPS persistant ----
def adresses_ip():
    """Adresses IPv4 de la machine (hors 127.x), ex. ['10.90.20.169']."""
    ips = set()
    try:  # Linux / Raspberry Pi
        sortie = subprocess.run(["hostname", "-I"], capture_output=True, text=True, timeout=2)
        ips.update(ip for ip in sortie.stdout.split() if "." in ip)
    except Exception:
        pass
    try:  # IP utilisée pour sortir sur le réseau (aucun paquet n'est envoyé)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            ips.add(s.getsockname()[0])
    except Exception:
        pass
    return sorted(ip for ip in ips if not ip.startswith("127."))


def ips_du_certificat():
    """IP inscrites dans le certificat existant (vide s'il n'existe pas)."""
    from cryptography import x509
    try:
        with open(FICHIER_CERT, "rb") as f:
            cert = x509.load_pem_x509_certificate(f.read())
        san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
        return {str(ip) for ip in san.get_values_for_type(x509.IPAddress)}
    except Exception:
        return set()


def preparer_certificat():
    """Crée le certificat une seule fois ; le recrée seulement si l'IP a changé."""
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

    ips = adresses_ip()
    if os.path.exists(FICHIER_CLE) and set(ips) <= ips_du_certificat():
        return FICHIER_CERT, FICHIER_CLE

    print(f"Création du certificat HTTPS pour {', '.join(ips) or 'localhost'} "
          "(à réinstaller sur le poste : /certificat.crt)")
    os.makedirs(DOSSIER_CERTIFICAT, exist_ok=True)
    cle = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    nom = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Smart Blackjack")])
    hote = socket.gethostname()
    noms = [x509.DNSName("localhost"), x509.DNSName(hote), x509.DNSName(hote + ".local"),
            x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]
    noms += [x509.IPAddress(ipaddress.ip_address(ip)) for ip in ips]
    maintenant = dt.datetime.now(dt.timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(nom).issuer_name(nom)
        .public_key(cle.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(maintenant - dt.timedelta(days=1))
        .not_valid_after(maintenant + dt.timedelta(days=825))
        .add_extension(x509.SubjectAlternativeName(noms), critical=False)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), critical=False)
        .sign(cle, hashes.SHA256())
    )
    with open(FICHIER_CLE, "wb") as f:
        f.write(cle.private_bytes(serialization.Encoding.PEM,
                                  serialization.PrivateFormat.TraditionalOpenSSL,
                                  serialization.NoEncryption()))
    with open(FICHIER_CERT, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    return FICHIER_CERT, FICHIER_CLE


def demarrer(https=True):
    """Lance le serveur (port 5000) en arrière-plan (ne bloque pas)."""
    ssl = None
    if https:
        try:
            ssl = preparer_certificat()
        except ImportError:
            print("Paquet 'cryptography' absent : flux web en HTTP "
                  "(bloqué par AliveCode). pip install cryptography")
    schema = "https" if ssl else "http"

    serveur = make_server(HOTE, PORT, app, threaded=True, ssl_context=ssl)
    threading.Thread(target=serveur.serve_forever, daemon=True).start()

    for ip in adresses_ip() or ["<adresse-ip>"]:
        print(f"Page interactive : {schema}://{ip}:{PORT}")
        print(f"Flux seul        : {schema}://{ip}:{PORT}/flux")
